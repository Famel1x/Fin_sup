# src/parsers/pdf_parser.py
import pdfplumber
from typing import List, Dict
from datetime import datetime
import re

def parse_pdf(file_path: str) -> List[Dict]:
    with pdfplumber.open(file_path) as pdf:
        first_page_text = pdf.pages[0].extract_text() or ""
        lower_text = first_page_text.lower()
        if "справка о движении средств" in lower_text:
            print("📄 Найдена строка 'Справка о движении средств' — выбран формат справки")
            return parse_statement_format(file_path)
        elif is_statement_format(lower_text):
            print("📄 Выбран формат справки (по структуре)")
            return parse_statement_format(file_path)
        else:
            print("📄 Выбран классический формат")
            return parse_classic_format(file_path)

def is_statement_format(text: str) -> bool:
    lines = text.lower().splitlines()
    header_keywords = [
        "дата операции", "дата списания",
        "сумма в валюте операции", "сумма операции в валюте карты"
    ]
    matches = 0
    for line in lines[:15]:
        for keyword in header_keywords:
            if keyword in line:
                matches += 1
    return matches >= 2

def parse_classic_format(file_path: str) -> List[Dict]:
    transactions = []
    pattern = re.compile(
        r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+(?P<time>\d{2}:\d{2})\s+\d+\s+(?P<category>.+?)\s+(?P<amount>[+\-]?[\d\s]+,[\d]{2})"
    )

    with pdfplumber.open(file_path) as pdf:
        for page_number, page in enumerate(pdf.pages):
            print(f"--- Страница {page_number + 1} ---")
            text = page.extract_text()
            if not text:
                continue

            for line in text.splitlines():
                match = pattern.search(line)
                if match:
                    try:
                        ts = datetime.strptime(
                            f"{match.group('date')} {match.group('time')}", "%d.%m.%Y %H:%M")
                        
                        amount_text = match.group("amount")
                        has_plus = "+" in amount_text
                        amount_clean = amount_text.replace(" ", "").replace(",", ".").replace("+", "")
                        amount = float(amount_clean)
                        if not has_plus:
                            amount = -amount

                        transactions.append({
                            "timestamp": ts,
                            "category": match.group("category").strip(),
                            "amount": amount
                        })
                        print(f"✅ Парсинг: {ts}, {match.group('category').strip()}, {amount}")

                    except Exception as e:
                        print(f"❌ Ошибка разбора: {line} — {e}")
    return transactions

def parse_statement_format(file_path: str) -> List[Dict]:
    transactions = []
    date_pattern = re.compile(r"^(?P<date>\d{2}\.\d{2}\.\d{4})")
    amount_pattern = re.compile(r"-?\d{1,3}(?: \d{3})*(?:,|\.)\d{2}\s?₽")

    with pdfplumber.open(file_path) as pdf:
        for page_number, page in enumerate(pdf.pages):
            print(f"--- Страница {page_number + 1} ---")
            lines = page.extract_text().splitlines() if page.extract_text() else []

            buffer_date = None
            buffer_lines = []

            for line in lines:
                line = line.strip()
                date_match = date_pattern.match(line)

                if date_match:
                    if buffer_date and buffer_lines:
                        combined_text = " ".join(buffer_lines)
                        amounts = amount_pattern.findall(combined_text)
                        cleaned_text = amount_pattern.sub("", combined_text)
                        cleaned_text = re.sub(r"\b\d{2}\.\d{2}\.\d{4}\b", "", cleaned_text)  # убирает даты
                        cleaned_text = re.sub(r"\b\d{2}\.\d{2}\.\b", "", cleaned_text)  # убирает обрезанные даты
                        cleaned_text = re.sub(r"\s*\d{2}:\d{2}(\s+\d{2}:\d{2})?", "", cleaned_text)  # убирает время
                        cleaned_text = re.sub(r"\s*\d{4,}", "", cleaned_text)  # убирает длинные номера
                        cleaned_text = re.sub(r"\+7\d{10}", "", cleaned_text)  # убирает телефоны
                        cleaned_text = re.sub(r"\s{2,}", " ", cleaned_text)  # нормализует пробелы
                        cleaned_text = cleaned_text.strip()
                        if amounts:
                            try:
                                ts = datetime.strptime(buffer_date, "%d.%m.%Y")
                                raw_amount = amounts[-1]
                                is_negative = "-" in raw_amount
                                amount_text = raw_amount.replace(" ", "").replace("₽", "").replace(",", ".").replace("-", "")
                                amount = float(amount_text)
                                if is_negative:
                                    amount = -amount

                                print(amount)
                                category = combined_text
                                transactions.append({
                                    "timestamp": ts,
                                    "category": cleaned_text,
                                    "amount": amount
                                })
                                print(f"✅ Парсинг (справка): {ts}, {category}, {amount}")
                            except Exception as e:
                                print(f"❌ Ошибка справки: {combined_text} — {e}")
                        else:
                            print(f"⚠️ Пропущена запись без суммы: {buffer_date}, {combined_text}")
                    buffer_date = date_match.group("date")
                    buffer_lines = [line[date_match.end():].strip()]
                elif buffer_date:
                    buffer_lines.append(line.strip())

            if buffer_date and buffer_lines:
                combined_text = " ".join(buffer_lines)
                cleaned_text = amount_pattern.sub("", combined_text)
                cleaned_text = re.sub(r"\b\d{2}\.\d{2}\.\d{4}\b", "", cleaned_text)  # убирает даты
                cleaned_text = re.sub(r"\b\d{2}\.\d{2}\.\b", "", cleaned_text)  # убирает обрезанные даты
                cleaned_text = re.sub(r"\s*\d{2}:\d{2}(\s+\d{2}:\d{2})?", "", cleaned_text)  # убирает время
                cleaned_text = re.sub(r"\s*\d{4,}", "", cleaned_text)  # убирает длинные номера
                cleaned_text = re.sub(r"\+7\d{10}", "", cleaned_text)  # убирает телефоны
                cleaned_text = re.sub(r"\s{2,}", " ", cleaned_text)  # нормализует пробелы
                cleaned_text = cleaned_text.strip()
                amounts = amount_pattern.findall(combined_text)
                if amounts:
                    try:
                        ts = datetime.strptime(buffer_date, "%d.%m.%Y")
                        amount_text = amounts[-1].replace(" ", "").replace("₽", "").replace(",", ".")
                        amount = float(amount_text)
                        category = combined_text
                        transactions.append({
                            "timestamp": ts,
                            "category": cleaned_text,
                            "amount": amount
                        })
                        print(f"✅ Парсинг (справка): {ts}, {category}, {amount}")
                    except Exception as e:
                        print(f"❌ Ошибка справки: {combined_text} — {e}")
                else:
                    print(f"⚠️ Пропущена запись без суммы: {buffer_date}, {combined_text}")

    return transactions
