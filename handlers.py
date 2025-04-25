from aiogram import Router, F
from aiogram.types import Message, PhotoSize
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from src.parsers.image_parser import parse_image
from src.services.forecast import forecast_by_boosting, format_for_forecast
from datetime import datetime, timedelta

router = Router()

# FSM состояния загрузки
class UploadScreens(StatesGroup):
    waiting_for_months = State()
    collecting_screens = State()

user_screen_data = {}

@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("👋 Привет! Отправь мне скрин с категориями расходов — и я покажу, сколько ты потратишь завтра.")

@router.message(Command("upload_session"))
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
        await message.answer(f"📥 Отлично! Теперь загружай скрины за последние {months} месяцев. Когда закончишь — напиши /finish_upload")
        await state.set_state(UploadScreens.collecting_screens)
    except ValueError:
        await message.answer("🚫 Пожалуйста, введи число месяцев (например, 3, 5...) — целым числом")

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
        await message.answer("📸 Скрин добавлен в сессию")
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке скрина: {e}")

@router.message(Command("finish_upload"), UploadScreens.collecting_screens)
async def finish_upload(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in user_screen_data or not user_screen_data[user_id]["data"]:
        await message.answer("🚫 Нет данных для анализа. Сначала загрузите хотя бы один скрин.")
        return

    formatted = format_for_forecast(user_screen_data[user_id]["data"])
    forecast = forecast_by_boosting(formatted)

    if not forecast:
        await message.answer("⚠️ Не удалось построить прогноз. Возможно, данных недостаточно.")
        return

    total = sum(forecast.values())
    text_lines = ["📊 Прогноз на основе загруженных скринов:"]
    for cat, value in forecast.items():
        text_lines.append(f"• {cat}: {value:.2f} ₽")
    text_lines.append(f"\n📈 Общий прогноз: {total:.2f} ₽")

    await message.answer("\n".join(text_lines))
    await state.clear()
    user_screen_data.pop(user_id, None)
