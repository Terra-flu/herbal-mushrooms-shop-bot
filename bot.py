# ============================================================
# Телеграм-бот "Магазин-витрина" — исправленная и расширенная версия
# ============================================================

import os
import json
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, InlineKeyboardButton, InlineKeyboardMarkup,
    InputMediaPhoto, Update,
)

# ---------------- Логирование ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Переменные окружения ----------------
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_RAW = os.getenv("ADMIN_ID")
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW else None
GROUP_ID_RAW = os.getenv("GROUP_ID")             # id группы для заказов, напр. -1001234567890
GROUP_ID = int(GROUP_ID_RAW) if GROUP_ID_RAW else None
CHANNEL_ID_RAW = os.getenv("CHANNEL_ID")         # id приватного канала для инвайтов
CHANNEL_ID = int(CHANNEL_ID_RAW) if CHANNEL_ID_RAW else None
CHANNEL_STATIC_LINK = os.getenv("CHANNEL_STATIC_LINK")  # запасная статическая ссылка
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # напр. https://<имя-сервиса>.northflank.app — без слэша на конце
PORT = int(os.getenv("PORT", "8000"))     # Northflank сам подставит порт, если он задан в настройках сервиса

if not TOKEN:
    logger.error("❌ BOT_TOKEN не установлен!")
    raise ValueError("BOT_TOKEN не найден")

if not WEBHOOK_HOST:
    logger.error("❌ WEBHOOK_HOST не установлен! Укажи публичный адрес сервиса на Northflank.")
    raise ValueError("WEBHOOK_HOST не найден")

if not ADMIN_ID and not GROUP_ID:
    logger.warning("⚠️ Не заданы ни ADMIN_ID, ни GROUP_ID — заказы некому будет отправлять в Telegram!")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ---------------- Хранилище в памяти ----------------
# ВНИМАНИЕ: при перезапуске бота (в т.ч. из-за "засыпания" на Render) корзины обнуляются.
# Для продакшена лучше вынести cart в Redis или БД — см. комментарий в конце файла.
cart: dict[int, list[dict]] = {}   # user_id -> [{"type","category","idx","quantity"}]


