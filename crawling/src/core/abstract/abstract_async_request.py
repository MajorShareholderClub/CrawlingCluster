from abc import ABC, abstractmethod

import aiohttp

from crawling.src.core.types import (
    SelectHtmlOrJson,
    SelectResponseType,
    UrlStatusCodeOrUrlAddress,
)
from crawling.src.utils.logger import AsyncLogger

# fmt: off
class AbstractAsyncRequestAcquisition(ABC):
    """비동기 호출의 추상 클래스"""

    def __init__(
        self, 
        url: str, 
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.url = url
        self.params = params
        self.headers = headers
        self.logging = AsyncLogger(target="request", log_file="request.log")

    @abstractmethod
    async def async_source(self, response: aiohttp.ClientSession, response_type: str) -> SelectHtmlOrJson: 
        raise NotImplementedError()

    @abstractmethod
    async def async_request(self, response: aiohttp.ClientSession) -> UrlStatusCodeOrUrlAddress: 
        raise NotImplementedError()

    @abstractmethod
    async def async_type(self, type_: str, source: str | None = None) -> SelectResponseType: 
        raise NotImplementedError()
