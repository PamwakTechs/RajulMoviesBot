import sqlite3
from config import DB_NAME


def connect():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = connect()
    cur = conn.cursor()

    # Movies
    cur.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        poster_file_id TEXT
    )
    """)

    # Movie Parts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS parts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_id INTEGER NOT NULL,
        part_name TEXT NOT NULL,
        poster_file_id TEXT,
        video_file_id TEXT,
        price INTEGER NOT NULL,
        FOREIGN KEY(movie_id) REFERENCES movies(id)
    )
    """)

    # Orders
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        movie_id INTEGER,
        part_id INTEGER,
        phone TEXT,
        amount INTEGER,
        checkout_id TEXT,
        status TEXT DEFAULT 'PENDING',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS paid_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        part_id INTEGER
    )
    """)

    conn.commit()
    conn.close()

def execute(query, params=()):
    conn = connect()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()


def fetchone(query, params=()):
    conn = connect()
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row


def fetchall(query, params=()):
    conn = connect()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_wallet_balance(user_id):
    conn = sqlite3.connect("movies.db")
    cur = conn.cursor()

    cur.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    conn.close()

    if row:
        return row[0]
    return 0


def update_wallet_balance(user_id, amount):
    conn = sqlite3.connect("movies.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO wallet (user_id, balance)
        VALUES (?, 0)
    """, (user_id,))

    cur.execute("""
        UPDATE wallet
        SET balance = balance + ?
        WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()


def save_wallet_transaction(user_id, tx_type, amount, description):
    conn = sqlite3.connect("movies.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO wallet_transactions
        (user_id, type, amount, description)
        VALUES (?, ?, ?, ?)
    """, (user_id, tx_type, amount, description))

    conn.commit()
    conn.close()

def save_order(telegram_id, movie_id, part_id, phone, amount, checkout_id):
    execute(
        """
        INSERT INTO orders
        (telegram_id, movie_id, part_id, phone, amount, checkout_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            telegram_id,
            movie_id,
            part_id,
            phone,
            amount,
            checkout_id
        )
    )

def get_paid_orders():
    return fetchall(
        """
        SELECT id, telegram_id, part_id
        FROM orders
        WHERE status='PAID'
        """
    )


def mark_delivered(order_id):
    execute(
        """
        UPDATE orders
        SET status='DELIVERED'
        WHERE id=?
        """,
        (order_id,)
    )

init_db()

