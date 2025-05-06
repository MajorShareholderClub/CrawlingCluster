from abc import ABC, abstractmethod

import httpx
from crawling.src.core.types import (
    SelectHtmlOrJson,
    SelectResponseType,
    UrlStatusCodeOrUrlAddress,
)
from common.utils.logging_utils import EnhancedLogger

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
        self.logging = EnhancedLogger(
            name="request",
            file_name="request.log"
        )

    @abstractmethod
    async def async_source(self, response: httpx.Response, response_type: str) -> SelectHtmlOrJson: 
        raise NotImplementedError()

    @abstractmethod
    async def async_request(self, response: httpx.Response) -> UrlStatusCodeOrUrlAddress: 
        raise NotImplementedError()

    @abstractmethod
    async def async_type(self, type_: str, source: str | None = None) -> SelectResponseType: 
        raise NotImplementedError()
