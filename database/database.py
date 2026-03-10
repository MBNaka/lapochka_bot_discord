# database/birthday.py
import asyncio
import json
import os
import sqlite3
from typing import Any, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "birthdays.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


async def run_in_thread(func, *args, **kwargs):
    return await asyncio.to_thread(func, *args, **kwargs)


def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        # Таблица гильдий
        c.execute(
            """CREATE TABLE IF NOT EXISTS guilds (
            guild_id TEXT PRIMARY KEY
        )"""
        )
        # Таблица пользователей
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            username TEXT NOT NULL,
            UNIQUE(guild_id, user_id),
            FOREIGN KEY(guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
        )"""
        )
        # Таблица дней рождений
        c.execute(
            """CREATE TABLE IF NOT EXISTS birthdays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            birthday TEXT NOT NULL,
            UNIQUE(guild_id, user_id),
            FOREIGN KEY(guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
            FOREIGN KEY(guild_id, user_id) REFERENCES users(guild_id, user_id) ON DELETE CASCADE
        )"""
        )
        # Таблица поздравлений (embed json)
        c.execute(
            """CREATE TABLE IF NOT EXISTS birthday_greetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            embed_json TEXT NOT NULL,
            UNIQUE(guild_id, user_id),
            FOREIGN KEY(guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
            FOREIGN KEY(guild_id, user_id) REFERENCES users(guild_id, user_id) ON DELETE CASCADE
        )"""
        )
        # Таблица админов
        c.execute(
            """CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            UNIQUE(guild_id, user_id),
            FOREIGN KEY(guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
            FOREIGN KEY(guild_id, user_id) REFERENCES users(guild_id, user_id) ON DELETE CASCADE
        )"""
        )
        # Таблица для отслеживания выданных ролей именинника
        c.execute(
            """CREATE TABLE IF NOT EXISTS birthday_role_assignments (
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            assigned_at TEXT NOT NULL,
            PRIMARY KEY(guild_id, user_id),
            FOREIGN KEY(guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
            FOREIGN KEY(guild_id, user_id) REFERENCES users(guild_id, user_id) ON DELETE CASCADE
        )"""
        )
        # Лог отправленных поздравлений, чтобы не дублировать сообщения при рестартах
        c.execute(
            """CREATE TABLE IF NOT EXISTS birthday_delivery_log (
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            delivery_date TEXT NOT NULL,
            PRIMARY KEY(guild_id, user_id, delivery_date)
        )"""
        )
        # Таблица запланированных сообщений
        c.execute(
            '''CREATE TABLE IF NOT EXISTS scheduled_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                repeat TEXT NOT NULL, -- never, day, week, month, year
                datetime TEXT NOT NULL, -- ISO формат
                channel_id TEXT NOT NULL,
                message TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                last_error TEXT,
                attempt_count INTEGER DEFAULT 0,
                last_attempt_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )'''
        )

        # Мягкая миграция для существующих БД: добавляем столбцы, если их ещё нет
        c.execute("PRAGMA table_info(scheduled_messages)")
        columns = {row[1] for row in c.fetchall()}
        if "last_error" not in columns:
            c.execute("ALTER TABLE scheduled_messages ADD COLUMN last_error TEXT")
        if "attempt_count" not in columns:
            c.execute(
                "ALTER TABLE scheduled_messages ADD COLUMN attempt_count INTEGER DEFAULT 0"
            )
        if "last_attempt_at" not in columns:
            c.execute("ALTER TABLE scheduled_messages ADD COLUMN last_attempt_at TEXT")
        conn.commit()


def register_guild(guild_id: str):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO guilds (guild_id) VALUES (?)", (guild_id,))
        conn.commit()


def register_user(guild_id: str, user_id: str, username: str):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO users (guild_id, user_id, username) VALUES (?, ?, ?)",
            (guild_id, user_id, username),
        )
        conn.commit()


def set_birthday(guild_id: str, user_id: str, birthday: str):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO birthdays (guild_id, user_id, birthday) VALUES (?, ?, ?)",
            (guild_id, user_id, birthday),
        )
        embed_json = json.dumps(
            {
                "title": "С Днём рождения!",
                "description": "Пусть этот день будет ярким и радостным!",
                "image_url": None,
            }
        )
        c.execute(
            "INSERT OR REPLACE INTO birthday_greetings (guild_id, user_id, embed_json) VALUES (?, ?, ?)",
            (guild_id, user_id, embed_json),
        )
        conn.commit()


def get_birthday(guild_id: str, user_id: str) -> Optional[str]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT birthday FROM birthdays WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        )
        row = c.fetchone()
        return row[0] if row else None


def set_greeting(guild_id: str, user_id: str, embed: Dict[str, Any]):
    with get_connection() as conn:
        c = conn.cursor()
        embed_json = json.dumps(embed)
        c.execute(
            "INSERT OR REPLACE INTO birthday_greetings (guild_id, user_id, embed_json) VALUES (?, ?, ?)",
            (guild_id, user_id, embed_json),
        )
        conn.commit()


def get_greeting(guild_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT embed_json FROM birthday_greetings WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        )
        row = c.fetchone()
        return json.loads(row[0]) if row else None


def add_admin(guild_id: str, user_id: str):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO admins (guild_id, user_id) VALUES (?, ?)",
            (guild_id, user_id),
        )
        conn.commit()


def remove_admin(guild_id: str, user_id: str):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "DELETE FROM admins WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
        )
        conn.commit()


def is_admin(guild_id: str, user_id: str) -> bool:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT 1 FROM admins WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        )
        return c.fetchone() is not None


def get_admin_ids(guild_id: str):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id FROM admins WHERE guild_id = ?", (guild_id,))
        return [row[0] for row in c.fetchall()]


def get_all_birthdays_on_date(guild_id: str, date_str: str):
    with get_connection() as conn:
        c = conn.cursor()
        # Сравниваем только день и месяц (первые 5 символов)
        c.execute(
            "SELECT user_id FROM birthdays WHERE guild_id = ? AND substr(birthday, 1, 5) = ?",
            (guild_id, date_str),
        )
        return [row[0] for row in c.fetchall()]


def assign_birthday_role(guild_id: str, user_id: str):
    from datetime import datetime, timezone

    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO birthday_role_assignments (guild_id, user_id, assigned_at) VALUES (?, ?, ?)",
            (guild_id, user_id, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def get_users_with_birthday_role(guild_id: str):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT user_id, assigned_at FROM birthday_role_assignments WHERE guild_id = ?",
            (guild_id,),
        )
        return c.fetchall()


def remove_birthday_role(guild_id: str, user_id: str):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "DELETE FROM birthday_role_assignments WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        )
        conn.commit()


def has_birthday_delivery(guild_id: str, user_id: str, delivery_date: str) -> bool:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT 1 FROM birthday_delivery_log WHERE guild_id = ? AND user_id = ? AND delivery_date = ?",
            (guild_id, user_id, delivery_date),
        )
        return c.fetchone() is not None


def mark_birthday_delivered(guild_id: str, user_id: str, delivery_date: str):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO birthday_delivery_log (guild_id, user_id, delivery_date) VALUES (?, ?, ?)",
            (guild_id, user_id, delivery_date),
        )
        conn.commit()


def add_scheduled_message(guild_id, repeat, datetime_str, channel_id, message, enabled=1):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            '''INSERT INTO scheduled_messages (guild_id, repeat, datetime, channel_id, message, enabled, last_error, attempt_count, last_attempt_at) VALUES (?, ?, ?, ?, ?, ?, NULL, 0, NULL)''',
            (guild_id, repeat, datetime_str, channel_id, message, enabled),
        )
        conn.commit()
        return c.lastrowid


def get_scheduled_messages(guild_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''SELECT id, repeat, datetime, channel_id, message, enabled FROM scheduled_messages WHERE guild_id = ? ORDER BY datetime(datetime)''', (guild_id,))
        return c.fetchall()


def get_scheduled_messages_with_meta(guild_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            '''SELECT id, repeat, datetime, channel_id, message, enabled, last_error, attempt_count, last_attempt_at
               FROM scheduled_messages
               WHERE guild_id = ?
               ORDER BY datetime(datetime)''',
            (guild_id,),
        )
        return c.fetchall()


def remove_scheduled_message(guild_id, msg_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''DELETE FROM scheduled_messages WHERE guild_id = ? AND id = ?''', (guild_id, msg_id))
        conn.commit()


def update_scheduled_message(guild_id, msg_id, repeat, datetime_str, channel_id, message, enabled=1):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''UPDATE scheduled_messages SET repeat=?, datetime=?, channel_id=?, message=?, enabled=?, updated_at=CURRENT_TIMESTAMP WHERE guild_id=? AND id=?''',
                  (repeat, datetime_str, channel_id, message, enabled, guild_id, msg_id))
        conn.commit()


def record_scheduled_message_failure(guild_id, msg_id, error_message):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            '''UPDATE scheduled_messages
               SET last_error = ?,
                   attempt_count = COALESCE(attempt_count, 0) + 1,
                   last_attempt_at = CURRENT_TIMESTAMP,
                   updated_at = CURRENT_TIMESTAMP
               WHERE guild_id = ? AND id = ?''',
            (str(error_message), guild_id, msg_id),
        )
        conn.commit()


def record_scheduled_message_success(guild_id, msg_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            '''UPDATE scheduled_messages
               SET last_error = NULL,
                   attempt_count = COALESCE(attempt_count, 0) + 1,
                   last_attempt_at = CURRENT_TIMESTAMP,
                   updated_at = CURRENT_TIMESTAMP
               WHERE guild_id = ? AND id = ?''',
            (guild_id, msg_id),
        )
        conn.commit()
