import sqlite3
import threading
import re
import telebot
from telebot import types

# =====================================================
# TOKEN
# =====================================================
import os

token = os.getenv("BOT_TOKEN")

if not token:
    raise ValueError("BOT_TOKEN topilmadi")

bot = telebot.TeleBot(
    token,
    parse_mode="HTML",
    threaded=True
)

# =====================================================
# ADMINLAR
# =====================================================

ADMIN_USERNAMES = {
    "Murodjon_129",
    "X_Z_01_18",
    "beek_navroz"
}

ADMIN_USERNAMES_NORMALIZED = {
    x.lower().lstrip("@")
    for x in ADMIN_USERNAMES
}

ADMIN_IDS = set()

# =====================================================
# XOTIRA
# =====================================================

users = {}
admins = {}

memory_lock = threading.Lock()
db_lock = threading.Lock()

# =====================================================
# MANZIL
# =====================================================

ADDRESS = """
📍 <b>BEK BARAKA MARKET</b>

Toshkent viloyati,
Zangiota tumani,
Navqiron Markaz,
Shoh Dom 110

🏪 <i>(Yangi Domlar, Bek Baraka Market)</i>
"""

# =====================================================
# DATABASE
# =====================================================

DB_NAME = "bek_baraka_market.db"


def get_db():
    conn = sqlite3.connect(
        DB_NAME,
        timeout=30
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_database():

    conn = get_db()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price TEXT NOT NULL,
                active INTEGER DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                telegram_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                phone TEXT,
                address TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                phone TEXT,
                address TEXT,
                product TEXT,
                price TEXT,
                status TEXT DEFAULT 'Yangi'
            )
        """)

        conn.commit()

    finally:
        conn.close()


init_database()

# =====================================================
# DATABASE FUNKSIYALAR
# =====================================================


def db_fetchall(query, params=()):

    with db_lock:

        conn = get_db()

        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

        finally:
            conn.close()


def db_fetchone(query, params=()):

    with db_lock:

        conn = get_db()

        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

        finally:
            conn.close()


def db_execute(query, params=()):

    with db_lock:

        conn = get_db()

        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

            return cursor.lastrowid

        finally:
            conn.close()


# =====================================================
# ADMIN TEKSHIRISH
# =====================================================


def is_admin(message):

    username = message.from_user.username or ""

    username = username.lower().lstrip("@")

    if username in ADMIN_USERNAMES_NORMALIZED:

        ADMIN_IDS.add(
            message.from_user.id
        )

        return True

    if message.from_user.id in ADMIN_IDS:
        return True

    return False


# =====================================================
# MENYULAR
# =====================================================


def main_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        "💰 Narxlar",
        "👨‍💼 Admin"
    )

    markup.row(
        "📍 Manzil",
        "🛍 Mahsulotlar"
    )

    markup.row(
        "🛒 Buyurtma berish"
    )

    return markup


def admin_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        "📦 Buyurtmalar",
        "👥 Klientlar"
    )

    markup.row(
        "➕ Mahsulot qo‘shish",
        "✏️ Narx o‘zgartirish"
    )

    markup.row(
        "🗑 Mahsulot o‘chirish",
        "📋 Mahsulotlar"
    )

    markup.row(
        "♻️ Mahsulotni tiklash",
        "👨‍💼 Adminlar"
    )

    return markup


# =====================================================
# START
# =====================================================


@bot.message_handler(commands=["start"])
def start(message):

    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "Mijoz"

    if username.lower().lstrip("@") in ADMIN_USERNAMES_NORMALIZED:

        ADMIN_IDS.add(user_id)

    # Clientni bazaga qo'shish

    db_execute("""
        INSERT OR IGNORE INTO clients
        (telegram_id, name, username)
        VALUES (?, ?, ?)
    """, (
        user_id,
        first_name,
        username
    ))

    db_execute("""
        UPDATE clients
        SET name = ?, username = ?
        WHERE telegram_id = ?
    """, (
        first_name,
        username,
        user_id
    ))

    # ADMIN

    if is_admin(message):

        bot.send_message(
            message.chat.id,

            f"""
👨‍💼 <b>BEK BARAKA MARKET</b>

<b>ADMIN PANEL</b>

Assalomu alaykum, <b>{first_name}</b>!

🆔 ID:
<code>{user_id}</code>

✅ Admin panel tayyor.
""",

            reply_markup=admin_menu()
        )

        return

    # CLIENT

    bot.send_message(
        message.chat.id,

        f"""
