import pandas as pd
import numpy as np
import logging
from pmdarima import auto_arima
from datetime import datetime

# Настройка логгирования
logging.basicConfig(
    filename='sarima.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_data(file_path):
    """Загрузка и подготовка данных"""
    try:
        df = pd.read_csv(file_path, parse_dates=['date'])
        df = df.melt(id_vars='date', var_name='category', value_name='amount')
        return df.set_index('date')
    except Exception as e:
        logging.error(f"Ошибка загрузки данных: {str(e)}")
        raise

def train_and_predict(df):
    """Обучение и прогнозирование для всех категорий"""
    results = {}
    categories = df['category'].unique()
    
    for category in categories:
        logging.info(f"Обработка категории: {category}")
        try:
            # Выделение данных для категории
            series = df[df['category'] == category]['amount']
            
            # Обучение модели
            start_time = datetime.now()
            model = auto_arima(
                series,
                seasonal=True,
                m=12,
                suppress_warnings=True,
                error_action='ignore'
            )
            train_time = datetime.now() - start_time
            
            # Прогноз
            forecast = model.predict(n_periods=1)[0]
            
            # Сохранение результатов
            results[category] = {
                'forecast': forecast,
                'train_time': train_time.total_seconds()
            }
            
            logging.info(f"Категория {category} успешно обработана. Время обучения: {train_time}")

        except Exception as e:
            logging.error(f"Ошибка для категории {category}: {str(e)}")
            results[category] = None
    
    return results

if __name__ == "__main__":
    try:
        # Пример данных
        data = {
            'date': pd.date_range(start='2022-01-01', periods=24, freq='M').repeat(6),
            'category': np.tile([f'category_{i}' for i in range(1,7)], 24),
            'amount': np.random.randint(500, 5000, 144)
        }
        df = pd.DataFrame(data).set_index('date')
        df.to_excel("dasda.xlsx")
        
        # Запуск обработки
        results = train_and_predict(df)
        
        # Вывод результатов
        for category, res in results.items():
            if res:
                print(f"{category}: {res['forecast']:.2f} руб. (обучено за {res['train_time']:.1f} сек.)")
        
    except Exception as e:
        logging.critical(f"Критическая ошибка: {str(e)}")
        raise