import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
logging.basicConfig(level=logging.INFO)
import uvicorn

# Получаем токен и ID админа
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Создаём бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()
    
# Категории товаров
products_categories = [
    {"name": "Растения", "callback": "plants"},
    {"name": "Грибы", "callback": "mushrooms"},
    {"name": "Артефакты силы", "callback": "artifacts"},
    {"name": "БАДы", "callback": "bads"}
]

# Категории услуг
services_categories = [
    {"name": "Консультация", "callback": "consultation"},
    {"name": "Сопровождение", "callback": "accompaniment"},
    {"name": "Грибные Ретриты", "callback": "retreats"},
    {"name": "Услуги Ситтера или Проводника", "callback": "sitter"}
]

# Товары по категориям
products = {
    "plants": [
        {
            
        "name": "Аконит Джунгарский",
        "price": "500 руб/50мл",
        "desc": "Настойка10% .. Свежий корень под индивидуальный заказ.Онкология, Иммуностимулятор и Корректор, все болевые синдромы.",
        "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/akonit.jpg?text=Аконит"
    },
        {
            
        "name": "Якорцы стелющиеся. Трибулус",
        "price": "200 руб/30г",
        "desc": "Трава для чая. Для мужчин! Повышение уровня гормонов, выносливость, повышение либидо.",
        "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/jakorci.jpg?text=Якорцы стелющиеся"
 }
    ],
    "mushrooms": [
        {
            "name": "Мухомор Пантерный",
            "price": "3500 руб/50г",
            "desc": "Собраны собственноручно со всеми надлежащими ритуалама в Казахстанском Алтае. Оъем ограничен! Только для глубоких заныров или целей внутренней трансформации.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/pantera.jpg?text=Пантерный мухомор"
        }
    ],
    "artifacts": [
        {
            "name": "Камень Силы",
            "price": "3500 руб",
            "desc": "Камень, заряженный энергией природы. Помогает при болезни, медитации, как Талисман.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/stoun.jpg?text=Камень"
        }
    ],
    "bads": [
        {
            "name": "Витамин D3",
            "price": "500 руб",
            "desc": "Поддержка иммунитета и костей.",
            "photo": "https://via.placeholder.com/300x200?text=Витамин"
        }
    ]
}

# Услуги по категориям
services = {
    "consultation": [
        {
            "name": "Консультация по травам, грибам",
            "price": "500 руб/30 мин",
            "desc": "Подбор растений под твои цели: сон, иммунитет, стресс. Онлайн или очно.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/konsult.jpg?text=Консультация"
        }
    ],
    "accompaniment": [
        {
            "name": "Сопровождение в лесу",
            "price": "5000 руб/2 часа",
            "desc": "Проведу тебя в лес, покажу грибы и лекарственные травы и растения, расскажу их свойства научу собирать.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/compani.jpg?text=Сопровождение"
        }
    ],
    "retreats": [
        {
            "name": "Грибной ретрит",
            "price": "50000 руб/3 дня",
            "desc": "3 дня с полным погружением с Проводником в Трип на Пантерном Мухоморе:Випасана или Атмавичара, работа с Психосоматикой в трипе, разблокировка тела и ума медитация, чай из грибов.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/retrit.jpg?text=Ретрит"
        }
    ],
    "sitter": [
        {
            "name": "Услуги Ситтера",
            "price": "8000 руб/8 часов",
            "desc": "Буду сидеть с тобой, если ты в 'Тупняке' — поддержу, привяжу, утешу, свожу в туалет, не дам убиться  тебе.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/sitter.jpg?text=Ситтер"
        }
    ]
}

