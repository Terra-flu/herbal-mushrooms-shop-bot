# 1. Импорты
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import json
from datetime import datetime
import uvicorn

# 2. Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 3. Получаем токен и ID админа
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

if not TOKEN:
    logger.error("❌ BOT_TOKEN не установлен!")
    raise ValueError("BOT_TOKEN не найден")

# ✅ 4. ИНИЦИАЛИЗИРУЕМ БОТ И ДИСПЕТЧЕР ЗДЕСЬ — ПЕРЕД LIFESPAN!
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 5. Глобальные переменные
cart = {}

# 6. Функции
def log_order(order_data: dict):
    with open("orders.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(order_data, ensure_ascii=False) + "\n")

# 7. LIFESPAN — теперь использует уже созданный bot
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 ========== БОТ ЗАПУСКАЕТСЯ ==========")
    webhook_url = "https://herbal-mushrooms-shop-bot.onrender.com/webhook"
    try:
        await bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Ошибка при установке webhook: {e}")
    
    yield
    
    try:
        await bot.delete_webhook()
        logger.info("🛑 Webhook удалён (бот останавливается)")
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении webhook: {e}")
    logger.info("🚀 ========== БОТ ОСТАНОВЛЕН ==========")

# 8. Создаём FastAPI
app = FastAPI(lifespan=lifespan)

# 9. Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 10. Эндпоинты
@app.head("/")
@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Бот работает!"}

# Для опроса рендера
@app.get("/health")
@app.head("/health")
async def health_check_render():
    return {"status": "ok", "message": "Бот работает!"}
    
@app.get("/ping")
async def ping():
    logger.info("📍 Ping получен от UptimeRobot - бот активен")
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

@app.head("/ping")
async def ping_head():
    return {}

# 11. Обработчик webhook
@app.post("/webhook")
async def webhook(update: dict):
    try:
        update_id = update.get("update_id", "unknown")
        if "message" in update:
            msg_text = update["message"].get("text", "")[:50]
            user_id = update["message"].get("from", {}).get("id", "unknown")
            logger.info(f"📨 Update #{update_id} от пользователя {user_id}: {msg_text}")
        elif "callback_query" in update:
            callback_data = update["callback_query"].get("data", "")
            user_id = update["callback_query"].get("from", {}).get("id", "unknown")
            logger.info(f"🔘 Callback #{update_id} от пользователя {user_id}: {callback_data}")
        
        await dp.feed_update(bot, Update(**update))
        return {"ok": True}
    except Exception as e:
        logger.error(f"❌ Ошибка в webhook: {e}")
        return {"ok": False, "error": str(e)}
# О нас
about_photos = [
    "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/about_banner.jpg",
    "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/about2.jpg",
    "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/about3.jpg"
]

about_caption = "🌿 Мы занимаемся сбором и продажей лекарственных грибов и растений. Консультации и индивидуальное сопровождение. Работа с психосоматикой, кризисами и застарелыми болезнями.\n💬 Проводим консультации по их применению.\n\nСвязаться: @petrik_suf"
# Состояние для отслеживания текущего фото
photo_state = {}

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
        "price_numeric": 500,
        "desc": "Настойка10% .. Свежий корень под индивидуальный заказ.Онкология, Иммуностимулятор и Корректор, все болевые синдромы.",
        "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/akonit.jpg?text=Аконит"
    },
        {
            
        "name": "Якорцы стелющиеся. Трибулус",
        "price": "200 руб/30г",
        "price_numeric": 500,
        "desc": "Трава для чая. Для мужчин! Повышение уровня гормонов, выносливость, повышение либидо.",
        "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/jakorci.jpg?text=Якорцы стелющиеся"
 }
    ],
    "mushrooms": [
        {
            "name": "Мухомор Пантерный",
            "price": "3500 руб/50г",
            "price_numeric": 500,
            "desc": "Собраны собственноручно со всеми надлежащими ритуалами в Казахстанском Алтае. Объем ограничен! Только для глубоких заныров или целей внутренней трансформации.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/pantera.jpg"
        }
    ],
    "artifacts": [
        {
            "name": "Камень Силы",
            "price": "3500 руб",
            "price_numeric": 500,
            "desc": "Камень, заряженный энергией природы. Помогает при болезни, медитации, как Талисман.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/stoun.jpg?text=Камень"
        }
    ],
    "bads": [
        {
            "name": "Цветочная пыльца",
            "price": "500 руб/150грамм",
            "price_numeric": 500,
            "desc": "Поддержка иммунитета, стимулятор обмена веществ. Собранная с весенне-летнего разнотравия, включая мак, тюльпаны, сафлор. Must have!",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/pilca.jpg"
        }
    ]
}