def log_order(order_data: dict):
    with open("orders.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(order_data, ensure_ascii=False) + "\n")


# ---------------- FastAPI + webhook ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 ========== БОТ ЗАПУСКАЕТСЯ ==========")
    webhook_url = f"{WEBHOOK_HOST}/webhook"
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


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@app.head("/")
async def health_check():
    return {"status": "ok", "message": "Бот работает!"}


@app.get("/health")
@app.head("/health")
async def health_check_render():
    return {"status": "ok", "message": "Бот работает!"}


@app.get("/ping")
async def ping():
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


@app.head("/ping")
async def ping_head():
    return {}


@app.post("/webhook")
async def webhook(update: dict):
    try:
        await dp.feed_update(bot, Update(**update))
        return {"ok": True}
    except Exception as e:
        logger.error(f"❌ Ошибка в webhook: {e}")
        return {"ok": False, "error": str(e)}


# ---------------- Каталог ----------------
about_photos = [
    "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/about_banner.jpg",
    "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/about2.jpg",
    "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/about3.jpg",
]
about_caption = (
    "🌿 Мы занимаемся сбором и продажей лекарственных грибов и растений. "
    "Консультации и индивидуальное сопровождение. Работа с психосоматикой, "
    "кризисами и застарелыми болезнями.\n💬 Проводим консультации по их применению.\n\n"
    "Связаться: @petrik_suf"
)

products_categories = [
    {"name": "Растения", "callback": "plants"},
    {"name": "Грибы", "callback": "mushrooms"},
    {"name": "Артефакты силы", "callback": "artifacts"},
    {"name": "БАДы", "callback": "bads"},
]
services_categories = [
    {"name": "Консультация", "callback": "consultation"},
    {"name": "Сопровождение", "callback": "accompaniment"},
    {"name": "Грибные Ретриты", "callback": "retreats"},
    {"name": "Услуги Ситтера или Проводника", "callback": "sitter"},
]

products = {
    "plants": [
        {
            "name": "Аконит Джунгарский",
            "price": "500 руб/50мл",
            "price_numeric": 500,
            "desc": "Настойка 10%. Свежий корень под индивидуальный заказ. Онкология, иммуностимулятор и корректор, все болевые синдромы.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/akonit.jpg",
        },
        {
            "name": "Якорцы стелющиеся. Трибулус",
            "price": "200 руб/30г",
            "price_numeric": 200,
            "desc": "Трава для чая. Для мужчин! Повышение уровня гормонов, выносливость, повышение либидо.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/jakorci.jpg",
        },
    ],
    "mushrooms": [
        {
            "name": "Мухомор Пантерный",
            "price": "3500 руб/50г",
            "price_numeric": 3500,
            "desc": "Собраны собственноручно со всеми надлежащими ритуалами в Казахстанском Алтае. Объём ограничен! Только для глубоких заныров или целей внутренней трансформации.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/pantera.jpg",
        }
    ],
    "artifacts": [
        {
            "name": "Камень Силы",
            "price": "3500 руб",
            "price_numeric": 3500,
            "desc": "Камень, заряженный энергией природы. Помогает при болезни, медитации, как талисман.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/stoun.jpg",
        }
    ],
    "bads": [
        {
            "name": "Цветочная пыльца",
            "price": "500 руб/150г",
            "price_numeric": 500,
            "desc": "Поддержка иммунитета, стимулятор обмена веществ. Собрана с весенне-летнего разнотравья, включая мак, тюльпаны, сафлор. Must have!",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/pilca.jpg",
        }
    ],
}

services = {
    "consultation": [
        {
            "name": "Консультация по травам, грибам",
            "price": "500 руб/30 мин",
            "price_numeric": 500,
            "desc": "Подбор растений под твои цели: сон, иммунитет, стресс. Онлайн или очно.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/konsult.jpg",
        }
    ],
    "accompaniment": [
        {
            "name": "Сопровождение в лесу",
            "price": "5000 руб/2 часа",
            "price_numeric": 5000,
            "desc": "Проведу тебя в лес, покажу грибы и лекарственные травы и растения, расскажу их свойства, научу собирать.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/compani.jpg",
        }
    ],
    "retreats": [
        {
            "name": "Грибной ретрит",
            "price": "50000 руб/3 дня",
            "price_numeric": 50000,
            "desc": "3 дня с полным погружением с проводником в трип на пантерном мухоморе: випассана или атмавичара, работа с психосоматикой в трипе, разблокировка тела и ума, медитация, чай из грибов.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/retrit.jpg",
        }
    ],
    "sitter": [
        {
            "name": "Услуги ситтера",
            "price": "8000 руб/8 часов",
            "price_numeric": 8000,
            "desc": "Буду рядом с тобой в процессе — поддержу, утешу, провожу, не дам себе навредить.",
            "photo": "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/sitter.jpg",
        }
    ],
}


def get_item(item_type: str, category: str, idx: int) -> dict:
    source = products if item_type == "product" else services
    return source[category][idx]


MAIN_BANNER = "https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/main_banner.jpg"


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌿 Товары", callback_data="products_menu")],
        [InlineKeyboardButton(text="💬 Услуги", callback_data="services_menu")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart_inline")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")],
    ])


# ---------------- FSM оформления заказа ----------------
class OrderForm(StatesGroup):
    name = State()
    phone = State()
    comment = State()
    confirm = State()


# ================= Главное меню =================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer_photo(
        photo=MAIN_BANNER,
        caption="Добро пожаловать, Ищущий, в нашу витрину!",
        reply_markup=main_menu_kb(),
    )


