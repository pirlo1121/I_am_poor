from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import json
import traceback

from schemas import (
    ChatRequest, ChatResponse,
    ReminderResponse, BillResponse,
    ReminderListResponse, BillListResponse
)
from database import check_upcoming_bills, get_due_reminders, delete_reminder
from ai.tools import all_tools
from ai.providers import generate_ai_response

# In-memory session proxy
user_sessions = {}

def get_session(user_id: int):
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    return user_sessions[user_id]

def save_session(user_id: int, state: dict):
    user_sessions[user_id] = state

app = FastAPI(
    title="I Am Poor - Financial Assistant API",
    description="Backend API for the Telegram Financial Assistant Bot",
    version="1.0.0"
)

# CORS setup (allow all for internal Docker network)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def process_ai_response(response, user_message: str, user_id: int):
    """Procesa la respuesta usando el proveedor configurado."""
    state = get_session(user_id)
    chat_session = state.get('chat_session')
    
    if os.getenv("AI_PROVIDER", "gemini").lower() == "chatgpt":
        import openai
        
        reply_text = response.choices[0].message.content
        tool_calls = response.choices[0].message.tool_calls
        
        if tool_calls:
            # Prepare openai tools spec
            openai_tools = []
            for func_decl in all_tools.function_declarations:
                # Basic conversion for the tool schema
                from ai.providers import _gemini_schema_to_openai
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": func_decl.name,
                        "description": func_decl.description,
                        "parameters": _gemini_schema_to_openai(func_decl.parameters)
                    }
                })
            
            messages = chat_session if chat_session else [{"role": "system", "content": "You are a financial assistant."}]
            if messages[-1].get("content") != user_message:
                messages.append({"role": "user", "content": user_message})
            messages.append(response.choices[0].message.model_dump())
            
            from ai.tools import execute_function as call_tool
            # Execute all tools
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"[API] 🛠️ Ejecutando herramienta ChatGPT: {function_name}({arguments})")
                tool_result = call_tool(function_name, arguments, user_id)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": str(tool_result)
                })
            
            # Get final response
            final_response = openai.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=messages,
                tools=openai_tools
            )
            reply_text = final_response.choices[0].message.content
            messages.append({"role": "assistant", "content": reply_text})
            state['chat_session'] = messages
        else:
            if not chat_session:
                chat_session = [{"role": "system", "content": "You are a financial assistant."}]
            if not chat_session or chat_session[-1].get("content") != user_message:
                chat_session.append({"role": "user", "content": user_message})
            chat_session.append({"role": "assistant", "content": reply_text})
            state['chat_session'] = chat_session
            
    else: # Gemini
        from google.genai import types
        chat = chat_session
        
        if response.function_calls:
            from ai.tools import execute_function as call_tool
            for tool_call in response.function_calls:
                function_name = tool_call.name
                
                # Extract args
                if isinstance(tool_call.args, dict):
                    args_dict = tool_call.args
                elif hasattr(tool_call.args, "items"):
                    args_dict = {k: v for k, v in tool_call.args.items()}
                else:
                    args_dict = tool_call.args
                
                print(f"[API] 🛠️ Ejecutando herramienta Gemini: {function_name}({args_dict})")
                tool_result = call_tool(function_name, args_dict, user_id)
                
                # Send result back
                tool_response = types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=function_name,
                            response={"result": str(tool_result)}
                        )
                    ]
                )
                
                try:
                    final_response = chat.send_message(tool_response)
                    reply_text = final_response.text
                except Exception as e:
                    print(f"[API] ⚠️ Error en 2da llamada Gemini: {e}")
                    reply_text = "Se ejecutó la acción pero hubo un problema generando la respuesta final."
        else:
            reply_text = response.text
            
        state['chat_session'] = chat
        
    save_session(user_id, state)
    return reply_text

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        user_id = request.user_id
        message = request.message
        
        state = get_session(user_id)
        chat_session = state.get('chat_session')
        
        if not chat_session:
            print(f"[API] 🆕 Iniciando nueva sesión para usuario {user_id}")
            from settings import AI_PROVIDER
            if AI_PROVIDER == "gemini":
                from settings import gemini_client
                from ai.prompts import get_system_instruction
                from google.genai import types
                chat_session = gemini_client.chats.create(
                    model='models/gemini-2.5-flash',
                    config=types.GenerateContentConfig(
                        system_instruction=get_system_instruction(),
                        tools=[all_tools],
                        temperature=0.7
                    )
                )
            else:
                chat_session = []
            
            state['chat_session'] = chat_session
            save_session(user_id, state)
        
        response = generate_ai_response(message, chat_session)
        reply = process_ai_response(response, message, user_id)
        
        return ChatResponse(reply=reply)
        
    except Exception as e:
        print(f"[API] ❌ Error en /api/chat: {e}")
        traceback.print_exc()
        # Reset session on critical error
        save_session(request.user_id, {'chat_session': None})
        return ChatResponse(reply="Lo siento, hubo un error interno. He reiniciado la sesión.", error=str(e))

@app.post("/api/chat/voice", response_model=ChatResponse)
async def chat_voice_endpoint(user_id: int = Form(...), file: UploadFile = File(...)):
    try:
        import openai
        
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
            content = await file.read()
            temp_audio.write(content)
            temp_audio_path = temp_audio.name
            
        try:
            # Transcribe
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            with open(temp_audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="es"
                )
            
            user_text = transcription.text
            print(f"[API] 🎙️ Texto transcrito: '{user_text}'")
            
        finally:
            os.remove(temp_audio_path)
            
        if not user_text.strip():
            return ChatResponse(reply="No pude entender el mensaje de voz. ¿Podrías intentar de nuevo o escribirlo?")
            
        # Process as chat message
        request = ChatRequest(user_id=user_id, message=user_text)
        return await chat_endpoint(request)
        
    except Exception as e:
        print(f"[API] ❌ Error en /api/chat/voice: {e}")
        traceback.print_exc()
        return ChatResponse(reply="Hubo un error procesando tu audio.", error=str(e))

@app.get("/api/reminders/bills/due", response_model=BillListResponse)
def get_due_bills(days_ahead: int = 1):
    try:
        upcoming = check_upcoming_bills(days_ahead=days_ahead)
        return {"bills": upcoming}
    except Exception as e:
        print(f"[API] ❌ Error fetching bills: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reminders/custom/due", response_model=ReminderListResponse)
def get_custom_reminders():
    try:
        due = get_due_reminders()
        # Convert dict to expected model format if necessary
        return {"reminders": due}
    except Exception as e:
        print(f"[API] ❌ Error fetching custom reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/reminders/custom/{reminder_id}")
def delete_custom_reminder(reminder_id: int):
    try:
        delete_reminder(reminder_id)
        return {"status": "ok", "deleted_id": reminder_id}
    except Exception as e:
        print(f"[API] ❌ Error deleting custom reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))
