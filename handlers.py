from aiogram import Router, F
from aiogram.types import Message, PhotoSize
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from src.parsers.image_parser import parse_image
from src.services.forecast import forecast_by_boosting, format_for_forecast
from datetime import datetime

router = Router()

# FSM состояния загрузки
class UploadScreens(StatesGroup):
    waiting_for_months = State()
    collecting_screens = State()

user_screen_data = {}

@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("👋 Привет! Отправь мне скрин с категориями расходов — и я покажу прогноз трат.")

@router.message(F.text == "/upload_session")
async def start_upload_session(message: Message, state: FSMContext):
    await message.answer("📅 За сколько месяцев ты хочешь загрузить скрины?")
    await state.set_state(UploadScreens.waiting_for_months)

@router.message(UploadScreens.waiting_for_months)
async def set_months(message: Message, state: FSMContext):
    try:
        months = int(message.text)
        user_screen_data[message.from_user.id] = {
            "months": months,
            "data": []
        }
        await message.answer(f"📥 Отлично! Загружай скрины за последние {months} месяцев. Когда закончишь — напиши /finish_upload")
        await state.set_state(UploadScreens.collecting_screens)
    except ValueError:
        await message.answer("🚫 Введи число месяцев целым числом (например: 3, 5...)!")

@router.message(F.photo, UploadScreens.collecting_screens)
async def collect_photo(message: Message, bot, state: FSMContext):
    try:
        photo: PhotoSize = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        downloaded = await bot.download_file(file.file_path)

        with open("temp_image.png", "wb") as f:
            f.write(downloaded.read())

        extracted = parse_image("temp_image.png")
        if not extracted:
            await message.answer("⚠️ Не удалось извлечь данные со скрина. Попробуй другой.")
            return

        now = datetime.now()
        parsed_data = [
            {"timestamp": now, "amount": amt, "category": cat} for cat, amt in extracted
        ]

        user_screen_data[message.from_user.id]["data"].extend(parsed_data)
        await message.answer("📸 Скрин добавлен. Загрузи следующий или отправь /finish_upload для завершения.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке скрина: {e}")

@router.message(F.text == "/finish_upload", UploadScreens.collecting_screens)
async def finish_upload(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = user_screen_data.get(user_id)

    if not user_data or not user_data["data"]:
        await message.answer("🚫 Нет данных для анализа. Пожалуйста, сначала загрузи скрины.")
        return

    try:
        formatted = format_for_forecast(user_data["data"])
        if not formatted:
            await message.answer("⚠️ Не удалось подготовить данные для прогноза. Попробуй загрузить новые скрины.")
            await state.clear()
            user_screen_data.pop(user_id, None)
            return

        forecast = forecast_by_boosting(formatted)

        valid_forecast = {cat: value for cat, value in forecast.items() if value is not None}
        if not valid_forecast:
            await message.answer("⚠️ Недостаточно данных для построения прогноза. Загрузи больше скринов с тратами за разные дни.")
            await state.clear()
            user_screen_data.pop(user_id, None)
            return

        total = sum(valid_forecast.values())

        text_lines = ["📊 Прогноз по всем загруженным скринам:"]
        for cat, value in valid_forecast.items():
            text_lines.append(f"• {cat}: {value:.2f} ₽")
        text_lines.append(f"\n📈 Общий прогноз: {total:.2f} ₽")

        await message.answer("\n".join(text_lines))
    except Exception as e:
        await message.answer(f"❌ Ошибка при построении прогноза: {e}")
    finally:
        await state.clear()
        user_screen_data.pop(user_id, None)
