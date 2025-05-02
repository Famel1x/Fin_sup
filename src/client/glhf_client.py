from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import CommandStart
# import openai
from openai import AsyncOpenAI
import os
import logging


GLHF_TOKEN = os.getenv("GLHF_TOKEN")
client = AsyncOpenAI(
    api_key=GLHF_TOKEN,
    base_url="https://api.glhf.chat/v1"
)

async def ask_model(text):
        try:
            response = await client.chat.completions.create(
                model="hf:meta-llama/Llama-3.1-8B-Instruct",
                messages=[
                    {
                        "role": "system", 
                        "content": ("You are a helpful assistant. Отвечай только на вопросы связанные "
                        "с финансами, финансовой аналитикой и темами связанными с деньгами и тратами пользователя. "
                        "Если у тебя есть сомнение, что вопрос относится к одной из этих тем, то ответь таким текстом: ""Я не могу ответить на этот запрос""")
                    },
                    {"role": "user", "content": text}
                ],
                # temperature=0.7,
                # max_tokens=512
            )
            answer = response.choices[0].message.content
            return answer
        except Exception as err:
            logging.error(f"Error sending message to glhf service {err}")
            return "❌ Произошла ошибка при обращении к AI."