@dp.callback_query(F.data == "main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_media(
        media=InputMediaPhoto(media=MAIN_BANNER, caption="Добро пожаловать, Ищущий, в нашу витрину!"),
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


# ================= Категории =================
@dp.callback_query(F.data == "products_menu")
async def products_menu(callback: types.CallbackQuery):
    kb = [[InlineKeyboardButton(text=c["name"], callback_data=f"browse_products_{c['callback']}")]
          for c in products_categories]
    kb.append([InlineKeyboardButton(text="« Назад", callback_data="main")])
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media="https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/banner_products.jpg",
            caption="Выбери категорию товаров:",
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
    )
    await callback.answer()


@dp.callback_query(F.data == "services_menu")
async def services_menu(callback: types.CallbackQuery):
    kb = [[InlineKeyboardButton(text=c["name"], callback_data=f"browse_services_{c['callback']}")]
          for c in services_categories]
    kb.append([InlineKeyboardButton(text="« Назад", callback_data="main")])
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media="https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/banner_services.jpg",
            caption="Выбери категорию услуг:",
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("browse_products_"))
async def show_products_by_category(callback: types.CallbackQuery):
    category = callback.data.removeprefix("browse_products_")
    if category not in products:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    kb = [[InlineKeyboardButton(text=p["name"], callback_data=f"item_product_{category}_{i}")]
          for i, p in enumerate(products[category])]
    kb.append([InlineKeyboardButton(text="« Назад", callback_data="products_menu")])
    cat_name = next(c["name"] for c in products_categories if c["callback"] == category)
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media="https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/banner_products.jpg",
            caption=f"Товары в категории: {cat_name}",
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("browse_services_"))
async def show_services_by_category(callback: types.CallbackQuery):
    category = callback.data.removeprefix("browse_services_")
    if category not in services:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    kb = [[InlineKeyboardButton(text=s["name"], callback_data=f"item_service_{category}_{i}")]
          for i, s in enumerate(services[category])]
    kb.append([InlineKeyboardButton(text="« Назад", callback_data="services_menu")])
    cat_name = next(c["name"] for c in services_categories if c["callback"] == category)
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media="https://raw.githubusercontent.com/Terra-flu/herbal-mushrooms-shop-bot/main/photos/banner_services.jpg",
            caption=f"Услуги в категории: {cat_name}",
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
    )
    await callback.answer()


# ================= Карточка товара/услуги =================
@dp.callback_query(F.data.startswith("item_product_"))
async def show_product(callback: types.CallbackQuery):
    try:
        category, idx_str = callback.data.removeprefix("item_product_").rsplit("_", 1)
        idx = int(idx_str)
        p = products[category][idx]
    except Exception as e:
        logger.error(f"Error in show_product: {e}")
        await callback.answer("Ошибка при загрузке товара", show_alert=True)
        return
    kb = [
        [InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"cartadd_product_{category}_{idx}")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart_inline")],
        [InlineKeyboardButton(text="« Назад", callback_data=f"browse_products_{category}")],
    ]
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=p["photo"],
            caption=f"<b>{p['name']}</b>\n\n{p['desc']}\n\nЦена: {p['price']}",
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("item_service_"))
async def show_service(callback: types.CallbackQuery):
    try:
        category, idx_str = callback.data.removeprefix("item_service_").rsplit("_", 1)
        idx = int(idx_str)
        s = services[category][idx]
    except Exception as e:
        logger.error(f"Error in show_service: {e}")
        await callback.answer("Ошибка при загрузке услуги", show_alert=True)
        return
    kb = [
        [InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"cartadd_service_{category}_{idx}")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart_inline")],
        [InlineKeyboardButton(text="« Назад", callback_data=f"browse_services_{category}")],
    ]
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=s["photo"],
            caption=f"<b>{s['name']}</b>\n\n{s['desc']}\n\nЦена: {s['price']}",
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
    )
    await callback.answer()