# Услуги по категориям
services = {
    "consultation": [
        {
            "name": "Консультация по травам, грибам",
            "price": "500 руб/30 мин",
            "price_numeric": 500,
            "desc": "Подбор растений под твои цели: сон, иммунитет, стресс. Онлайн или очно.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/konsult.jpg?text=Консультация"
        }
    ],
    "accompaniment": [
        {
            "name": "Сопровождение в лесу",
            "price": "5000 руб/2 часа",
            "price_numeric": 500,
            "desc": "Проведу тебя в лес, покажу грибы и лекарственные травы и растения, расскажу их свойства научу собирать.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/compani.jpg?text=Сопровождение"
        }
    ],
    "retreats": [
        {
            "name": "Грибной ретрит",
            "price": "50000 руб/3 дня",
            "price_numeric": 500,
            "desc": "3 дня с полным погружением с Проводником в Трип на Пантерном Мухоморе:Випасана или Атмавичара, работа с Психосоматикой в трипе, разблокировка тела и ума медитация, чай из грибов.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/retrit.jpg"
        }
    ],
    "sitter": [
        {
            "name": "Услуги Ситтера",
            "price": "8000 руб/8 часов",
            "price_numeric": 500,
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
    [InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart_inline")],
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

    photo_url = "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/services.jpg"
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

        # Удаляем старое сообщение и отправляем новое
        await callback.message.delete()
        kb = [
    [InlineKeyboardButton(text="✅ Добавить в корзину", callback_data=f"add_to_cart_product_{category}_{idx}")],
    [InlineKeyboardButton(text="« Назад", callback_data=f"products_{category}")]
        ]
        await callback.message.answer_photo(
            photo=p["photo"],
            caption=f"<b>{p['name']}</b>\n\n{p['desc']}\n\nЦена: {p['price']}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
        await callback.answer()  # Чтобы убрать "загрузка"
    except Exception as e:
        logging.error(f"Error in show_product: {e}")
        await callback.answer("Ошибка при загрузке товара", show_alert=True)
        
        
# Показ конкретной услуги
@dp.callback_query(lambda c: c.data.startswith("service_"))
async def show_service(callback: types.CallbackQuery):
    try:
        parts = callback.data.split("_")
        category = parts [1]
        idx = int(parts [2])
        s = services[category][idx]

        # Удаляем старое сообщение и отправляем новое
        await callback.message.delete()
        kb = [
    [InlineKeyboardButton(text="✅ Добавить в корзину", callback_data=f"add_to_cart_service_{category}_{idx}")],
    [InlineKeyboardButton(text="« Назад", callback_data=f"services_{category}")]
        ]
        await callback.message.answer_photo(
            photo=s["photo"],
            caption=f"<b>{s['name']}</b>\n\n{s['desc']}\n\nЦена: {s['price']}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
        await callback.answer()  # Чтобы убрать "загрузка"
    
    except Exception as e:
        logging.error(f"Error in show_service: {e}")
        await callback.answer("Ошибка при загрузке услуги", show_alert=True)
        
# Заказ товара
@dp.callback_query(lambda c: c.data.startswith("order_product_"))
async def order_product(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    category = parts [2]
    idx = int(parts [3])
    p = products[category][idx]
    user = callback.from_user

    # Логируем заказ
    order_data = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "product": p["name"],
        "price": p["price"],
        "timestamp": datetime.now().isoformat()
    }
    log_order(order_data)

    # Отправляем админу
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

    # Логируем заказ
    order_data = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "service": s["name"],
        "price": s["price"],
        "timestamp": datetime.now().isoformat()
    }
    log_order(order_data)

    # Отправляем админу
    order_msg = f"💬 Новая консультация:\n\nУслуга: {s['name']}\nЦена: {s['price']}\n\nПользователь: @{user.username or user.id}\nИмя: {user.first_name} {user.last_name or ''}"
    await bot.send_message(ADMIN_ID, order_msg)
    await callback.message.edit_text("✅ Заказ принят! Я свяжусь с вами в ближайшее время.", reply_markup=None)

# О нас
def build_about_kb(idx: int) -> InlineKeyboardMarkup:
    """Строит клавиатуру для раздела 'О нас'"""
    kb = []
    
    # Кнопки навигации — только если фото больше одного
    if len(about_photos) > 1:
        kb.append([
            InlineKeyboardButton(text="◀️", callback_data=f"about_slide_{idx - 1}"),
            InlineKeyboardButton(text=f"{idx + 1}/{len(about_photos)}", callback_data="noop"),
            InlineKeyboardButton(text="▶️", callback_data=f"about_slide_{idx + 1}")
        ])
    
    kb.append([InlineKeyboardButton(text="« Назад", callback_data="main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


# Навигация по фото в разделе "О нас"
@dp.callback_query(lambda c: c.data.startswith("about_slide_"))
async def about_slide(callback: types.CallbackQuery):
    idx = int(callback.data.split("_") [2])
    
    # Зацикливаем: если вышли за границы — переходим на другой конец
    idx = idx % len(about_photos)
    
    photo_state["about"] = idx
    kb = build_about_kb(idx)

    await callback.message.edit_media(
        media=InputMediaPhoto(media=about_photos[idx], caption=about_caption),
        reply_markup=kb
    )
    await callback.answer()
@dp.callback_query(lambda c: c.data == "about")
async def about(callback: types.CallbackQuery):
    idx = 0  # Начинаем с первого фото
    photo_state["about"] = idx  # Сохраняем состояние

    kb = build_about_kb(idx)  # Строим клавиатуру

    await callback.message.edit_media(
        media=InputMediaPhoto(media=about_photos[idx], caption=about_caption),
        reply_markup=kb
    )
    await callback.answer()
    
# Назад в меню
@dp.callback_query(lambda c: c.data == "main")
async def back_to_main(callback: types.CallbackQuery):
    photo_url = "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/main_banner.jpg"
    kb = [
    [InlineKeyboardButton(text="🌿 Товары", callback_data="products_menu")],
    [InlineKeyboardButton(text="💬 Услуги", callback_data="services_menu")],
    [InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart_inline")],
    [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")]
]
    await callback.message.edit_media(
        media=InputMediaPhoto(media=photo_url, caption="Добро пожаловать, Ищущий, в нашу витрину!"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
# 🛒 Добавление товара в корзину
@dp.callback_query(lambda c: c.data.startswith("add_to_cart_"))
async def add_to_cart(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    item_type = parts[3]   # "product" или "service"
    category = parts[4]
    idx = int(parts[5])

    if item_type == "product":
        item = products[category][idx]
    else:
        item = services[category][idx]

    user_id = callback.from_user.id

    if user_id not in cart:
        cart[user_id] = []

    # Проверяем, есть ли уже такой товар в корзине
    existing = next((it for it in cart[user_id] if it["type"] == item_type and it["category"] == category and it["idx"] == idx), None)
    if existing:
        existing["quantity"] += 1  # увеличиваем количество
        text = f"✅ +1 к {item['name']} (теперь {existing['quantity']})"
    else:
        cart[user_id].append({
            "type": item_type,
            "category": category,
            "idx": idx,
            "quantity": 1
        })
        text = f"✅ {item['name']} добавлен в корзину!"

    await callback.answer(text)
    await callback.message.delete()
    await callback.bot.send_message(callback.from_user.id, "Товар/услуга добавлен(а) в корзину. Нажмите /cart, чтобы посмотреть.")

    # Инициализируем корзину для пользователя
    if user_id not in cart:
        cart[user_id] = []

    # Добавляем товар/услугу в корзину
    # станет:
    cart[user_id].append({
      "type": item_type,
      "category": category,
      "idx": idx,               # лучше хранить индекс, а не весь item (экономим память)
      "quantity": 1             # ← новое поле! 
        })
    await callback.answer(f"✅ {item['name']} добавлен в корзину!")
    await callback.message.delete()
    await callback.bot.send_message(callback.from_user.id, "Товар/услуга добавлен(а) в корзину. Нажмите /cart, чтобы посмотреть.")

# 🛒 Показ корзины (через команду /cart)
@dp.message(Command("cart"))
async def show_cart(message: Message):
    user_id = message.from_user.id
    if user_id not in cart or len(cart[user_id]) == 0:
        await message.answer("Корзина пуста.")
        return

    cart_items = cart[user_id]
    caption = "🛒 Ваша корзина:\n\п"
    total = 0

for i, entry in enumerate(cart_items):
    if entry["type"] == "product":
        item = products[entry["category"]][entry["idx"]]
    else:
        item = services[entry["category"]][entry["idx"]]
    
    line = f"{i+1}. {item['name']} × {entry['quantity']} — {item['price']}"
    caption += line + "\n"
    
    total += entry["quantity"] * item.get("price_numeric", 0)
    caption += f"\n💰 Итого: {total} руб"

    kb = [
    [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
    [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")]
]
await message.answer(caption, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# 🛒 Показ корзины (через кнопку "🛒 Корзина" в меню)
@dp.callback_query(lambda c: c.data == "show_cart_inline")
async def show_cart_inline(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in cart or len(cart[user_id]) == 0:
        await callback.answer("Корзина пуста.", show_alert=True)
        return

    cart_items = cart[user_id]
    caption = "🛒 Ваша корзина:\n\n"
    total = 0

for i, entry in enumerate(cart_items):
    if entry["type"] == "product":
        item = products[entry["category"]][entry["idx"]]
    else:
        item = services[entry["category"]][entry["idx"]]
    
    line = f"{i+1}. {item['name']} × {entry['quantity']} — {item['price']}"
    caption += line + "\n"
    
    total += entry["quantity"] * item.get("price_numeric", 0)

    caption += f"\n💰 Итого: {total} руб"
    kb = [
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")],
        [InlineKeyboardButton(text="« Назад", callback_data="main")]
]

    await callback.message.edit_caption(caption, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await callback.answer()

# ✅ Оформить заказ
@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in cart or len(cart[user_id]) == 0:
        await callback.answer("Корзина пуста.", show_alert=True)
        return

    order_msg = "📦 Новый заказ из корзины:\n\n"
    for item in cart[user_id]:
        if item["type"] == "product":
            order_msg += f"Товар: {item['item']['name']}\nЦена: {item['item']['price']}\n\n"
        else:
            order_msg += f"Услуга: {item['item']['name']}\nЦена: {item['item']['price']}\n\n"
    order_msg += f"Пользователь: @{callback.from_user.username or callback.from_user.id}\nИмя: {callback.from_user.first_name} {callback.from_user.last_name or ''}"

    # Логируем заказ
    log_order({
        "user_id": callback.from_user.id,
        "username": callback.from_user.username,
        "items": [item['item']['name'] for item in cart[user_id]],
        "timestamp": datetime.now().isoformat()
    })

    await bot.send_message(ADMIN_ID, order_msg)
    await callback.message.edit_text("✅ Заказ принят! Я свяжусь с вами в ближайшее время.")
    cart[user_id] = []

# 🗑️ Очистить корзину
@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in cart:
        cart[user_id] = []
    await callback.message.edit_text("🗑️ Корзина очищена.")

# Отправка списка заказа в телеграм по запросу
@dp.message(Command("orders"))
async def send_orders(message: Message):
    if os.path.exists("orders.json"):
        with open("orders.json", "rb") as f:
            await message.answer_document(f)
    else:
        await message.answer("Нет заказов.")
        
# Запуск
if __name__ == "__main__":
    logging.info("🟢 Запуск Uvicorn сервера на http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
