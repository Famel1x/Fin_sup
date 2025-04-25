from src.parsers.pdf_parser import parse_pdf
from src.services.forecast import forecast_daily_limit
from datetime import datetime
from src.utils import summarize_top_categories, summarize_top_expenses

def format_for_forecast(parsed_data):
    cleaned = []
    for t in parsed_data:
        if "timestamp" in t and "amount" in t:
            try:
                ts = t["timestamp"] if isinstance(t["timestamp"], datetime) else datetime.strptime(t["timestamp"], "%Y-%m-%d")
                amt = abs(t["amount"])
                cleaned.append({"timestamp": ts, "amount": amt})
            except Exception as e:
                print(f"Ошибка в формате строки: {t} — {e}")
    return cleaned

def test_pdf_forecast(path):
    parsed = parse_pdf(path)

    print("=== PARSED PDF DATA ===")
    print(f"✅ Найдено транзакций: {len(parsed)}")
    for row in parsed[:5]:
        print(row)

    formatted = format_for_forecast(parsed)
    print(f"✅ Готово к прогнозу: {len(formatted)} записей")

    if not formatted:
        print("⚠️ Нет валидных транзакций для прогноза.")
        return

    daily_limit = forecast_daily_limit(formatted)
    print(f"Рекомендуемый дневной лимит: {daily_limit} ₽")

# if __name__ == "__main__":
#     test_pdf_forecast("tests/Выписка_по_счёту_дебетовой_карты.pdf")
#     test_pdf_forecast("tests/Справка_о_движении_денежных_средств.pdf")
transactions  = parse_pdf("tests/Выписка_по_счёту_дебетовой_карты.pdf")
top_expenses = summarize_top_categories(transactions, top_n=10)
print(top_expenses)
summarize_top_expenses(transactions)
transactions  = parse_pdf("tests/Справка_о_движении_денежных_средств.pdf")
top_expenses = summarize_top_categories(transactions, top_n=10)
print(top_expenses)
summarize_top_expenses(transactions)

# print(parse_pdf("tests/Справка_о_движении_денежных_средств.pdf"))