🛍 <b>BEK BARAKA MARKET</b>

Assalomu alaykum, <b>{first_name}</b>!

🆔 User ID:
<code>{user_id}</code>

Menyudan foydalaning.

⚠️ <b>OGOHLANTIRISH</b>

🔴 Yetkazib berish xizmati mavjud LEKIN OLGAN MAHSULOTINGIZ 500 000 DAN OSHSAGINA YETKAZIB BERAMIZ
VA YETKAZIB BERISH JOY RAYSENTRGACHA AGAR OSHMASA.

📦 Buyurtmani do‘kondan o‘zingiz olib ketasiz.
""",

        reply_markup=main_menu()
    )


# =====================================================
# MY ID
# =====================================================


@bot.message_handler(commands=["myid"])
def myid(message):

    bot.send_message(
        message.chat.id,

        f"""
🆔 <b>USER ID:</b>
<code>{message.from_user.id}</code>

👤 Username:
@{message.from_user.username or 'yo‘q'}
"""
    )


# =====================================================
# CANCEL
# =====================================================


@bot.message_handler(commands=["cancel"])
def cancel(message):

    user_id = message.from_user.id

    with memory_lock:

        users.pop(user_id, None)
        admins.pop(user_id, None)

    if is_admin(message):

        bot.send_message(
            message.chat.id,
            "❌ Amal bekor qilindi.",
            reply_markup=admin_menu()
        )

    else:

        bot.send_message(
            message.chat.id,
            "❌ Amal bekor qilindi.",
            reply_markup=main_menu()
        )


# =====================================================
# MIJOZ — MAHSULOTLAR
# =====================================================


@bot.message_handler(
    func=lambda m: m.text in [
        "💰 Narxlar",
        "🛍 Mahsulotlar"
    ]
)
def show_products(message):

    products = db_fetchall("""
        SELECT id, name, price
        FROM products
        WHERE active = 1
        ORDER BY id
    """)

    if not products:

        bot.send_message(
            message.chat.id,
            "🛍 Hozirda mahsulotlar mavjud emas."
        )

        return

    text = """
🛍 <b>MAHSULOTLAR VA NARXLAR</b>

"""

    for p in products:

        text += (
            f"🆔 <b>{p['id']}</b> | "
            f"{p['name']} — "
            f"<b>{p['price']} so‘m</b>\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =====================================================
# MANZIL
# =====================================================


@bot.message_handler(
    func=lambda m: m.text == "📍 Manzil"
)
def show_address(message):

    bot.send_message(
        message.chat.id,
        ADDRESS
    )


# =====================================================
# ADMIN INFO
# =====================================================


@bot.message_handler(
    func=lambda m: m.text == "👨‍💼 Admin"
)
def show_admin_info(message):

    bot.send_message(
        message.chat.id,

        """
👨‍💼 <b>ADMIN BILAN BOG‘LANISH</b>

👤 @Murodjon_129
👤 @X_Z_01_18
👤 @beek_navroz
"""
    )


# =====================================================
# BUYURTMA BOSHLASH
# =====================================================


@bot.message_handler(
    func=lambda m: m.text == "🛒 Buyurtma berish"
)
def start_order(message):

    products = db_fetchall("""
        SELECT id, name, price
        FROM products
        WHERE active = 1
        ORDER BY id
    """)

    if not products:

        bot.send_message(
            message.chat.id,
            "❌ Hozirda sotuvda mahsulot yo‘q."
        )

        return

    with memory_lock:

        users[message.from_user.id] = {
            "step": "choose_product"
        }

    markup = types.InlineKeyboardMarkup()

    for p in products:

        markup.add(
            types.InlineKeyboardButton(
                f"{p['name']} — {p['price']} so‘m",
                callback_data=f"buy_{p['id']}"
            )
        )

    bot.send_message(
        message.chat.id,

        "🛒 <b>Mahsulotni tanlang:</b>",

        reply_markup=markup
    )


# =====================================================
# BUYURTMA — MAHSULOT TANLASH
# =====================================================


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("buy_")
)
def process_product_choice(call):

    try:

        product_id = int(
            call.data.split("_")[1]
        )

    except:

        bot.answer_callback_query(
            call.id,
            "❌ Xatolik."
        )

        return

    product = db_fetchone("""
        SELECT id, name, price
        FROM products
        WHERE id = ?
        AND active = 1
    """, (product_id,))

    if not product:

        bot.answer_callback_query(
            call.id,
            "❌ Mahsulot topilmadi."
        )

        return

    user_id = call.from_user.id

    with memory_lock:

        users[user_id] = {
            "step": "get_phone",
            "prod_id": product["id"],
            "prod_name": product["name"],
            "price": product["price"]
        }

    bot.answer_callback_query(
        call.id,
        "✅ Tanlandi."
    )

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )

    markup.add(
        types.KeyboardButton(
            "📞 Telefon raqamni yuborish",
            request_contact=True
        )
    )

    bot.send_message(
        call.message.chat.id,

        f"""
