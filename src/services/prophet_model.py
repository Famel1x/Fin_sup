import pandas as pd
import numpy as np
import logging
from prophet import Prophet
from datetime import datetime

logging.basicConfig(
    filename='prophet.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def prepare_data(df, category):
    """Подготовка данных для конкретной категории"""
    try:
        filtered = df[df['category'] == category][['date', 'amount']]
        filtered.columns = ['ds', 'y']
        return filtered.dropna()
    except Exception as e:
        logging.error(f"Ошибка подготовки данных для {category}: {str(e)}")
        raise

def process_category(df, category):
    """Полный цикл обработки для одной категории"""
    try:
        logging.info(f"Старт обработки категории: {category}")
        
        # Подготовка данных
        data = prepare_data(df, category)
        
        # Инициализация и обучение модели
        start_time = datetime.now()
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False
        )
        model.fit(data)
        
        # Прогнозирование
        future = model.make_future_dataframe(periods=1, freq='M')
        forecast = model.predict(future)
        
        # Результаты
        result = forecast.tail(1)['yhat'].values[0]
        exec_time = datetime.now() - start_time
        
        logging.info(f"Категория {category} завершена за {exec_time.total_seconds():.1f} сек.")
        return result
        
    except Exception as e:
        logging.error(f"Ошибка в категории {category}: {str(e)}")
        return None

if __name__ == "__main__":
    try:
        # Пример данных
        data = {
            'date': pd.date_range(start='2022-01-01', periods=24, freq='M').repeat(6),
            'category': np.tile([f'category_{i}' for i in range(1,7)], 24),
            'amount': np.random.randint(500, 5000, 144)
        }
        df = pd.DataFrame(data)
        
        # Обработка всех категорий
        results = {}
        for category in df['category'].unique():
            results[category] = process_category(df, category)
        
        # Вывод результатов
        for category, value in results.items():
            if value:
                print(f"{category}: {value:.2f} руб.")
                
    except Exception as e:
        logging.critical(f"Критическая ошибка: {str(e)}")
        raise