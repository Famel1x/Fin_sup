import pandas as pd
import numpy as np
import logging
from prophet import Prophet
from typing import List, Dict
from datetime import datetime
import os
from .gradient_boosting_model import main

logging.basicConfig(
    filename='forecast_pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

EXCLUDED_CATEGORIES = {'перевод', 'вклад', 'сбп', 'карта', 'прочее'}

def is_valid_category(category: str) -> bool:
    return not any(ex in category.lower() for ex in EXCLUDED_CATEGORIES)

def build_time_series(transactions: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    daily_totals = df.groupby('date')['amount'].sum().reset_index()
    daily_totals.columns = ['ds', 'y']
    return daily_totals

def forecast_daily_limit(transactions: List[Dict], days_ahead: int = 1) -> float:
    ts = build_time_series(transactions)
    model = Prophet(daily_seasonality=True)
    model.fit(ts)
    future = model.make_future_dataframe(periods=days_ahead)
    forecast = model.predict(future)
    last_days = forecast.tail(days_ahead)
    return round(last_days['yhat'].mean(), 2)

def forecast_by_boosting(transactions: List[Dict]) -> Dict[str, float]:
    df = pd.DataFrame(transactions)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df[df['category'].apply(is_valid_category)]
    df['date'] = df['timestamp'].dt.date

    # Полный список дат и категорий
    all_dates = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
    all_categories = df['category'].unique()

    df_full = df.groupby(['date', 'category'])['amount'].sum().unstack(fill_value=0)
    df_full = df_full.reindex(index=all_dates, columns=all_categories, fill_value=0)
    df_full.index.name = 'date'
    df_full = df_full.reset_index().melt(id_vars='date', var_name='category', value_name='amount')
    df_full = df_full.sort_values(['date', 'category'])

    try:
        df_full.to_excel("boosting_input_all_categories.xlsx", index=False)
        logging.info("Полный датафрейм (каждый день × каждая категория) сохранён ✅")
    except Exception as e:
        logging.error(f"Ошибка при сохранении входного датафрейма: {str(e)}")

    
    results = main(df_full)

    for category, value in results.items():
        if value:
            print(f"{category}: {value:.2f} руб.")


    return results

def format_for_forecast(parsed_data):
    cleaned = []
    for t in parsed_data:
        if "timestamp" in t and "amount" in t:
            try:
                ts = t["timestamp"] if isinstance(t["timestamp"], datetime) else datetime.strptime(t["timestamp"], "%Y-%m-%d")
                amt = abs(t["amount"])
                category = t.get("category", "прочее")
                cleaned.append({"timestamp": ts, "amount": amt, "category": category})
            except Exception as e:
                print(f"Ошибка в формате строки: {t} — {e}")
    return cleaned