🛍 <b>Tanlangan:</b>
{product['name']}

💰 <b>Narx:</b>
{product['price']} so‘m

📞 Telefon raqamingizni yuboring.
""",

        reply_markup=markup
    )


# =====================================================
# TELEFON TEKSHIRISH
# =====================================================


def valid_phone(phone):

    if not phone:
        return False

    phone = phone.strip()

    pattern = r"^\+?998\d{9}$|^9\d{8}$"

    return bool(
        re.match(pattern, phone)
    )


# =====================================================
# ADMIN — BUYURTMALAR
# =====================================================


@bot.message_handler(
    func=lambda m:
        is_admin(m)
        and m.text == "📦 Buyurtmalar"
)
def admin_orders(message):

    orders = db_fetchall("""
        SELECT
            id,
            user_id,
            name,
            phone,
            product,
            price,
            status
        FROM orders
        ORDER BY id DESC
        LIMIT 20
    """)

    if not orders:

        bot.send_message(
            message.chat.id,
            "📦 Hozircha buyurtmalar yo‘q."
        )

        return

    text = "📦 <b>OXIRGI 20 TA BUYURTMA</b>\n\n"

    for o in orders:

        text += f"""
🆔 <b>#{o['id']}</b>

👤 {o['name']}
🆔 User ID: <code>{o['user_id']}</code>
📞 {o['phone']}

🛍 {o['product']}
💰 {o['price']} so‘m

📌 Status: <b>{o['status']}</b>

━━━━━━━━━━━━━━━━
"""

    bot.send_message(
        message.chat.id,
        text
    )


# =====================================================
# ADMIN — KLIENTLAR
# =====================================================


@bot.message_handler(
    func=lambda m:
        is_admin(m)
        and m.text == "👥 Klientlar"
)
def admin_clients(message):

    clients = db_fetchone("""
        SELECT COUNT(*) AS count
        FROM clients
    """)

    orders = db_fetchone("""
        SELECT COUNT(*) AS count
        FROM orders
    """)

    bot.send_message(
        message.chat.id,

        f"""
👥 <b>KLIENTLAR</b>

👤 Jami klientlar:
<b>{clients['count']}</b> ta

📦 Jami buyurtmalar:
<b>{orders['count']}</b> ta
"""
    )


# =====================================================
# ADMIN — MAHSULOT QO'SHISH
# =====================================================


@bot.message_handler(
    func=lambda m:
        is_admin(m)
        and m.text == "➕ Mahsulot qo‘shish"
)
def admin_add_product(message):

    with memory_lock:

        admins[message.from_user.id] = {
            "step": "add_name"
        }

    bot.send_message(
        message.chat.id,

        """
➕ <b>MAHSULOT QO‘SHISH</b>

Mahsulot nomini yozing.

Masalan:
<code>Coca Cola 1.5L</code>

Bekor qilish:
<code>/cancel</code>
"""
    )


# =====================================================
# ADMIN — NARX O'ZGARTIRISH
# =====================================================


@bot.message_handler(
    func=lambda m:
        is_admin(m)
        and m.text == "✏️ Narx o‘zgartirish"
)
def admin_edit_price(message):

    with memory_lock:

        admins[message.from_user.id] = {
            "step": "edit_id"
        }

    bot.send_message(
        message.chat.id,

        """
✏️ <b>NARX O‘ZGARTIRISH</b>

Mahsulot ID sini yozing.

Masalan:
<code>1</code>

Bekor qilish:
<code>/cancel</code>
"""
    )


# =====================================================
# ADMIN — O'CHIRISH
# =====================================================


@bot.message_handler(
    func=lambda m:
        is_admin(m)
        and m.text == "🗑 Mahsulot o‘chirish"
)
def admin_delete_product(message):

    with memory_lock:

        admins[message.from_user.id] = {
            "step": "delete_id"
        }

    bot.send_message(
        message.chat.id,

        """
