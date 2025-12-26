from fastapi import APIRouter, Depends,HTTPException
from pydantic import BaseModel
from typing import List
from app.users import current_active_user
from app.schemas import  ChatMessage


from openai import AsyncOpenAI
import os
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)





class ChatRequest(BaseModel):
    messages: List[ChatMessage]


@router.post("/chat")
async def chat_with_ai(request: ChatRequest, user=Depends(current_active_user)):
    if not request.messages[-1].content:
        raise HTTPException(status_code=400, detail="Empty")

    try:

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": request.messages[-1].content}]
        )

        ai_reply = response.choices[0].message.content
        return {"reply": ai_reply}

    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=400, detail=str(e))