# ================= Корзина =================
@dp.callback_query(F.data.startswith("cartadd_"))
async def add_to_cart(callback: types.CallbackQuery):
    try:
        _, item_type, category, idx_str = callback.data.split("_")
        idx = int(idx_str)
        item = get_item(item_type, category, idx)
    except Exception as e:
        logger.error(f"Error in add_to_cart: {e}")
        await callback.answer("Ошибка добавления в корзину", show_alert=True)
        return

    user_cart = cart.setdefault(callback.from_user.id, [])
    existing = next(
        (it for it in user_cart if it["type"] == item_type and it["category"] == category and it["idx"] == idx),
        None,
    )
    if existing:
        existing["quantity"] += 1
        qty = existing["quantity"]
    else:
        user_cart.append({"type": item_type, "category": category, "idx": idx, "quantity": 1})
        qty = 1
    await callback.answer(f"✅ {item['name']} — в корзине: {qty}")


def build_cart_view(user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    items = cart.get(user_id, [])
    if not items:
        return "🛒 Корзина пуста.", InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="« Назад", callback_data="main")]]
        )

    lines = ["🛒 <b>Ваша корзина:</b>\n"]
    kb_rows = []
    total = 0
    for i, entry in enumerate(items):
        item = get_item(entry["type"], entry["category"], entry["idx"])
        subtotal = entry["quantity"] * item["price_numeric"]
        total += subtotal
        lines.append(f"{i + 1}. {item['name']} × {entry['quantity']} — {subtotal} руб")
        kb_rows.append([
            InlineKeyboardButton(text="➖", callback_data=f"cartdec_{i}"),
            InlineKeyboardButton(text=str(entry["quantity"]), callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"cartinc_{i}"),
            InlineKeyboardButton(text="🗑", callback_data=f"cartdel_{i}"),
        ])
    lines.append(f"\n💰 <b>Итого: {total} руб</b>")

    kb_rows.append([InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")])
    kb_rows.append([InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")])
    kb_rows.append([InlineKeyboardButton(text="« Назад", callback_data="main")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=kb_rows)


@dp.message(Command("cart"))
async def show_cart(message: Message):
    text, kb = build_cart_view(message.from_user.id)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@dp.callback_query(F.data == "show_cart_inline")
async def show_cart_inline(callback: types.CallbackQuery):
    text, kb = build_cart_view(callback.from_user.id)
    try:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


async def _refresh_cart_message(callback: types.CallbackQuery):
    text, kb = build_cart_view(callback.from_user.id)
    await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=kb)


@dp.callback_query(F.data.startswith("cartinc_"))
async def cart_inc(callback: types.CallbackQuery):
    i = int(callback.data.removeprefix("cartinc_"))
    user_cart = cart.get(callback.from_user.id, [])
    if 0 <= i < len(user_cart):
        user_cart[i]["quantity"] += 1
    await _refresh_cart_message(callback)
    await callback.answer()


@dp.callback_query(F.data.startswith("cartdec_"))
async def cart_dec(callback: types.CallbackQuery):
    i = int(callback.data.removeprefix("cartdec_"))
    user_cart = cart.get(callback.from_user.id, [])
    if 0 <= i < len(user_cart):
        user_cart[i]["quantity"] -= 1
        if user_cart[i]["quantity"] <= 0:
            user_cart.pop(i)
    await _refresh_cart_message(callback)
    await callback.answer()


@dp.callback_query(F.data.startswith("cartdel_"))
async def cart_del(callback: types.CallbackQuery):
    i = int(callback.data.removeprefix("cartdel_"))
    user_cart = cart.get(callback.from_user.id, [])
    if 0 <= i < len(user_cart):
        user_cart.pop(i)
    await _refresh_cart_message(callback)
    await callback.answer()


@dp.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: types.CallbackQuery):
    cart[callback.from_user.id] = []
    await _refresh_cart_message(callback)
    await callback.answer("Корзина очищена")


@dp.callback_query(F.data == "noop")
async def noop(callback: types.CallbackQuery):
    await callback.answer()


# ================= Оформление заказа (FSM) =================
@dp.callback_query(F.data == "checkout")
async def checkout_start(callback: types.CallbackQuery, state: FSMContext):
    if not cart.get(callback.from_user.id):
        await callback.answer("Корзина пуста.", show_alert=True)
        return
    await state.set_state(OrderForm.name)
    await callback.message.answer("Оформление заказа.\n\nКак вас зовут? (/cancel — отменить)")
    await callback.answer()


@dp.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    current = await state.get_state()
    if current and current.startswith("OrderForm"):
        await state.clear()
        await message.answer("Оформление заказа отменено. Товары остались в корзине.")
    else:
        await message.answer("Сейчас нечего отменять.")


@dp.message(OrderForm.name)
async def order_get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(OrderForm.phone)
    await message.answer("Укажите номер телефона для связи:")


@dp.message(OrderForm.phone)
async def order_get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await state.set_state(OrderForm.comment)
    await message.answer("Комментарий к заказу (адрес, пожелания) — или отправьте «-», если нечего добавить:")


@dp.message(OrderForm.comment)
async def order_get_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text.strip())
    data = await state.get_data()
    cart_text, _ = build_cart_view(message.from_user.id)

    summary = (
        f"{cart_text}\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📝 Комментарий: {data['comment']}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="confirm_order")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")],
    ])
    await state.set_state(OrderForm.confirm)
    await message.answer(f"Проверьте данные заказа:\n\n{summary}", parse_mode="HTML", reply_markup=kb)


