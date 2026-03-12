import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Получаем токен и ID админа
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Создаём бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Пример товаров
products = [
    {
        "name": "Ромашка аптечная",
        "price": "150 руб/100г",
        "desc": "Сушёная ромашка для чая и настоев. Успокаивает, помогает при бессоннице.",
        "photo": "https://via.placeholder.com/300x200?text=Ромашка"
    },
    {
        "name": "Мелисса лимонная",
        "price": "200 руб/100г",
        "desc": "Ароматная трава для чая. Снимает стресс, улучшает настроение.",
        "photo": "https://via.placeholder.com/300x200?text=Мелисса"
    }
]

# Пример услуг
services = [
    {
        "name": "Консультация по травам",
        "price": "500 руб/30 мин",
        "desc": "Подбор растений под твои цели: сон, иммунитет, стресс. Онлайн или очно.",
        "photo": "https://via.placeholder.com/300x200?text=Консультация"
    }
]

# Главное меню
@dp.message(Command("start"))
async def start(message: Message):
    kb = [
        [InlineKeyboardButton(text="🌿 Товары", callback_data="products")],
        [InlineKeyboardButton(text="💬 Услуги", callback_data="services")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")]
    ]
    await message.answer("Добро пожаловать в нашу витрину!", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# Категории товаров
@dp.callback_query(lambda c: c.data == "products")
async def show_products(callback: types.CallbackQuery):
    kb = []
    for i, p in enumerate(products):
        kb.append([InlineKeyboardButton(text=p["name"], callback_data=f"product_{i}")])
    kb.append([InlineKeyboardButton(text="« Назад", callback_data="main")])
    await callback.message.edit_text("Выбери растение:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# Категории услуг
@dp.callback_query(lambda c: c.data == "services")
async def show_services(callback: types.CallbackQuery):
    kb = []
    for i, s in enumerate(services):
        kb.append([InlineKeyboardButton(text=s["name"], callback_data=f"service_{i}")])
    kb.append([InlineKeyboardButton(text="« Назад", callback_data="main")])
    await callback.message.edit_text("Выбери услугу:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# Показ товара
@dp.callback_query(lambda c: c.data.startswith("product_"))
async def show_product(callback: types.CallbackQuery):
    idx = int(callback.data.split("_") [1])
    p = products[idx]
    kb = [
        [InlineKeyboardButton(text="✅ Заказать", callback_data=f"order_product_{idx}")],
        [InlineKeyboardButton(text="« Назад", callback_data="products")]
    ]
    await callback.message.edit_text(
        f"<b>{p['name']}</b>\n\n{p['desc']}\n\nЦена: {p['price']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# Показ услуги
@dp.callback_query(lambda c: c.data.startswith("service_"))
async def show_service(callback: types.CallbackQuery):
    idx = int(callback.data.split("_") [1])
    s = services[idx]
    kb = [
        [InlineKeyboardButton(text="✅ Заказать", callback_data=f"order_service_{idx}")],
        [InlineKeyboardButton(text="« Назад", callback_data="services")]
    ]
    await callback.message.edit_text(
        f"<b>{s['name']}</b>\n\n{s['desc']}\n\nЦена: {s['price']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# Заказ товара
@dp.callback_query(lambda c: c.data.startswith("order_product_"))
async def order_product(callback: types.CallbackQuery):
    idx = int(callback.data.split("_") [2])
    p = products[idx]
    user = callback.from_user
    order_msg = f"📦 Новый заказ:\n\nТовар: {p['name']}\nЦена: {p['price']}\n\nПользователь: @{user.username or user.id}\nИмя: {user.first_name} {user.last_name or ''}"
    await bot.send_message(ADMIN_ID, order_msg)
    await callback.message.edit_text("✅ Заказ принят! Я свяжусь с вами в ближайшее время.", reply_markup=None)

# Заказ услуги
@dp.callback_query(lambda c: c.data.startswith("order_service_"))
async def order_service(callback: types.CallbackQuery):
    idx = int(callback.data.split("_") [2])
    s = services[idx]
    user = callback.from_user
    order_msg = f"💬 Новая консультация:\n\nУслуга: {s['name']}\nЦена: {s['price']}\n\nПользователь: @{user.username or user.id}\nИмя: {user.first_name} {user.last_name or ''}"
    await bot.send_message(ADMIN_ID, order_msg)
    await callback.message.edit_text("✅ Заказ принят! Я свяжусь с вами в ближайшее время.", reply_markup=None)

# О нас
@dp.callback_query(lambda c: c.data == "about")
async def about(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🌿 Мы занимаемся сбором и продажей лекарственных растений.\n💬 Проводим консультации по их применению.\n\nСвязаться: @ваш_юзернейм",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« Назад", callback_data="main")]])
    )

# Назад в меню
@dp.callback_query(lambda c: c.data == "main")
async def back_to_main(callback: types.CallbackQuery):
    await start(callback.message)

# Создаём FastAPI
app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Запуск бота
async def start_bot():
    await dp.start_polling(bot)

# Запуск FastAPI
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_bot())

# Проверка — что Render видит порт
@app.get("/")
async def root():
    return {"status": "bot is running"}

# Запуск
