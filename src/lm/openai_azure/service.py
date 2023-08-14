from fastapi import FastAPI
from pydantic import BaseModel

from lm import chat


class ChatHistory(BaseModel):
    system: str
    messages: list


app = FastAPI()


@app.post("/chat")
async def root(chat_history: ChatHistory):
    inputs = chat_history.model_dump()
    return chat(**inputs)