# Главное меню
@dp.message(Command("start"))
async def start(message: Message):
    photo_url = "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/main_banner.jpg"
    kb = [
        [InlineKeyboardButton(text="🌿 Товары", callback_data="products_menu")],
        [InlineKeyboardButton(text="💬 Услуги", callback_data="services_menu")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")]
    ]
    await message.answer_photo(
        photo=photo_url,
        caption="Добро пожаловать,Ищущий, в нашу витрину!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

# Меню категорий товаров
@dp.callback_query(lambda c: c.data == "products_menu")
async def products_menu(callback: types.CallbackQuery):
    photo_url = "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/banner_products.jpg"
    kb = []
    for cat in products_categories:
        kb.append([InlineKeyboardButton(text=cat["name"], callback_data=f"products_{cat['callback']}")])
    kb.append([InlineKeyboardButton(text="« Назад", callback_data="main")])
    await callback.message.edit_media(
        media=InputMediaPhoto(media=photo_url, caption="Выбери категорию товаров:"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    
# Меню категорий услуг
@dp.callback_query(lambda c: c.data == "services_menu")
async def services_menu(callback: types.CallbackQuery):
    photo_url = "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/banner_services.jpg"
    kb = []
    for cat in services_categories:
        kb.append([InlineKeyboardButton(text=cat["name"], callback_data=f"services_{cat['callback']}")])
    kb.append([InlineKeyboardButton(text="« Назад", callback_data="main")])
    await callback.message.edit_media(
        media=InputMediaPhoto(media=photo_url, caption="Выбери категорию услуг:"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    
# Меню показа товаров по категории
@dp.callback_query(lambda c: c.data.startswith("products_"))
async def show_products_by_category(callback: types.CallbackQuery):
    category = callback.data.split("_") [1]
    if category not in products:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    photo_url = "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/banner_products.jpg"
    kb = []
    for i, p in enumerate(products[category]):
        kb.append([InlineKeyboardButton(text=p["name"], callback_data=f"product_{category}_{i}")])
    kb.append([InlineKeyboardButton(text="« Назад", callback_data="products_menu")])
    await callback.message.edit_media(
        media=InputMediaPhoto(media=photo_url, caption=f"Товары в категории: {next(cat['name'] for cat in products_categories if cat['callback'] == category)}"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

# Показ услуг по категории
@dp.callback_query(lambda c: c.data.startswith("services_"))
async def show_services_by_category(callback: types.CallbackQuery):
    category = callback.data.split("_") [1]
    if category not in services:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    photo_url = "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/IMG_20260312_161546_733.jpg"
    kb = []
    for i, s in enumerate(services[category]):
        kb.append([InlineKeyboardButton(text=s["name"], callback_data=f"service_{category}_{i}")])
    kb.append([InlineKeyboardButton(text="« Назад", callback_data="services_menu")])
    await callback.message.edit_media(
        media=InputMediaPhoto(media=photo_url, caption=f"Услуги в категории: {next(cat['name'] for cat in services_categories if cat['callback'] == category)}"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

# показ конкретного товара 
@dp.callback_query(lambda c: c.data.startswith("product_"))
async def show_product(callback: types.CallbackQuery):
    try:
        parts = callback.data.split("_")
        category = parts [1]
        idx = int(parts [2])
        p = products[category][idx]
        kb = [
            [InlineKeyboardButton(text="✅ Заказать", callback_data=f"order_product_{category}_{idx}")],
            [InlineKeyboardButton(text="« Назад", callback_data=f"products_{category}")]
        ]
        await callback.message.edit_media(
            media=InputMediaPhoto(media=p["photo"], caption=f"<b>{p['name']}</b>\n\n{p['desc']}\n\nЦена: {p['price']}", parse_mode="HTML"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
    except Exception as e:
        logging.error(f"Error in show_product: {e}")
        await callback.answer("Ошибка при загрузке товара", show_alert=True)
    parts = callback.data.split("_")
    category = parts [1]
    idx = int(parts [2])
    p = products[category][idx]
    kb = [
        [InlineKeyboardButton(text="✅ Заказать", callback_data=f"order_product_{category}_{idx}")],
        [InlineKeyboardButton(text="« Назад", callback_data=f"products_{category}")]
    ]
    await callback.message.edit_media(
        media=InputMediaPhoto(media=p["photo"], caption=f"<b>{p['name']}</b>\n\n{p['desc']}\n\nЦена: {p['price']}", parse_mode="HTML"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

# Показ конкретной услуги
@dp.callback_query(lambda c: c.data.startswith("service_"))
async def show_service(callback: types.CallbackQuery):
    try:
        parts = callback.data.split("_")
        category = parts [1]
        idx = int(parts [2])
        s = services[category][idx]
        kb = [
            [InlineKeyboardButton(text="✅ Заказать", callback_data=f"order_service_{category}_{idx}")],
            [InlineKeyboardButton(text="« Назад", callback_data=f"services_{category}")]
        ]
        await callback.message.edit_media(
            media=InputMediaPhoto(media=s["photo"], caption=f"<b>{s['name']}</b>\n\n{s['desc']}\n\nЦена: {s['price']}", parse_mode="HTML"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
          )  
    except Exception as e:
        logging.error(f"Error in show_service: {e}")
        await callback.answer("Ошибка при загрузке услуги", show_alert=True)
    parts = callback.data.split("_")
    category = parts [1]
    idx = int(parts [2])
    s = services[category][idx]
    kb = [
        [InlineKeyboardButton(text="✅ Заказать", callback_data=f"order_service_{category}_{idx}")],
        [InlineKeyboardButton(text="« Назад", callback_data=f"services_{category}")]
    ]
    await callback.message.edit_media(
        media=InputMediaPhoto(media=s["photo"], caption=f"<b>{s['name']}</b>\n\n{s['desc']}\n\nЦена: {s['price']}", parse_mode="HTML"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

# Заказ товара
@dp.callback_query(lambda c: c.data.startswith("order_product_"))
async def order_product(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    category = parts [2]
    idx = int(parts [3])
    p = products[category][idx]
    user = callback.from_user
    order_msg = f"📦 Новый заказ:\n\nТовар: {p['name']}\nЦена: {p['price']}\n\nПользователь: @{user.username or user.id}\nИмя: {user.first_name} {user.last_name or ''}"
    await bot.send_message(ADMIN_ID, order_msg)
    await callback.message.edit_text("✅ Заказ принят! Я свяжусь с вами в ближайшее время.", reply_markup=None)

# Заказ услуги
@dp.callback_query(lambda c: c.data.startswith("order_service_"))
async def order_service(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    category = parts [2]
    idx = int(parts [3])
    s = services[category][idx]
    user = callback.from_user
    order_msg = f"💬 Новая консультация:\n\nУслуга: {s['name']}\nЦена: {s['price']}\n\nПользователь: @{user.username or user.id}\nИмя: {user.first_name} {user.last_name or ''}"
    await bot.send_message(ADMIN_ID, order_msg)
    await callback.message.edit_text("✅ Заказ принят! Я свяжусь с вами в ближайшее время.", reply_markup=None)

# О нас
@dp.callback_query(lambda c: c.data == "about")
async def about(callback: types.CallbackQuery):
    photo_url = "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/about_banner.jpg"
    await callback.message.edit_media(
        media=InputMediaPhoto(media=photo_url, caption="🌿 Мы занимаемся сбором и продажей лекарственных грибов и растений.Консультации и индивидуальное сопровождение. Работа с психосоматикой, кризисами и застарелыми болезнями. \n💬 Проводим консультации по их применению.\n\nСвязаться: @ваш_юзернейм"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« Назад", callback_data="main")]])
    )
    
# Назад в меню
@dp.callback_query(lambda c: c.data == "main")
async def back_to_main(callback: types.CallbackQuery):
    photo_url = "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/main_banner.jpg"
    kb = [
        [InlineKeyboardButton(text="🌿 Товары", callback_data="products_menu")],
        [InlineKeyboardButton(text="💬 Услуги", callback_data="services_menu")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")]
    ]
    await callback.message.edit_media(
        media=InputMediaPhoto(media=photo_url, caption="Добро пожаловать, Ищущий, в нашу витрину!"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

# Создаём FastAPI с lifespan
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    webhook_url = "https://herbal-mushrooms-shop-bot.onrender.com/webhook"
    await bot.set_webhook(url=webhook_url)
    logging.info("Webhook set")
    yield
    await bot.delete_webhook()
    logging.info("Webhook deleted")

app = FastAPI(lifespan=lifespan)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 

# Простой тестовый эндпоинт — чтобы проверить, что сервер жив
@app.get("/")
async def root():
    return {"status": "bot is running"}

# Запуск
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
