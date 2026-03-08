from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    user_id: int
    message: str

class ChatResponse(BaseModel):
    reply: str
    error: Optional[str] = None

class ReminderResponse(BaseModel):
    id: int
    chat_id: str
    message: str
    remind_at: str

class BillResponse(BaseModel):
    id: int
    user_id: str
    description: str
    amount: float
    day_of_month: int

class ReminderListResponse(BaseModel):
    reminders: List[ReminderResponse]

class BillListResponse(BaseModel):
    bills: List[BillResponse]
