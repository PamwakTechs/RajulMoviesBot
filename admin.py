from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from config import (
    ADMIN_ID,
    DEFAULT_PART_PRICE,
    KENYAN_LEAKS_PRICE,
)

from database import (
    connect,
    fetchall,
    execute,
)

# ==========================
# STATES
# ==========================

(
    MOVIE_NAME,
    MOVIE_CATEGORY,
    MOVIE_DESCRIPTION,
    MOVIE_POSTER,
    PART_MOVIE,
    PART_NAME,
    PART_POSTER,
    PART_VIDEO,
    PART_PRICE,
) = range(9)


# ==========================
# ADMIN CHECK
# ==========================

def is_admin(update):
    return update.effective_user.id == ADMIN_ID


# ==========================
# ADMIN PANEL
# ==========================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text("❌ Access denied.")
        return

    keyboard = [
        [InlineKeyboardButton("🎬 Add Movie", callback_data="admin_add_movie")],
        [InlineKeyboardButton("🎥 Add Part", callback_data="admin_add_part")],
        [InlineKeyboardButton("📋 Movies", callback_data="admin_movies")],
        [InlineKeyboardButton("📦 Orders", callback_data="admin_orders")],
    ]

    await update.message.reply_text(
        "🔐 RAJUL MOVIES ADMIN PANEL",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
# ==========================
# ADD MOVIE
# ==========================

async def add_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text("❌ Access denied.")
        return ConversationHandler.END

    context.user_data.clear()

    await update.callback_query.message.reply_text(

        "🎬 Send Movie Name:"
    )

    return MOVIE_NAME


async def movie_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["name"] = update.message.text.strip()

    await update.message.reply_text(
        "📂 Send Category:\n\n"
        "Action\n"
        "Romance\n"
        "Horror\n"
        "Series\n"
        "DJ Smith\n"
        "DJ Afro\n"
        "Kenyan Leaks"
    )

    return MOVIE_CATEGORY


async def movie_category(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["category"] = update.message.text.strip()

    await update.message.reply_text("📝 Send Movie Description:")

    return MOVIE_DESCRIPTION


async def movie_description(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["description"] = update.message.text.strip()

    await update.message.reply_text("🖼 Send Movie Poster:")

    return MOVIE_POSTER

async def movie_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message.photo:
        await update.message.reply_text(
            "❌ Please send a photo."
        )
        return MOVIE_POSTER

    poster = update.message.photo[-1].file_id

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO movies
        (name, category, description, poster_file_id)
        VALUES (?, ?, ?, ?)
        """,
        (
            context.user_data["name"],
            context.user_data["category"],
            context.user_data["description"],
            poster,
        ),
    )

    movie_id = cur.lastrowid

    conn.commit()
    conn.close()

    # ==========================
    # PUBLIC CHANNEL BUTTONS
    # ==========================

    keyboard = [
        [
            InlineKeyboardButton(
                "🎥 Buy Parts",
                url=f"https://t.me/RajpaymentBot?start=movie_{movie_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "📦 Buy All Parts",
                url=f"https://t.me/RajpaymentBot?start=buyall_{movie_id}"
            )
        ]
    ]

    # ==========================
    # POST TO PUBLIC CHANNEL
    # ==========================

    msg = await context.bot.send_photo(
        chat_id="@rajulmoviehub",
        photo=poster,
        caption=(
            f"🎬 {context.user_data['name']}\n\n"
            f"📂 {context.user_data['category']}\n\n"
            f"{context.user_data['description']}"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    # ==========================
    # SAVE CHANNEL MESSAGE ID
    # ==========================

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE movies
        SET channel_message_id=?
        WHERE id=?
        """,
        (
            msg.message_id,
            movie_id,
        ),
    )

    conn.commit()
    conn.close()

    context.user_data.clear()

    await update.message.reply_text(
        f"✅ Movie added successfully.\n\nMovie ID: {movie_id}"
    )

    return ConversationHandler.END

# ==========================
# ADD PART
# ==========================

async def add_part_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text("❌ Access denied.")
        return ConversationHandler.END

    context.user_data.clear()

    await update.callback_query.message.reply_text(

        "🎬 Send Movie ID:"
    )

    return PART_MOVIE


async def part_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message.text.isdigit():
        await update.message.reply_text("❌ Invalid Movie ID.")
        return PART_MOVIE

    context.user_data["movie_id"] = int(update.message.text)

    await update.message.reply_text("🎥 Send Part Name (Example: Part 1)")

    return PART_NAME


async def part_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["part_name"] = update.message.text.strip()

    await update.message.reply_text("🖼 Send Part Poster")

    return PART_POSTER


async def part_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message.photo:
        await update.message.reply_text("❌ Please send a photo.")
        return PART_POSTER

    context.user_data["poster"] = update.message.photo[-1].file_id

    await update.message.reply_text(
        "🎬 Forward the movie video from your private channel."
    )

    return PART_VIDEO


async def part_video(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message.video:
        await update.message.reply_text("❌ Please send a Telegram video.")
        return PART_VIDEO

    context.user_data["video"] = update.message.video.file_id

    await update.message.reply_text("💰 Send Price (KSh):")

    return PART_PRICE

async def part_price(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message.text.isdigit():
        await update.message.reply_text("❌ Numbers only.")
        return PART_PRICE

    price = int(update.message.text)

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO parts
        (movie_id, part_name, poster_file_id, video_file_id, price)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            context.user_data["movie_id"],
            context.user_data["part_name"],
            context.user_data["poster"],
            context.user_data["video"],
            price,
        ),
    )

    conn.commit()

    cur.execute(
        """
        SELECT channel_message_id, name, category, description, poster_file_id
        FROM movies
        WHERE id=?
        """,
        (context.user_data["movie_id"],)
    )

    movie = cur.fetchone()

    cur.execute(
        """
        SELECT id, part_name
        FROM parts
        WHERE movie_id=?
        ORDER BY id
        """,
        (context.user_data["movie_id"],)
    )

    parts = cur.fetchall()

    conn.close()

    if movie and movie[0]:

        keyboard = []

        keyboard.append([
            InlineKeyboardButton(
                "🎥 Buy Parts",
                url=f"https://t.me/RajpaymentBot?start=movie_{context.user_data['movie_id']}"
            )
        ])

        keyboard.append([
            InlineKeyboardButton(
                "📦 Buy All Parts",
                url=f"https://t.me/RajpaymentBot?start=buyall_{context.user_data['movie_id']}"
            )
        ])

        await context.bot.edit_message_caption(
            chat_id="@rajulmoviehub",
            message_id=movie[0],
            caption=(
                f"🎬 {movie[1]}\n\n"
                f"📂 {movie[2]}\n\n"
                f"{movie[3]}\n\n"
                f"📦 Parts Available: {len(parts)}"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    context.user_data.clear()

    await update.message.reply_text(
        "✅ Part added successfully and public post updated."
    )

    return ConversationHandler.END

# ==========================
# CONVERSATIONS
# ==========================

from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

movie_conversation = ConversationHandler(
    entry_points=[
        CommandHandler("addmovie", add_movie_start),
        CallbackQueryHandler(
            add_movie_start,
            pattern="^admin_add_movie$"
        ),
    ],
    states={
        MOVIE_NAME: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                movie_name
            )
        ],
        MOVIE_CATEGORY: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                movie_category
            )
        ],
        MOVIE_DESCRIPTION: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                movie_description
            )
        ],
        MOVIE_POSTER: [
            MessageHandler(
                filters.PHOTO,
                movie_poster
            )
        ],
    },
    fallbacks=[],
)
part_conversation = ConversationHandler(
    entry_points=[
        CommandHandler("addpart", add_part_start),
        CallbackQueryHandler(
            add_part_start,
            pattern="^admin_add_part$"
        ),
    ],
    states={
        PART_MOVIE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, part_movie)
        ],
        PART_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, part_name)
        ],
        PART_POSTER: [
            MessageHandler(filters.PHOTO, part_poster)
        ],
        PART_VIDEO: [
            MessageHandler(filters.VIDEO, part_video)
        ],
        PART_PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, part_price)
        ],
    },
    fallbacks=[],
)

