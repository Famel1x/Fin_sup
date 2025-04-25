# src/parsers/image_parser.py
import easyocr
from typing import List, Tuple

def parse_image(file_path: str) -> List[Tuple[str, float]]:
    try:
        reader = easyocr.Reader(['ru'], gpu=False)
        results = reader.readtext(file_path, detail=0)

        print("=== RAW OCR TEXT (EasyOCR) ===")
        for line in results:
            print(line)

        categories = []
        parsing = False
        temp_category = None

        for line in results:
            line = line.strip()
            if line.lower().startswith("категории"):
                parsing = True
                continue

            if not parsing:
                continue

            if "операци" in line.lower():
                continue

            if temp_category is None:
                temp_category = line
            elif "₽" in line:
                try:
                    amount_str = line.split("₽")[0].replace(" ", "").replace(",", ".")
                    amount = float(amount_str)
                    categories.append((temp_category, amount))
                except ValueError:
                    pass
                temp_category = None

        return categories
    except Exception as e:
        print(f"Ошибка при парсинге изображения: {e}")
        return []
