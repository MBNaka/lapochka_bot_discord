import asyncio

import pytest

from utils.track_card import create_track_card


@pytest.mark.asyncio
async def test_create_track_card_no_cover():
    # Проверяем, что функция возвращает BytesIO даже без обложки
    result = await create_track_card("Test Track", "Test Artist")
    assert hasattr(result, "read")
    assert result.getbuffer().nbytes > 0


@pytest.mark.asyncio
async def test_create_track_card_with_fake_url():
    # Проверяем, что функция не падает при невалидном URL
    result = await create_track_card(
        "Test Track", "Test Artist", cover_url="http://invalid-url"
    )
    assert hasattr(result, "read")
    assert result.getbuffer().nbytes > 0
