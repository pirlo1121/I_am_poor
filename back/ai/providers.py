"""
AI Providers wrapper - Unifica Gemini y ChatGPT.
"""

from google.genai import types
from settings import AI_PROVIDER, gemini_client, openai, logger
from .prompts import get_system_instruction
from .tools import all_tools


def generate_ai_response(user_message: str, chat_session=None):
    """
    Genera una respuesta usando el AI provider configurado (Gemini o ChatGPT).
    Retorna un objeto unificado con la respuesta y function calls.
    
    Args:
        user_message: El mensaje del usuario
        chat_session: Para Gemini: sesión de chat. Para ChatGPT: lista de mensajes de historial
    """
    if AI_PROVIDER == "chatgpt":
        # ===== CHATGPT =====
        # Convertir tools al formato de OpenAI
        openai_tools = []
        for func_decl in all_tools.function_declarations:
            tool_def = {
                "type": "function",
                "function": {
                    "name": func_decl.name,
                    "description": func_decl.description,
                    "parameters": _gemini_schema_to_openai(func_decl.parameters)
                }
            }
            openai_tools.append(tool_def)
        
        # Construir mensajes con historial
        # Obtener system instruction con fecha actual
        messages = [{"role": "system", "content": get_system_instruction()}]
        
        # Si hay historial, agregarlo
        if chat_session and isinstance(chat_session, list):
            messages.extend(chat_session)
        
        # Agregar mensaje actual del usuario
        messages.append({"role": "user", "content": user_message})
        
        # Llamar a ChatGPT
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )
        
        return response
    
    else:
        # ===== GEMINI =====
        # Si hay una sesión de chat existente, usar send_message
        if chat_session:
            response = chat_session.send_message(user_message)
        else:
            # Modo stateless (para compatibilidad hacia atrás)
            # Obtener system instruction con fecha actual
            system_prompt = get_system_instruction()
            
            response = gemini_client.models.generate_content(
                model='models/gemini-2.5-flash',
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=[all_tools],
                    temperature=0.7
                )
            )
        
        return response


def _gemini_schema_to_openai(gemini_schema):
    """Convierte el schema de Gemini al formato de OpenAI."""
    if not gemini_schema:
        return {"type": "object", "properties": {}}
    
    openai_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    if hasattr(gemini_schema, 'properties') and gemini_schema.properties:
        for prop_name, prop_schema in gemini_schema.properties.items():
            prop_def = {}
            
            # Mapear tipo
            if prop_schema.type == types.Type.STRING:
                prop_def["type"] = "string"
            elif prop_schema.type == types.Type.NUMBER:
                prop_def["type"] = "number"
            elif prop_schema.type == types.Type.INTEGER:
                prop_def["type"] = "integer"
            elif prop_schema.type == types.Type.BOOLEAN:
                prop_def["type"] = "boolean"
            else:
                prop_def["type"] = "string"
            
            # Añadir descripción
            if hasattr(prop_schema, 'description'):
                prop_def["description"] = prop_schema.description
            
            # Añadir enum si existe
            if hasattr(prop_schema, 'enum') and prop_schema.enum:
                prop_def["enum"] = list(prop_schema.enum)
            
            openai_schema["properties"][prop_name] = prop_def
    
    # Añadir campos requeridos
    if hasattr(gemini_schema, 'required') and gemini_schema.required:
        openai_schema["required"] = list(gemini_schema.required)
    
    return openai_schema