@dp.callback_query(F.data == "cancel_order")
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Заказ отменён. Товары остались в корзине.")
    await callback.answer()


@dp.callback_query(F.data == "confirm_order")
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = callback.from_user
    data = await state.get_data()
    items = cart.get(user_id, [])
    if not items:
        await callback.answer("Корзина пуста.", show_alert=True)
        await state.clear()
        return

    lines = []
    total = 0
    order_items_log = []
    for entry in items:
        item = get_item(entry["type"], entry["category"], entry["idx"])
        subtotal = entry["quantity"] * item["price_numeric"]
        total += subtotal
        lines.append(f"• {item['name']} × {entry['quantity']} — {subtotal} руб")
        order_items_log.append({"name": item["name"], "qty": entry["quantity"]})

    order_text = (
        "📦 <b>Новый заказ</b>\n\n" + "\n".join(lines) +
        f"\n\n💰 Итого: {total} руб\n\n"
        f"👤 Имя: {data.get('name')}\n"
        f"📞 Телефон: {data.get('phone')}\n"
        f"📝 Комментарий: {data.get('comment')}\n\n"
        f"Telegram: @{user.username or '—'} (id {user.id})"
    )

    log_order({
        "user_id": user.id,
        "username": user.username,
        "name": data.get("name"),
        "phone": data.get("phone"),
        "comment": data.get("comment"),
        "items": order_items_log,
        "total": total,
        "timestamp": datetime.now().isoformat(),
    })

    # Отправка в группу (и/или копия админу)
    target_chat = GROUP_ID or ADMIN_ID
    if target_chat:
        try:
            await bot.send_message(target_chat, order_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Не удалось отправить заказ в группу/админу: {e}")
    if ADMIN_ID and target_chat != ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, order_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Не удалось отправить копию заказа админу: {e}")

    # Приглашение в приватный канал
    invite_text = "✅ Заказ принят! Мы свяжемся с вами в ближайшее время."
    invite_link = None
    if CHANNEL_ID:
        try:
            link = await bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                member_limit=1,
                name=f"order_{user.id}_{int(datetime.now().timestamp())}",
            )
            invite_link = link.invite_link
        except Exception as e:
            logger.error(f"Не удалось создать инвайт в канал: {e}")
    if not invite_link and CHANNEL_STATIC_LINK:
        invite_link = CHANNEL_STATIC_LINK
    if invite_link:
        invite_text += f"\n\n💬 Присоединяйтесь к закрытому каналу для вопросов и общения:\n{invite_link}"

    cart[user_id] = []
    await state.clear()
    await callback.message.edit_text(invite_text, parse_mode="HTML")
    await callback.answer()


