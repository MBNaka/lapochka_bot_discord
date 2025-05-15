from utils.settings import get_guild_setting
from embeds import member_join

import json

ADMIN_MESSAGES = {
    "no_permission": "❌ У вас нет прав для выполнения этой команды.",
    "already_admin": "❌ Этот пользователь уже является администратором.",
    "added_admin": "✅ Пользователь {mention} добавлен в список админов.",
    "removed_admin": "✅ Пользователь {mention} удалён из списка админов.",
    "no_greeting": "❌ У пользователя нет сохранённого поздравления.",
    "greeting_updated": "✅ Поздравление успешно обновлено!",
    "admin_list_empty": "Список администраторов пуст.",
    "admin_list": "**Список администраторов:**\n{admin_list}",
}

WELCOME_MESSAGES = {
    "enabled": "✅ Приветственные сообщения включены!",
    "disabled": "✅ Приветственные сообщения выключены!",
    "channel_set": "✅ Канал для приветствий установлен: {}",
    "message_updated": "✅ Текст приветствия обновлен!",
    "no_channel": "❌ Укажите канал!",
    "no_permission": "❌ У вас нет прав на использование этой команды!",
}

MESSAGES = {
    "not_in_voice": "Пожалуйста, подключись к каналу, прежде чем звать меня 😽",
    "connect_error": "Не удалось подключиться к голосовому каналу 😿",
    "track_not_found": "Я попытался поискать твой трек, но так ничего и не нашёл 😿",
    "queue_empty": "📭 Очередь пуста.",
    "player_not_playing": "Я не могу выполнить действие, потому что музыка не играет 😿. Попробуй включить меня",
    "skip_nothing": "Я не могу пропустить трек, потому что пропускать нечего 😿. Попробуй включить меня",
    "stopped": "Остановил плеер",
    "paused": "Поставил на паузу",
    "resumed": "Возобновил трек",
    "volume_set": "Установил уровень громкости на {value}%",
    "volume_invalid": "Уровень громкости должен быть 25, 50, 75 или 100",
    **WELCOME_MESSAGES,
}

TITLES = {}

DESCRIPTIONS = {}


async def get_guild_join_message(guild_id: int, username: str) -> str:
    template = await get_guild_setting(
        guild_id, "GUILD_JOIN", "Привет, я Lapochka Bot!"
    )
    return template.format(username=username)

async def get_welcome_embed(guild_id: int, user_id: int, channel_id: int) -> str:
    data = await get_guild_setting(
        guild_id, "WELCOME_EMBED", None
    )
    embed = await member_join.get_embed(data, user_id, channel_id)
    return embed

