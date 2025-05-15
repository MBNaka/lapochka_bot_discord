from io import BytesIO
from typing import Optional

import aiohttp
from colorthief import ColorThief
from PIL import Image, ImageDraw, ImageFont

from loader import aiohttp_session, init_aiohttp_session, logger

# Пути к файлам
FONT_PATH = "media/fonts/Montserrat-Bold.ttf"  # Путь к шрифту
TEMPLATE_IMAGE = "media/templates/music_template.jpg"  # Шаблонное изображение

CARD_WIDTH = 700
CARD_HEIGHT = 400
COVER_SIZE = 250
TEXT_GAP = 30  # Отступ текста от картинки


async def download_image(url: str) -> Optional[BytesIO]:
    """Простая асинхронная загрузка изображения по URL"""
    logger.info(f"Downloading image from {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        if aiohttp_session is None:
            await init_aiohttp_session()
        async with aiohttp_session.get(url, headers=headers, timeout=30) as response:
            if response.status == 200:
                data = await response.read()
                return BytesIO(data)
            else:
                logger.error(f"Failed to download image. Status: {response.status}")
                return None
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        return None


async def create_track_card(
    track_title: str, artist_name: str, cover_url: Optional[str] = None
) -> BytesIO:
    """Генерирует изображение карточки трека асинхронно"""
    logger.info(f"Creating track card for {track_title} by {artist_name}")
    try:
        # Загрузка обложки (или шаблона)
        if cover_url:
            image_data = await download_image(cover_url)
            if image_data:
                logger.info(f"Image downloaded successfully")
                cover = Image.open(image_data).convert("RGBA")
            else:
                logger.info(f"Image download failed. Use template instead")
                cover = Image.open(TEMPLATE_IMAGE).convert("RGBA")
        else:
            logger.info(f"No cover image provided. Use template instead")
            cover = Image.open(TEMPLATE_IMAGE).convert("RGBA")

        # Обрезка изображения до квадрата
        logger.debug(f"Cropping image to {COVER_SIZE}x{COVER_SIZE}")
        min_side = min(cover.size)
        cover = cover.crop((0, 0, min_side, min_side)).resize((COVER_SIZE, COVER_SIZE))

        # Скругленные углы
        logger.debug(f"Rounding corners of image")
        mask = Image.new("L", (COVER_SIZE, COVER_SIZE), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, COVER_SIZE, COVER_SIZE), radius=40, fill=255)
        cover.putalpha(mask)

        # Определение цвета фона
        logger.debug(f"Determining dominant color")
        try:
            if cover_url and image_data:
                image_data.seek(0)
                color_thief = ColorThief(image_data)
            else:
                color_thief = ColorThief(TEMPLATE_IMAGE)
            dominant_color = color_thief.get_color(quality=10)
        except Exception as e:
            logger.error(f"Color detection failed: {e}")
            dominant_color = (50, 50, 50)

        # Создание фонового изображения
        logger.debug(f"Creating background image")
        background = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), dominant_color)

        # Вставка обложки (по центру, чуть выше середины)
        logger.debug(f"Inserting cover image")
        cover_x = (CARD_WIDTH - COVER_SIZE) // 2
        cover_y = (CARD_HEIGHT // 2) - (COVER_SIZE // 2) - 20
        background.paste(cover, (cover_x, cover_y), cover)

        # Определение цвета текста
        logger.debug(f"Determining text color")
        brightness = sum(dominant_color) / 3
        text_color = (255, 255, 255) if brightness < 128 else (0, 0, 0)

        # Добавление текста
        logger.debug(f"Drawing text")
        draw = ImageDraw.Draw(background)
        font_title = ImageFont.truetype(FONT_PATH, 35)
        font_artist = ImageFont.truetype(FONT_PATH, 18)

        # Координаты текста
        logger.debug(f"Calculating text coordinates")
        text_x = CARD_WIDTH // 2
        title_y = cover_y + COVER_SIZE + TEXT_GAP  # Немного ниже обложки
        artist_y = title_y + 35  # Отступ между названием и исполнителем

        # Размещение текста
        logger.debug(f"Inserting text")
        draw.text(
            (text_x, title_y),
            track_title,
            fill=text_color,
            font=font_title,
            anchor="mm",
        )
        draw.text(
            (text_x, artist_y),
            artist_name,
            fill=text_color,
            font=font_artist,
            anchor="mm",
        )

        # Сохранение изображения в BytesIO
        logger.debug(f"Saving image to BytesIO")
        output = BytesIO()
        background.save(output, format="PNG")
        output.seek(0)
        logger.info("Image saved to BytesIO")
        return output
    except Exception as e:
        logger.error(f"Failed to create track card: {e}")
        # Возвращаем пустой BytesIO, чтобы не падал бот
        return BytesIO()
