from openai import AsyncOpenAI
import os
import base64
import asyncio
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO

GLHF_TOKEN = os.getenv("GLHF_TOKEN")
client = AsyncOpenAI(api_key=GLHF_TOKEN, base_url="https://api.glhf.chat/v1")

def get_next_month_details():
    """Возвращает детали следующего месяца"""
    today = datetime.now()
    next_month_date = today.replace(day=1) + timedelta(days=32)
    last_day_of_month = next_month_date.replace(day=1) - timedelta(days=1)
    return {
        "month_name": next_month_date.strftime("%B %Y"),
        "days_in_month": last_day_of_month.day
    }

async def process_image(image_path):
    """Обработка и оптимизация изображения"""
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Файл {image_path} не найден")
        
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            img.thumbnail((1024, 1024))
            
            buffered = BytesIO()
            img.save(buffered, 
                     format="JPEG",
                     quality=90,
                     optimize=True,
                     progressive=True)
            
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    except Exception as e:
        print(f"Ошибка обработки изображения: {str(e)}")
        return None

async def analyze_single_image(base64_img):
    """Анализ одного изображения на 7 категорий"""
    try:
        response = await client.chat.completions.create(
            model="hf:meta-llama/Llama-3.2-11B-Vision-Instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": (
                        "Выдели 7 ключевых аспектов для прогноза по изображению.\n"
                        "Формат:\n"
                        "1. Категория: [Название] - [Значение]\n"
                        "...\n"
                        "7. Категория: [Название] - [Значение]"
                    )},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                ]
            }],
            temperature=0.6,
            max_tokens=10000
        )
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Ошибка анализа изображения: {str(e)}")
        return None

async def generate_monthly_report(analyses, month_name, days_in_month):
    try:
        response = await client.chat.completions.create(
            model="hf:meta-llama/Llama-3.2-11B-Vision-Instruct",
            messages=[{
                "role": "user",
                "content": [ {
                    "type": "text",
                    "text": (
                            f"На основе анализа {len(analyses)} изображений:\n\n"
                            + "\n\n".join(analyses) +
                            f"\n\nСоставь подробный прогноз ежедневных трат на {month_name} ({days_in_month} дней).\n"
                            "1. Определи 7 характерных категорий трат. Вместо слов «Категория 1» и т.п. сразу используй названия, например: "
                            "«Продукты питания», «Транспорт», «Жильё», «Удобства и развлечения», «Образование и развитие», «Здоровье и красота», «Прочие расходы».\n"
                            "2. Для каждого дня напиши сумму по каждой из этих 7 категорий. Не используй таблицы — представь как понятный структурированный текст в формате:\n\n"
                            "День 1:\n"
                            "Продукты питания: 500₽\n"
                            "Транспорт: 0₽\n"
                            "...\n"
                            "Прочие расходы: 0₽\n\n"
                            "3. Сделай это для всех дней месяца — от 1 до {days_in_month}.\n"
                            "4. В конце напиши итоги по каждой категории за месяц, общую сумму всех расходов и средний дневной расход.\n"
                            "Старайся писать реалистично, как для обычного жителя России со средней активностью."
                            "Пиши обязательно каждый день это невероятно важно"

                    )
                }]
            }],
            temperature=0.7,
            max_tokens=12000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка генерации отчета: {str(e)}")
        return None



async def main(image_paths):
    """Основной поток выполнения"""
    # Получаем данные о месяце
    month_details = get_next_month_details()
    
    # Анализ изображений
    analyses = []
    for path in image_paths[:5]:
        print(f"🔍 Анализ {os.path.basename(path)}...")
        base64_img = await process_image(path)
        if base64_img:
            analysis = await analyze_single_image(base64_img)
            if analysis:
                analyses.append(analysis)
                print(f"✅ Получено {len(analysis.splitlines())} категорий")
    
    if not analyses:
        return "❌ Не удалось проанализировать изображения"
    
    # Генерация отчета
    print("\n🌀 Синтез данных...")
    report = await generate_monthly_report(
        analyses,
        month_details["month_name"],
        month_details["days_in_month"]
    )
    
    if report:
        return f"\n📅 Прогноз на {month_details['month_name']}:\n\n{report}"
    return "❌ Не удалось сгенерировать отчет"

if __name__ == "__main__":
    # Пример использования
    images = [
        'tests/photo_2025-04-23_20-32-50.jpg',
        'tests/photo_2025-04-23_20-33-03.jpg',
        'tests/photo_2025-04-23_20-33-19.jpg',
        'tests/photo_2025-04-23_20-33-39.jpg'
    ]
    
    result = asyncio.run(main(images))
    print(result)