# ================= "О нас" =================
def build_about_kb(idx: int) -> InlineKeyboardMarkup:
    kb = []
    if len(about_photos) > 1:
        kb.append([
            InlineKeyboardButton(text="◀️", callback_data=f"about_slide_{idx - 1}"),
            InlineKeyboardButton(text=f"{idx + 1}/{len(about_photos)}", callback_data="noop"),
            InlineKeyboardButton(text="▶️", callback_data=f"about_slide_{idx + 1}"),
        ])
    kb.append([InlineKeyboardButton(text="« Назад", callback_data="main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


@dp.callback_query(F.data == "about")
async def about(callback: types.CallbackQuery):
    await callback.message.edit_media(
        media=InputMediaPhoto(media=about_photos[0], caption=about_caption),
        reply_markup=build_about_kb(0),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("about_slide_"))
async def about_slide(callback: types.CallbackQuery):
    idx = int(callback.data.removeprefix("about_slide_")) % len(about_photos)
    await callback.message.edit_media(
        media=InputMediaPhoto(media=about_photos[idx], caption=about_caption),
        reply_markup=build_about_kb(idx),
    )
    await callback.answer()


# ================= Служебные команды =================
@dp.message(Command("orders"))
async def send_orders(message: Message):
    if os.path.exists("orders.json"):
        with open("orders.json", "rb") as f:
            await message.answer_document(f)
    else:
        await message.answer("Нет заказов.")


# ================= Запуск =================
if __name__ == "__main__":
    logging.info(f"🟢 Запуск Uvicorn сервера на http://0.0.0.0:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)

# ============================================================
# ЗАМЕТКИ ПО ДЕПЛОЮ НА NORTHFLANK (не код, просто рекомендации):
#
# 1. Переменные окружения, которые нужно задать в Northflank (Secret group /
#    Runtime environment variables сервиса):
#    BOT_TOKEN            — токен бота от @BotFather
#    ADMIN_ID             — твой личный numeric Telegram ID (узнать через @userinfobot)
#    WEBHOOK_HOST          — https://<имя-сервиса>.northflank.app (без / на конце;
#                            Northflank покажет точный адрес после первого деплоя)
#    GROUP_ID             — (необязательно) id группы для заказов
#    CHANNEL_ID           — (необязательно) id приватного канала для инвайтов
#    CHANNEL_STATIC_LINK  — (необязательно) запасная постоянная ссылка-приглашение
#    PORT                  — обычно не нужно трогать, по умолчанию 8000; просто
#                            укажи этот же порт как "Public port" в настройках
#                            сервиса на Northflank (раздел Networking)
#
# 2. Диск контейнера на Northflank (как и почти везде на бесплатных тарифах)
#    НЕ сохраняется между передеплоями/перезапусками. orders.json — это просто
#    быстрый локальный лог для команды /orders, а не надёжное хранилище:
#    не полагайся на него как на единственную копию заказов. Основной и
#    надёжный "журнал" заказов — это сообщения, которые бот шлёт в Telegram
#    (ADMIN_ID/GROUP_ID): переписка в Telegram никуда не пропадёт при рестарте
#    контейнера. Если нужна надёжная история в БД — на Northflank можно
#    подключить Postgres-аддон (есть на бесплатном тарифе) — это отдельная
#    доработка, скажи, если нужна.
#
# 3. Корзины (словарь cart) хранятся в оперативной памяти процесса — при
#    перезапуске контейнера они обнуляются. Для реального магазина стоит
#    вынести в тот же Postgres/Redis.
#
# 4. Бесплатный тариф Northflank, в отличие от Render, не "усыпляет" сервис —
#    часы работы постоянные, так что проблема с UptimeRobot из прошлого
#    вопроса тут не актуальна.
# ============================================================
