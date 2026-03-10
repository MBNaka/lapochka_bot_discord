"""
messages.py — централизованное хранилище всех текстовых сообщений и шаблонов для Lapochka Bot.
Содержит сообщения для команд, ошибок, подсказок, а также функции для генерации embed-ов и приветствий.
"""

from utils.settings import get_guild_setting, get_main_setting
from embeds import member_join

MESSAGES = {
    # Админ-команды
    "no_permission": "❌ У вас нет прав для выполнения этой команды.",
    "owner_only": "❌ Эту команду может использовать только владелец сервера.",
    "already_admin": "❌ Этот пользователь уже является администратором.",
    "added_admin": "✅ Пользователь {mention} добавлен в список админов.",
    "removed_admin": "✅ Пользователь {mention} удалён из списка админов.",
    "admin_list_empty": "Список администраторов пуст.",
    "admin_list": "**Список администраторов:**\n{admin_list}",
    # Приветствия
    "enabled": "✅ Приветственные сообщения включены.",
    "disabled": "✅ Приветственные сообщения выключены.",
    "channel_set": "✅ Канал для приветствий установлен: {0}",
    "message_updated": "✅ Текст приветствия обновлён.",
    "no_channel": "❌ Укажите канал для этой операции.",
    "welcome_placeholder": "Введите текст приветствия. Используйте {member} и {guild}",
    "default_welcome_message": "Привет, {member}! Добро пожаловать на сервер {guild}!",
    "already_sent": "❌ Приветственное сообщение уже отправлено ранее.",
    "welcome_sent": "✅ Приветственное сообщение отправлено в {channel}.",
    # Музыкальные команды
    "not_in_voice": "Пожалуйста, подключись к каналу, прежде чем звать меня 😽",
    "connect_error": "Не удалось подключиться к голосовому каналу 😿",
    "track_not_found": "Я попытался поискать твой трек, но так ничего и не нашёл 😿",
    "queue_empty": "📭 Очередь пуста.",
    "different_voice_channel": "❌ Нужно быть в том же голосовом канале, что и бот.",
    "player_not_playing": "Сейчас ничего не играет. Используй `/play`, чтобы запустить музыку.",
    "skip_nothing": "Нечего пропускать: сейчас ничего не играет.",
    "stopped": "⏹️ Плеер остановлен и очередь очищена.",
    "paused": "⏸️ Плеер поставлен на паузу.",
    "resumed": "▶️ Воспроизведение продолжено.",
    "volume_set": "🔊 Громкость установлена на {value}%.",
    "volume_invalid": "Уровень громкости должен быть: 25, 50, 75 или 100.",
    # Birthday-команды
    "no_greeting": "❌ У пользователя нет сохранённого поздравления.",
    "greeting_updated": "✅ Поздравление успешно обновлено!",
    "birthday_set": "✅ День рождения пользователя {mention} установлен на {date}.",
    "birthday_removed": "✅ День рождения пользователя {mention} удалён.",
    "birthday_not_found": "❌ День рождения пользователя не найден.",
    "birthday_list_empty": "Список дней рождений пуст.",
    # Setup-команды
    "setup_complete": "✅ Настройка завершена!",
    "setup_already": "Настройка уже была выполнена ранее.",
    # Общие
    "error": "Произошла ошибка. Попробуйте ещё раз позже.",
}

TITLES = {
    # Пример: "music": "Музыкальный плеер Lapochka"
}

DESCRIPTIONS = {
    # Пример: "music": "Управляй музыкой прямо в Discord!"
}

async def get_guild_join_message(username: str) -> str:
    """
    Получить приветственное сообщение для нового участника сервера.
    """
    template = await get_main_setting(
        "GUILD_JOIN", "Привет, я Lapochka Bot!"
    )
    return template.format(username=username)

async def get_welcome_embed(guild_id: int, user_id: int, channel_id: int):
    """
    Получить embed для приветствия нового участника.
    """
    data = await get_guild_setting(
        guild_id, "WELCOME_EMBED", None
    )
    embed = await member_join.get_embed(data, user_id, channel_id)
    return embed

