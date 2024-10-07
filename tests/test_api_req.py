import sys

[sys.path.append(i) for i in [".", ".."]]

import pytest
from unittest.mock import patch, AsyncMock
from crawling.src.driver.api_req.api_news_driver import (
    AsyncNaverNewsParsingDriver,
    AsyncDaumNewsParsingDriver,
    AsyncGoogleNewsParsingDriver,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "driver_class, target, count",
    [
        (AsyncNaverNewsParsingDriver, "비트코인", 1),
        (AsyncDaumNewsParsingDriver, "비트코인", 1),
        (AsyncGoogleNewsParsingDriver, "비트코인", 1),
    ],
)
async def test_async_parsing(driver_class, target, count):
    driver = driver_class(target=target, count=count)

    with patch(
        "crawling.src.utils.acquisition.AsyncRequestJSON", autospec=True
    ) as mock_request:
        # Mock async_fetch_json
        mock_request.return_value.async_fetch_json = AsyncMock()

        # Call the method to parse articles
        parsed_articles = await driver.news_collector()

        assert len(parsed_articles) == count * 10
        assert type(parsed_articles[0]["title"]) is str
        assert type(parsed_articles[0]["url"]) is str
