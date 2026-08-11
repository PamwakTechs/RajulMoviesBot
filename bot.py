from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import asyncio

import os

import threading

import health

from config import BOT_TOKEN, DEFAULT_PART_PRICE

from payment import send_stk_push, reference

from database import (
    fetchone,
    fetchall,
    save_order,
    execute,
)

from admin import (
    admin_panel,
    add_movie_start,
    add_part_start,
    movie_conversation,
    part_conversation,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print("START ARGS:", context.args)

    # Handle deep links
    if context.args:

        arg = context.args[0]

        if arg.startswith("movie_"):

            movie_id = int(arg.split("_")[1])

            context.user_data["movie_id"] = movie_id

            await show_movie_by_id(update, context, movie_id)

            return

        elif arg.startswith("buyall_"):

            movie_id = int(arg.split("_")[1])

            context.user_data["movie_id"] = movie_id

            parts = fetchall(
                "SELECT id FROM parts WHERE movie_id=?",
                (movie_id,),
            )

            total = len(parts) * DEFAULT_PART_PRICE

            context.user_data["amount"] = total
            context.user_data["part_id"] = None

            await update.message.reply_text(
                f"🎬 Buy All Parts\n\n"
                f"💰 Total: KSh {total}\n\n"
                "📱 Send your Safaricom or Airtel number:"
            )

            return

    keyboard = [
        [InlineKeyboardButton("🎬 Browse Movies", callback_data="browse")],
        [InlineKeyboardButton("👛 My Wallet", callback_data="wallet")],
        [InlineKeyboardButton("🛍️ My Orders", callback_data="orders")],
        [InlineKeyboardButton("❓ Help", callback_data="help")],
    ]

    await update.message.reply_text(
        "🎬 Welcome to RAJUL MOVIES\n\n"
        "Choose an option below.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ==========================
# CATEGORY LIST
# ==========================

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    category = query.data.split(":")[1]

    movies = fetchall(
        """
        SELECT id, name
        FROM movies
        WHERE category=?
        ORDER BY id DESC
        """,
        (category,),
    )

    if not movies:
        await query.message.edit_text(
            "❌ No movies found in this category."
        )
        return

    keyboard = []

    for movie in movies:
        keyboard.append(
            [
                InlineKeyboardButton(
                    movie[1],
                    callback_data=f"movie:{movie[0]}"
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data="home"
            )
        ]
    )

    await query.message.edit_text(
        f"🎬 {category}\n\nSelect a movie:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def show_movie_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE, movie_id):

    movie = fetchone(
        """
        SELECT id, name, description, poster_file_id
        FROM movies
        WHERE id=?
        """,
        (movie_id,),
    )

    if not movie:
        await update.message.reply_text("❌ Movie not found.")
        return

    parts = fetchall(
        """
        SELECT id, part_name, price
        FROM parts
        WHERE movie_id=?
        ORDER BY id
        """,
        (movie_id,),
    )

    total_price = sum(part[2] for part in parts)

    keyboard = []

    for part in parts:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🎥 {part[1]} - KSh {part[2]}",
                    callback_data=f"buypart:{part[0]}"
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                f"📦 Buy All Parts - KSh {total_price}",
                callback_data=f"buyall:{movie_id}"
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data="home"
            )
        ]
    )

    await update.message.reply_photo(
        photo=movie[3],
        caption=(
            f"🎬 {movie[1]}\n\n"
            f"{movie[2]}\n\n"
            f"📦 Total Parts: {len(parts)}\n"
            f"💰 Buy All: KSh {total_price}"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ==========================
# HOME BUTTON
# ==========================

async def go_home(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🎬 Browse Movies", callback_data="browse")],
        [InlineKeyboardButton("👛 My Wallet", callback_data="wallet")],
        [InlineKeyboardButton("🛍️ My Orders", callback_data="orders")],
        [InlineKeyboardButton("❓ Help", callback_data="help")],
    ]

    await query.edit_message_text(
        "🎬 Welcome to RAJUL MOVIES\n\nChoose an option below.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ==========================
# MOVIE PAGE
# ==========================

async def show_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    movie_id = int(query.data.split(":")[1])

    movie = fetchone(
        """
        SELECT id, name, description, poster_file_id
        FROM movies
        WHERE id=?
        """,
        (movie_id,),
    )

    if not movie:
        await query.message.reply_text("❌ Movie not found.")
        return

    total_parts = fetchone(
        "SELECT COUNT(*) FROM parts WHERE movie_id=?",
        (movie_id,),
    )[0]

    total_price = total_parts * DEFAULT_PART_PRICE

    keyboard = [
        [
            InlineKeyboardButton(
                "🎥 Buy Parts",
                callback_data=f"parts:{movie_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"📦 Buy All (KSh {total_price})",
                callback_data=f"buyall:{movie_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data=f"cat:{fetchone('SELECT category FROM movies WHERE id=?',(movie_id,))[0]}"
            )
        ]
    ]

    await query.message.reply_photo(
        photo=movie[3],
        caption=(
            f"🎬 {movie[1]}\n\n"
            f"{movie[2]}\n\n"
            f"📦 Parts: {total_parts}\n"
            f"💰 Buy All: KSh {total_price}"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
# ==========================
# SHOW PARTS
# ==========================

async def show_parts(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    movie_id = int(query.data.split(":")[1])

    parts = fetchall(
        """
        SELECT id, part_name, price
        FROM parts
        WHERE movie_id=?
        ORDER BY id
        """,
        (movie_id,),
    )

    if not parts:
        await query.message.reply_text("❌ No parts found.")
        return

    keyboard = []

    for part in parts:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{part[1]} - KSh {part[2]}",
                    callback_data=f"buypart:{part[0]}"
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data=f"movie:{movie_id}"
            )
        ]
    )

    await query.message.reply_text(
        "🎥 Select the part you want to buy:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ==========================
# BUY PART
# ==========================

async def buy_part(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    part_id = int(query.data.split(":")[1])

    part = fetchone(
        """
        SELECT movie_id, part_name, price
        FROM parts
        WHERE id=?
        """,
        (part_id,),
    )

    if not part:
        await query.message.reply_text("❌ Part not found.")
        return

    context.user_data["part_id"] = part_id
    context.user_data["movie_id"] = part[0]
    context.user_data["amount"] = part[2]
    context.user_data["buy_all"] = False

    keyboard = [
        [
            InlineKeyboardButton(
                "👛 Pay with Wallet",
                callback_data=f"walletpay:{part_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Pay with M-PESA",
                callback_data=f"mpesa:{part_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        ]
    ]

    await query.message.reply_text(
        f"🎬 {part[1]}\n"
        f"💰 Price: KSh {part[2]}\n\n"
        "💳 Choose your payment method:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ==========================
# PROCESS WALLET TOP-UP AMOUNT
# ==========================

async def handle_wallet_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("wallet_topup"):
        return

    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text(
            "❌ Please enter a valid amount in KSh."
        )
        return

    amount = int(text)

    if amount < 10:
        await update.message.reply_text(
            "❌ Minimum wallet top-up is KSh 10."
        )
        return

    context.user_data["wallet_amount"] = amount
    context.user_data["wallet_topup_payment"] = True
    context.user_data["wallet_topup"] = False

    await update.message.reply_text(
        f"💰 Wallet top-up: KSh {amount}\n\n"
        "📱 Now send your M-PESA/Airtel phone number:"
    )

# ==========================
# PROCESS PHONE PAYMENT
# ==========================


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):

    phone = update.message.text.strip()

    if not (phone.isdigit() and len(phone) >= 10):
        await update.message.reply_text(
            "❌ Send a valid phone number."
        )
        return

    # ==========================
    # WALLET TOP UP PAYMENT
    # ==========================

    if context.user_data.get("wallet_topup_payment"):

        amount = context.user_data.get("wallet_amount")

        if not amount:
            await update.message.reply_text(
                "❌ Amount missing. Start again."
            )
            return

        ref = reference()

        success, message, data = send_stk_push(
            phone,
            amount,
            ref
        )

        if not success:
            await update.message.reply_text(
                f"❌ Payment failed:\n{message}"
            )
            return

        execute(
            """
            INSERT INTO wallet_topups
            (user_id, amount, reference, status)
            VALUES (?, ?, ?, 'PENDING')
            """,
            (
                update.effective_user.id,
                amount,
                ref
            )
        )

        await update.message.reply_text(
            "📱 Wallet STK Push sent.\n\n"
            "Complete payment on your phone."
        )

        return


    # ==========================
    # MOVIE PAYMENT
    # ==========================

    amount = context.user_data.get("amount")
    part_id = context.user_data.get("part_id")

    if part_id is None:

        row = fetchone(
            """
            SELECT id
            FROM parts
            WHERE movie_id=?
            LIMIT 1
            """,
            (context.user_data.get("movie_id"),),
        )

        if row:
            part_id = row[0]


    if not amount:
        await update.message.reply_text(
            "❌ Session expired. Choose a movie again."
        )
        return


    ref = reference()

    success, message, data = send_stk_push(
        phone,
        amount,
        ref
    )


    if not success:
        await update.message.reply_text(
            f"❌ Payment failed:\n{message}"
        )
        return


    save_order(
        update.effective_user.id,
        context.user_data.get("movie_id"),
        part_id,
        phone,
        amount,
        ref
    )


    await update.message.reply_text(
        "📱 STK Push sent.\n\n"
        "Complete payment on your phone."
    )

# ==========================
# SEND PAID VIDEO
# ==========================

async def deliver_video(user_id, part_id, context):

    part = fetchone(
        """
        SELECT video_file_id, part_name
        FROM parts
        WHERE id=?
        """,
        (part_id,),
    )

    if not part:
        return

    await context.bot.send_video(
        chat_id=user_id,
        video=part[0],
        caption=f"✅ Your purchase:\n🎬 {part[1]}"
    )
async def check_paid_topups(context: ContextTypes.DEFAULT_TYPE):

    topups = fetchall(
        """
        SELECT id, user_id, amount
        FROM wallet_topups
        WHERE status='PAID'
        """
    )

    for topup_id, user_id, amount in topups:

        execute(
            """
            INSERT INTO wallet(user_id, balance)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET balance = balance + ?
            """,
            (
                user_id,
                amount,
                amount
            )
        )

        execute(
            """
            INSERT INTO wallet_transactions
            (user_id, type, amount, description)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                "CREDIT",
                amount,
                "Wallet top up"
            )
        )

        execute(
            """
            UPDATE wallet_topups
            SET status='DONE'
            WHERE id=?
            """,
            (topup_id,)
        )

async def check_paid_orders(context: ContextTypes.DEFAULT_TYPE):

    orders = fetchall(
        """
        SELECT id, telegram_id, part_id
        FROM orders
        WHERE status='PAID'
        """
    )

    for order_id, telegram_id, part_id in orders:

        if part_id:
            await deliver_video(
                telegram_id,
                part_id,
                context
            )

        execute(
            """
            UPDATE orders
            SET status='DELIVERED'
            WHERE id=?
            """,
            (order_id,)
        )

async def wallet_history(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    rows = fetchall(
        "SELECT type, amount, description, created_at "
        "FROM wallet_transactions "
        "WHERE user_id=? "
        "ORDER BY id DESC LIMIT 10",
        (user_id,)
    )

    if not rows:
        text = (
            "📜 Wallet Transactions\n\n"
            "No transactions yet."
        )
    else:
        text = "📜 Wallet Transactions\n\n"

        for row in rows:
            text += (
                f"{row[0]} | KSh {row[1]}\n"
                f"{row[2]}\n"
                f"{row[3]}\n\n"
            )

    keyboard = [
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
        [InlineKeyboardButton("👛 My Wallet", callback_data="wallet")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    balance = fetchone(
        "SELECT balance FROM wallet WHERE user_id=?",
        (user_id,)
    )

    if balance:
        amount = balance[0]
    else:
        amount = 0

    keyboard = [
        [InlineKeyboardButton("➕ Top Up Wallet", callback_data="wallet_topup")],
        [InlineKeyboardButton("📜 Wallet Transactions", callback_data="wallet_history")],
        [InlineKeyboardButton("🏠 Home", callback_data="home")]
    ]

    await query.edit_message_text(
        f"👛 My Wallet\n\n💰 Balance: KSh {amount}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    rows = fetchall(
        """
        SELECT
            movies.name,
            orders.amount,
            orders.status,
            orders.created_at
        FROM orders
        LEFT JOIN movies
            ON movies.id = orders.movie_id
        WHERE orders.telegram_id=?
        ORDER BY orders.id DESC
        """,
        (user_id,)
    )

    if not rows:
        text = "🛍️ My Orders\n\nYou have not purchased any movies yet."
    else:
        text = "🛍️ My Orders\n\n"

        for movie, amount, status, created in rows:
            text += (
                f"🎬 {movie}\n"
                f"💰 KSh {amount}\n"
                f"📌 {status}\n"
                f"📅 {created}\n\n"
            )

    keyboard = [
        [InlineKeyboardButton("🏠 Home", callback_data="home")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================
# CALLBACK ROUTER
# ==========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "admin_add_movie":
        await add_movie_start(update, context)
        return

    if data == "admin_add_part":
        await add_part_start(update, context)
        return

    if data == "admin_movies":
        await query.message.reply_text("📋 Movie list coming...")
        return

    if data == "wallet":
        await wallet_menu(update, context)
        return

    if data == "wallet_history":
        await wallet_history(update, context)
        return

    if data == "wallet_topup":
        await query.message.reply_text(
            "💰 Enter amount to add to your wallet (KSh):"
        )
        context.user_data["wallet_topup"] = True
        return

    if data == "home":
        await go_home(update, context)
        return

    if data == "browse":

        keyboard = [
            [InlineKeyboardButton("🎬 Action Movies", callback_data="cat:Action")],
            [InlineKeyboardButton("❤️ Romance Movies", callback_data="cat:Romance")],
            [InlineKeyboardButton("👻 Horror Movies", callback_data="cat:Horror")],
            [InlineKeyboardButton("📺 Series", callback_data="cat:Series")],
            [InlineKeyboardButton("🎧 DJ Smith", callback_data="cat:DJ Smith")],
            [InlineKeyboardButton("🎧 DJ Afro", callback_data="cat:DJ Afro")],
            [InlineKeyboardButton("🔥 Kenyan Leaks", callback_data="cat:Kenyan Leaks")],
            [InlineKeyboardButton("🏠 Home", callback_data="home")],
        ]

        await query.edit_message_text(
            "🎬 Browse Movies\n\nChoose a category:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if data == "orders":
        await my_orders(update, context)
        return

    if data == "help":
        await query.edit_message_text(
            "❓ Help\n\n"
            "1. Browse Movies.\n"
            "2. Select a movie.\n"
            "3. Pay with M-PESA or Wallet.\n"
            "4. Receive your movie automatically.\n\n"
            "Need help? Contact the admin.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="home")]
            ])
        )
        return

    if data.startswith("cat:"):
        await show_category(update, context)
        return

    if data.startswith("movie:"):
        await show_movie(update, context)
        return

    if data.startswith("parts:"):
        await show_parts(update, context)
        return

    if data.startswith("buypart:"):
        await buy_part(update, context)
        return

    if data.startswith("mpesa:"):

        part_id = int(data.split(":")[1])

        part = fetchone(
            "SELECT movie_id, part_name, price FROM parts WHERE id=?",
            (part_id,)
        )

        if not part:
            await query.message.reply_text(
                "❌ Part not found."
            )
            return

        context.user_data["part_id"] = part_id
        context.user_data["movie_id"] = part[0]
        context.user_data["amount"] = part[2]
        context.user_data["buy_all"] = False

        await query.message.reply_text(
            f"🎬 {part[1]}\n"
            f"💰 Price: KSh {part[2]}\n\n"
            "📱 Send your M-Pesa/Airtel phone number:"
        )

        return

    if data.startswith("walletpay:"):

        part_id = int(data.split(":")[1])

        balance = fetchone(
            "SELECT balance FROM wallet WHERE user_id=?",
            (query.from_user.id,)
        )

        if not balance:
            await query.message.reply_text(
                "❌ Your wallet is empty."
            )
            return

        amount = fetchone(
            "SELECT price FROM parts WHERE id=?",
            (part_id,)
        )[0]

        if balance[0] < amount:
            await query.message.reply_text(
                f"❌ Insufficient balance.\n\n"
                f"Wallet: KSh {balance[0]}\n"
                f"Price: KSh {amount}"
            )
            return

        execute(
            "UPDATE wallet SET balance = balance - ? WHERE user_id=?",
            (amount, query.from_user.id)
        )

        execute(
            """
            INSERT INTO wallet_transactions
            (user_id, type, amount, description)
            VALUES (?, ?, ?, ?)
            """,
            (
                query.from_user.id,
                "DEBIT",
                amount,
                "Movie purchase"
            )
        )

        await deliver_video(
            query.from_user.id,
            part_id,
            context
        )

        await query.message.reply_text(
            "✅ Payment successful!\n\n"
            "🎬 Your movie has been delivered."
        )

        return


        context.user_data["part_id"] = part_id
        context.user_data["movie_id"] = part[0]
        context.user_data["amount"] = part[2]
        context.user_data["buy_all"] = False

        await query.message.reply_text(
            f"🎬 {part[1]}\n"
            f"💰 Price: KSh {part[2]}\n\n"
            "📱 Send your M-Pesa/Airtel phone number:"
        )

        return

    if data.startswith("buyall:"):

        movie_id = int(data.split(":")[1])

        parts = fetchall(
            "SELECT id FROM parts WHERE movie_id=?",
            (movie_id,)
        )

        total = len(parts) * DEFAULT_PART_PRICE

        context.user_data["movie_id"] = movie_id
        context.user_data["amount"] = total
        context.user_data["part_id"] = None

        await query.message.reply_text(
            f"📦 Buy All Parts\n"
            f"💰 Total: KSh {total}\n\n"
            "📱 Send your M-PESA/Airtel number:"
        )
        return

# ==========================
# MAIN
# ==========================

def main():

    app = Application.builder().token(BOT_TOKEN).build()

    # User commands
    app.add_handler(
        CommandHandler("start", start)
    )

    # Admin
    app.add_handler(
        CommandHandler("admin", admin_panel)
    )

    # Movie / Part upload
    app.add_handler(movie_conversation)
    app.add_handler(part_conversation)

    # Buttons
    app.add_handler(
        CallbackQueryHandler(buttons)
    )

    # Phone input

    app.add_handler(
        MessageHandler(
            filters.Regex(r"^\d+$"),
            handle_wallet_amount,
            block=False
        ),
        group=0
    )

    app.add_handler(
        MessageHandler(
            filters.Regex(r"^(07|01|2547|2541)\d+$"),
            handle_phone,
            block=False
        ),
        group=1
    )

    app.job_queue.run_repeating(
        check_paid_orders,
        interval=5,
        first=5,
    )

    app.job_queue.run_repeating(
        check_paid_topups,
        interval=5,
        first=5,
    )

    print("🎬 RAJUL MOVIES BOT RUNNING...")

    threading.Thread(
        target=health.app.run,
        kwargs={
            "host": "0.0.0.0",
            "port": int(os.environ.get("PORT", 10000))
    },
    daemon=True
).start()

    app.run_polling()


if __name__ == "__main__":
    main()