🗑 <b>MAHSULOT O‘CHIRISH</b>

Mahsulot ID sini yozing.

Masalan:
<code>1</code>

Bekor qilish:
<code>/cancel</code>
"""
    )


# =====================================================
# ADMIN — TIKLASH
# =====================================================


@bot.message_handler(
    func=lambda m:
        is_admin(m)
        and m.text == "♻️ Mahsulotni tiklash"
)
def admin_restore_product(message):

    with memory_lock:

        admins[message.from_user.id] = {
            "step": "restore_id"
        }

    bot.send_message(
        message.chat.id,

        """
♻️ <b>MAHSULOTNI TIKLASH</b>

O‘chirilgan mahsulot ID sini yozing.

Masalan:
<code>1</code>

Bekor qilish:
<code>/cancel</code>
"""
    )


# =====================================================
# ADMIN — MAHSULOTLAR
# =====================================================


@bot.message_handler(
    func=lambda m:
        is_admin(m)
        and m.text == "📋 Mahsulotlar"
)
def admin_products_list(message):

    products = db_fetchall("""
        SELECT id, name, price, active
        FROM products
        ORDER BY id
    """)

    if not products:

        bot.send_message(
            message.chat.id,
            "📋 Bazada mahsulot yo‘q."
        )

        return

    text = "📋 <b>BARCHA MAHSULOTLAR</b>\n\n"

    for p in products:

        status = (
            "🟢 Faol"
            if p["active"] == 1
            else
            "🔴 O‘chirilgan"
        )

        text += f"""
🆔 <b>ID: {p['id']}</b>
🛍 {p['name']}
💰 {p['price']} so‘m
📌 {status}

━━━━━━━━━━━━━━━━
"""

    bot.send_message(
        message.chat.id,
        text
    )


# =====================================================
# ADMINLAR
# =====================================================


@bot.message_handler(
    func=lambda m:
        is_admin(m)
        and m.text == "👨‍💼 Adminlar"
)
def admin_list(message):

    bot.send_message(
        message.chat.id,

        """
👨‍💼 <b>ADMINLAR</b>

👤 @Murodjon_129
👤 @X_Z_01_18
👤 @beek_navroz

📌 Har bir admin botga /start yuborgan bo‘lishi kerak.
"""
    )


# =====================================================
# ADMIN FLOW
# =====================================================


@bot.message_handler(
    content_types=["text", "contact"]
)
def handle_all_messages(message):

    user_id = message.from_user.id

    # =================================================
    # BUYURTMA FLOW
    # =================================================

    with memory_lock:
        user_data = users.get(user_id)

    if user_data:

        # ---------------------------------------------
        # TELEFON
        # ---------------------------------------------

        if user_data["step"] == "get_phone":

            if message.contact:

                phone = message.contact.phone_number

            else:

                phone = message.text.strip()

            if not valid_phone(phone):

                bot.send_message(
                    message.chat.id,

                    """
❌ <b>Telefon raqam noto‘g‘ri.</b>

Masalan:
<code>+998901234567</code>

