from aiogram import Router, F
from aiogram.types import Message, PhotoSize
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from src.parsers.image_parser import parse_image
from src.services.forecast import forecast_by_boosting, format_for_forecast
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import openai
from src.client.glhf_client import ask_model
import logging

from aiogram import Bot


router = Router()

# FSM состояния загрузки
class UploadScreens(StatesGroup):
    waiting_for_months = State()
    collecting_screens = State()

user_screen_data = {}

def get_months_keyboard():
    buttons = [
        [InlineKeyboardButton(text="1 месяца", callback_data="months_1")],
        [InlineKeyboardButton(text="2 месяцев", callback_data="months_2")],
        [InlineKeyboardButton(text="3 месяцев", callback_data="months_3")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await message.answer("👋 Привет! Загрузи скрины трат за месяц по категориям из банковского приложения за 2-5 месяцев — и я покажу прогноз трат")
    # await message.answer("Выбери период:", reply_markup=get_months_keyboard())
    user_screen_data[message.from_user.id] = {
            "data": []
        }
    await state.set_state(UploadScreens.collecting_screens)


# @router.callback_query(UploadScreens.waiting_for_months, F.data.startswith("months_"))
# async def process_chosen_months(callback: CallbackQuery, state: FSMContext):
#     months = int(callback.data.split("_")[1])
    
#     user_screen_data[callback.from_user.id] = {
#         "months": months,
#         "data": []
#     }
#     await callback.message.edit_text(f"📥 Отлично! Загружай скрины за последние {months} месяцев. Когда закончишь — напиши /finish_upload")
#     await state.set_state(UploadScreens.collecting_screens)

# @router.message(F.text == "/upload_session")
# async def start_upload_session(message: Message, state: FSMContext):
#     await message.answer("📅 За сколько месяцев ты хочешь загрузить скрины?")
#     await state.set_state(UploadScreens.waiting_for_months)

# @router.message(UploadScreens.waiting_for_months)
# async def set_months(message: Message, state: FSMContext):
#     try:
#         months = int(message.text)
#         user_screen_data[message.from_user.id] = {
#             "months": months,
#             "data": []
#         }
#         await message.answer(f"📥 Отлично! Загружай скрины за последние {months} месяцев. Когда закончишь — напиши /finish_upload")
#         await state.set_state(UploadScreens.collecting_screens)
#     except ValueError:
#         await message.answer("🚫 Введи число месяцев целым числом (например: 3, 5...)!")

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

        text_lines = ["📊 Прогноз по всем загруженным скринам на день:"]
        for cat, value in valid_forecast.items():
            devided_val = value / 30
            text_lines.append(f"• {cat}: {devided_val:.2f} ₽")
        devided_total = total / 30
        text_lines.append(f"\n📈 Общий прогноз: {devided_total:.2f} ₽")

        text_lines.append(f"\n📈 прогноз на неделю")
        for cat, value in valid_forecast.items():
            devided_val = value / 4
            text_lines.append(f"• {cat}: {devided_val:.2f} ₽")
        devided_total = total / 4
        text_lines.append(f"\n📈 Общий прогноз: {devided_total:.2f} ₽")

        text_lines.append(f"\n📈 прогноз на месяц")
        for cat, value in valid_forecast.items():
            text_lines.append(f"• {cat}: {value:.2f} ₽")
        text_lines.append(f"\n📈 Общий прогноз: {total:.2f} ₽")

        await message.answer("\n".join(text_lines))
    except Exception as e:
        await message.answer(f"❌ Ошибка при построении прогноза: {e}")
    finally:
        await state.clear()
        user_screen_data.pop(user_id, None)


@router.message(F.text == "/get_id")
async def get_chat_id(message: Message):
    chat_id = message.chat.id
    chat_type = message.chat.type
    await message.answer(f"🆔 ID этого чата: `{chat_id}`\nТип чата: {chat_type}")

async def send_to_group(bot: Bot, chat_id: int, text: str):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        print(f"✅ Сообщение отправлено в чат {chat_id}")
    except Exception as e:
        print(f"❌ Не удалось отправить сообщение: {e}")

@router.message(F.text)
async def handle_any_text_without_state(message: Message, bot: Bot):
    chat_type = message.chat.type
    if chat_type == 'group' or chat_type == 'supergroup':
        return 
    user_text = message.text
    await message.answer("🧠 Думаю...")
    answer = await ask_model(user_text)
    await message.answer(answer)

    analytics_report = f"запрос пользователя:\n {user_text}, \nответ модели:\n {answer}"
    await bot.send_message('-4629644007', analytics_report)
