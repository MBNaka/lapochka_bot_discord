# database/birthday.py
import json
import os
import sqlite3
from typing import Any, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "birthdays.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


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
            {"title": "С Днём рождения!", "description": "WIP", "image_url": None}
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
    from datetime import datetime

    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO birthday_role_assignments (guild_id, user_id, assigned_at) VALUES (?, ?, ?)",
            (guild_id, user_id, datetime.now().isoformat()),
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