Yoki 📞 tugmasidan foydalaning.
"""
                )

                return

            with memory_lock:

                users[user_id]["phone"] = phone
                users[user_id]["step"] = "get_name"

            bot.send_message(
                message.chat.id,

                "👤 <b>Ismingizni kiriting:</b>",

                reply_markup=types.ReplyKeyboardRemove()
            )

            return

        # ---------------------------------------------
        # ISM
        # ---------------------------------------------

        if user_data["step"] == "get_name":

            if message.content_type != "text":

                bot.send_message(
                    message.chat.id,
                    "❌ Ismingizni matn ko‘rinishida yozing."
                )

                return

            name = message.text.strip()

            if len(name) < 2:

                bot.send_message(
                    message.chat.id,
                    "❌ Ism juda qisqa."
                )

                return

            with memory_lock:

                users[user_id]["name"] = name
                order_data = users[user_id].copy()

            # Clientni yangilash

            db_execute("""
                UPDATE clients
                SET name = ?, phone = ?
                WHERE telegram_id = ?
            """, (
                name,
                order_data["phone"],
                user_id
            ))

            # Buyurtma

            order_id = db_execute("""
                INSERT INTO orders
                (
                    user_id,
                    name,
                    phone,
                    address,
                    product,
                    price,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                name,
                order_data["phone"],
                "Do‘kondan olib ketish",
                order_data["prod_name"],
                order_data["price"],
                "Yangi"
            ))

            # Adminlarga yuborish

            admin_text = f"""
🆕 <b>YANGI BUYURTMA #{order_id}</b>

👤 Mijoz:
<b>{name}</b>

🆔 User ID:
<code>{user_id}</code>

📞 Telefon:
{order_data['phone']}

🛍 Mahsulot:
<b>{order_data['prod_name']}</b>

💰 Narx:
<b>{order_data['price']} so‘m</b>

📍 Olish:
Do‘kondan olib ketish

📌 Status:
<b>Yangi</b>
"""

            for admin_id in list(ADMIN_IDS):

                try:

                    bot.send_message(
                        admin_id,
                        admin_text
                    )

                except Exception as e:

                    print(
                        "ADMIN MESSAGE ERROR:",
                        admin_id,
                        e
                    )

            # Mijoz

            bot.send_message(
                message.chat.id,

                f"""
✅ <b>BUYURTMANGIZ QABUL QILINDI!</b>

━━━━━━━━━━━━━━━━

📦 Order ID:
<code>#{order_id}</code>

🆔 User ID:
<code>{user_id}</code>

🛍 Mahsulot:
<b>{order_data['prod_name']}</b>

💰 Narx:
<b>{order_data['price']} so‘m</b>

━━━━━━━━━━━━━━━━

👨‍💼 Admin tez orada siz bilan bog‘lanadi.

⚠️ <b>DIQQAT!</b>

🔴 Yetkazib berish xizmati mavjud emas.

📦 Buyurtmangizni do‘kondan o‘zingiz olib ketasiz.
""",

                reply_markup=main_menu()
            )

            with memory_lock:
                users.pop(user_id, None)

            return

    # =================================================
    # ADMIN FLOW
    # =================================================

    if is_admin(message):

        with memory_lock:
            admin_data = admins.get(user_id)

        if admin_data:

            # -----------------------------------------
            # MAHSULOT NOMI
            # -----------------------------------------

            if admin_data["step"] == "add_name":

                name = message.text.strip()

                if len(name) < 2:

                    bot.send_message(
                        message.chat.id,
                        "❌ Mahsulot nomi juda qisqa."
                    )

                    return

                with memory_lock:

                    admins[user_id]["name"] = name
                    admins[user_id]["step"] = "add_price"

                bot.send_message(
                    message.chat.id,

                    """
💰 <b>Narxni kiriting:</b>

Masalan:
<code>15000</code>
"""
                )

                return

            # -----------------------------------------
            # MAHSULOT NARXI
            # -----------------------------------------

            if admin_data["step"] == "add_price":

                price = message.text.strip()

                if not price or not any(
                    c.isdigit()
                    for c in price
                ):

                    bot.send_message(
                        message.chat.id,
                        "❌ Narx noto‘g‘ri."
                    )

                    return

                product_name = admin_data["name"]

                product_id = db_execute("""
                    INSERT INTO products
                    (name, price, active)
                    VALUES (?, ?, 1)
                """, (
                    product_name,
                    price
                ))

                with memory_lock:
                    admins.pop(user_id, None)

                bot.send_message(
                    message.chat.id,

                    f"""
✅ <b>MAHSULOT QO‘SHILDI!</b>

🆔 ID:
<code>{product_id}</code>

🛍 Mahsulot:
<b>{product_name}</b>

💰 Narx:
<b>{price} so‘m</b>
""",

                    reply_markup=admin_menu()
                )

                return

            # -----------------------------------------
            # EDIT ID
            # -----------------------------------------

            if admin_data["step"] == "edit_id":

                try:

                    product_id = int(
                        message.text.strip()
                    )

                except:

                    bot.send_message(
                        message.chat.id,
                        "❌ ID faqat raqam bo‘lishi kerak."
                    )

                    return

                product = db_fetchone("""
                    SELECT id, name, price
                    FROM products
                    WHERE id = ?
                    AND active = 1
                """, (product_id,))

                if not product:

                    bot.send_message(
                        message.chat.id,
                        "❌ Mahsulot topilmadi."
                    )

                    return

                with memory_lock:

                    admins[user_id]["product_id"] = product_id
                    admins[user_id]["step"] = "edit_price"

                bot.send_message(
                    message.chat.id,

                    f"""
✏️ <b>{product['name']}</b>

Hozirgi narx:
{product['price']} so‘m

💰 Yangi narxni kiriting:
"""
                )

                return

            # -----------------------------------------
            # EDIT PRICE
            # -----------------------------------------

            if admin_data["step"] == "edit_price":

                new_price = message.text.strip()

                if not new_price or not any(
                    c.isdigit()
                    for c in new_price
                ):

                    bot.send_message(
                        message.chat.id,
                        "❌ Narx noto‘g‘ri."
                    )

                    return

                product_id = admin_data["product_id"]

                db_execute("""
                    UPDATE products
                    SET price = ?
                    WHERE id = ?
                """, (
                    new_price,
                    product_id
                ))

                with memory_lock:
                    admins.pop(user_id, None)

                bot.send_message(
                    message.chat.id,

                    f"""
✅ <b>NARX O‘ZGARDI!</b>

🆔 ID:
<code>{product_id}</code>

💰 Yangi narx:
<b>{new_price} so‘m</b>
""",

                    reply_markup=admin_menu()
                )

                return

            # -----------------------------------------
            # DELETE ID
            # -----------------------------------------

            if admin_data["step"] == "delete_id":

                try:

                    product_id = int(
                        message.text.strip()
                    )

                except:

                    bot.send_message(
                        message.chat.id,
                        "❌ ID faqat raqam."
                    )

                    return

                product = db_fetchone("""
                    SELECT id, name, price
                    FROM products
                    WHERE id = ?
                    AND active = 1
                """, (product_id,))

                if not product:

                    bot.send_message(
                        message.chat.id,
                        "❌ Faol mahsulot topilmadi."
                    )

                    return

                db_execute("""
                    UPDATE products
                    SET active = 0
                    WHERE id = ?
                """, (
                    product_id,
                ))

                with memory_lock:
                    admins.pop(user_id, None)

                bot.send_message(
                    message.chat.id,

                    f"""
🗑 <b>MAHSULOT O‘CHIRILDI!</b>

🆔 ID:
<code>{product_id}</code>

🛍 {product['name']}

💰 {product['price']} so‘m

📌 Klientlarga ko‘rinmaydi.
""",

                    reply_markup=admin_menu()
                )

                return

            # -----------------------------------------
            # RESTORE ID
            # -----------------------------------------

            if admin_data["step"] == "restore_id":

                try:

                    product_id = int(
                        message.text.strip()
                    )

                except:

                    bot.send_message(
                        message.chat.id,
                        "❌ ID faqat raqam."
                    )

                    return

                product = db_fetchone("""
                    SELECT id, name, price
                    FROM products
                    WHERE id = ?
                    AND active = 0
                """, (product_id,))

                if not product:

                    bot.send_message(
                        message.chat.id,
                        "❌ O‘chirilgan mahsulot topilmadi."
                    )

                    return

                db_execute("""
                    UPDATE products
                    SET active = 1
                    WHERE id = ?
                """, (
                    product_id,
                ))

                with memory_lock:
                    admins.pop(user_id, None)

                bot.send_message(
                    message.chat.id,

                    f"""
♻️ <b>MAHSULOT TIKLANDI!</b>

🆔 ID:
<code>{product_id}</code>

🛍 {product['name']}

💰 {product['price']} so‘m

✅ Endi klientlarga ko‘rinadi.
""",

                    reply_markup=admin_menu()
                )

                return


# =====================================================
# UNKNOWN MESSAGE
# =====================================================


@bot.message_handler(
    func=lambda m: True
)
def unknown_message(message):

    if is_admin(message):

        bot.send_message(
            message.chat.id,
            "❓ Menyudagi tugmalardan foydalaning.",
            reply_markup=admin_menu()
        )

    else:

        bot.send_message(
            message.chat.id,
            "❓ Menyudagi tugmalardan foydalaning.",
            reply_markup=main_menu()
        )


# =====================================================
# START BOT
# =====================================================


if __name__ == "__main__":

    print("========================================")
    print("🚀 BEK BARAKA MARKET BOT")
    print("✅ BOT ISHLAYAPTI")
    print("========================================")

    try:

        bot.remove_webhook()

        bot.infinity_polling(
            skip_pending=True,
            timeout=30,
            long_polling_timeout=30
        )

    except Exception as e:

        print("❌ BOT XATOSI:")
        print(e)
