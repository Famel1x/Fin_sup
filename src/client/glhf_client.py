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
        
async def analyze_single_image(text: str, base64_img: str):
    """Анализ одного изображения на 7 категорий"""
    try:
        response = await client.chat.completions.create(
            model="hf:meta-llama/Llama-3.2-11B-Vision-Instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                ]
            }],
            temperature=0.6,
            max_tokens=1500,
            timeout=30.0
        )
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Ошибка обработки изображения: {str(e)}")
        logging.error(f"Ошибка обработки изображения: {str(e)}")
        return None

async def generate_monthly_report(analyses, month_name, days_in_month):
    """Генерация финального отчета"""
    try:
        response = await client.chat.completions.create(
            model="hf:meta-llama/Llama-3.2-11B-Vision-Instruct",
            messages=[{
                "role": "user",
                "content": [{
                    "type": "text", 
                    "text": (
                        f"На основе анализа {len(analyses)} изображений:\n\n"
                        + "\n\n".join(analyses) +
                        f"\n\nСоздай прогноз на {month_name}:\n"
                        "1. Детальный прогноз по 7 основным категориям\n"
                        f"2. {days_in_month} ежедневных тартов в формате:\n"
                        "День [X]: [Название] - [Символическое значение]"
                    )
                }]
            }],
            temperature=0.7,
            max_tokens=4000,
            timeout=30.0
        )
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Ошибка генерации отчета: {str(e)}")
        logging.error(f"Error sending message to glhf service {e}")
        return None