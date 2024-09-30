import sys

[sys.path.append(i) for i in [".", ".."]]

import asyncio
import pytest
from unittest.mock import patch, AsyncMock
from crawling.src.driver.api_news_driver import AsyncNaverNewsParsingDriver


@pytest.mark.asyncio
async def test_async_parsing_with_data():
    driver = AsyncNaverNewsParsingDriver(target="비트코인", count=1)

    with patch(
        "crawling.src.utils.acquisition.AsyncRequestJSON", autospec=True
    ) as mock_request:

        mock_request.return_value.async_fetch_json = AsyncMock()

        parsed_articles = await driver.extract_news_urls()

        # Mocked response data
        mocked_data = parsed_articles

        # Mock async_fetch_json to return the mocked data
        mock_request.return_value.async_fetch_json.return_value = mocked_data

        assert len(mocked_data) == 100
        assert type(mocked_data[0]["title"]) is str
        assert type(mocked_data[0]["url"]) is str


asyncio.run(test_async_parsing_with_data())
