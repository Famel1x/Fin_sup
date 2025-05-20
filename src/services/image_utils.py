import os
import base64

from PIL import Image
from io import BytesIO

from src.client.glhf_client import analyze_single_image
import logging



async def image_to_base64(image_path):
    """Обработка и оптимизация PNG-изображения"""
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Файл {image_path} не найден")
        
        with Image.open(image_path) as img:
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
            
            img.thumbnail((1024, 1024))
            
            buffered = BytesIO()
            img.save(buffered, format="PNG", optimize=True, compress_level=9)
            
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    except Exception as e:
        logging.error(f"Ошибка обработки изображения: {str(e)}")
        return None
    

async def process_image(base64_img):
    """Анализ одного изображения на 7 категорий"""
    result = await analyze_single_image((
                        "Выдели 7 ключевых аспектов для прогноза по изображению.\n"
                        "Формат:\n"
                        "1. Категория: [Название] - [Значение]\n"
                        "...\n"
                        "7. Категория: [Название] - [Значение]"
                    ), base64_img)
    return result