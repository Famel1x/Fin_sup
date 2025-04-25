from collections import defaultdict
from typing import List, Dict

def summarize_top_categories(transactions: List[Dict], top_n: int = 10) -> List[Dict]:
    print(transactions)
    category_totals = defaultdict(float)
    
    for tx in transactions:
        category = tx.get("category_clean") or tx.get("category") or "Неизвестно"
        amount = tx.get("amount", 0)
        if amount < 0:  # учитываем только расходы
            category_totals[category] += amount

    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1])[:top_n]
    result = [{"category": cat, "total": total} for cat, total in sorted_categories]

    print("\n📊 Топ категорий по расходам:")
    for i, entry in enumerate(result, 1):
        print(f"{i}. {entry['category']}: {entry['total']:.2f} ₽")

    return result

from collections import defaultdict

def summarize_top_expenses(transactions, top_n=10):
    print(transactions)
    totals = defaultdict(float)

    for tx in transactions:
        category = tx.get("category_clean") or tx.get("category", "Прочее")
        amount = tx.get("amount", 0)
        if amount < 0:  # только расходы
            totals[category] += amount

    top = sorted(totals.items(), key=lambda x: x[1])[:top_n]

    print("\n📊 Топ категорий по расходам:")
    for i, (cat, amt) in enumerate(top, 1):
        print(f"{i}. {cat}: {amt:.2f} ₽")

    return top



