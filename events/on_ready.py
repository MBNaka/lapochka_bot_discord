import wavelink
import logging
import discord

from loader import (bot, LAVALINK_HOST, LAVALINK_HOST_1, LAVALINK_HOST_2, LAVALINK_HOST_3,
                    LAVALINK_PASSWORD, LAVALINK_PASSWORD_1, LAVALINK_PASSWORD_2, LAVALINK_PASSWORD_3,
                    logger)

# Список хостов и паролей для выбора
nodes = [
    {"host": LAVALINK_HOST, "password": LAVALINK_PASSWORD},  # Хост 0
    {"host": LAVALINK_HOST_1, "password": LAVALINK_PASSWORD_1},  # Хост 1
    {"host": LAVALINK_HOST_2, "password": LAVALINK_PASSWORD_2},  # Хост 2
    {"host": LAVALINK_HOST_3, "password": LAVALINK_PASSWORD_3}
]

@bot.event
async def on_ready():
    discord.utils.setup_logging(level=logging.DEBUG)
    logger.info("Logged in: %s | %s", bot.user, bot.user.id)

    # Выбор хоста при старте
    print("Выберите хост для подключения (0, 1, 2, 3):")
    choice = input() 

    # Проверка правильности выбора
    if choice not in ["0", "1", "2", "3"]:
        print("Некорректный выбор, подключение будет выполнено к хосту 2.")
        choice = "2"

    # Подключение к выбранному хосту
    selected_node = nodes[int(choice)]
    node = wavelink.Node(
        uri=selected_node["host"],  # Хост выбранный пользователем
        password=selected_node["password"],  # Пароль для этого хоста
    )

    await wavelink.Pool.connect(nodes=[node], client=bot)
    logger.info(f"Lavalink node {choice} connected!")
    await bot.tree.sync()
