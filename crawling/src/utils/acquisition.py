import logging
import aiohttp

from crawling.src.core.types import (
    SelectHtmlOrJson,
    SelectResponseType,
    UrlStatusCodeOrUrlAddress,
)
from crawling.src.core.abstract.abstract_async_request import (
    AbstractAsyncRequestAcquisition,
)


# fmt: off
class AsyncRequestAcquisitionHTML(AbstractAsyncRequestAcquisition):
    """비동기 HTML 처리 클래스"""
    async def async_source(self, response: aiohttp.ClientResponse, response_type: str) -> SelectHtmlOrJson:
        """
        비동기 HTML 또는 JSON 호출
        
        Args:
            response (aiohttp.ClientResponse) : session
            response_type (str): 가져올 데이터의 유형 ("html" 또는 "json")

        Returns:
            str | dict: HTML 또는 JSON 데이터
    
        """
        try:
            if response_type == "html":
                return await response.text("utf-8")
            elif response_type == "json":
                return await response.json()
        except Exception as error:
            self.logging.log_message_sync(logging.ERROR, f"다음과 같은 에러로 가져올 수 없습니다 --> {error}")

    async def async_request(self, response: aiohttp.ClientResponse) -> UrlStatusCodeOrUrlAddress:
        """비동기 방식으로 원격 자원에 요청하고 상태 코드를 분류함

        Args:
            response (aiohttp.ClientResponse) : session

        Returns:
          UrlStatusCodeOrUrlAddress : 요청 결과 URL 또는 상태 코드
        """
        if response.status == 200:
            return self.url
        else:
            return {"status": response.status}

    async def async_type(self, type_: str, source: str | None = None) -> SelectResponseType:
        """
        Args:
            type_ (str): html source 를 가지고 올지 url 상태를 가지고올지 선택
            source (str | None, optional): html source를 가지고 올 format json or html 선택
        Returns:
            SelectResponseType: 선택한 함수 의 반환값 
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url=self.url, params=self.params, headers=self.headers) as response:
                if type_ == "source":
                    return await self.async_source(response, source)
                elif type_ == "request":
                    return await self.async_request(response)
 
 
class AsyncRequestUrlStatus(AsyncRequestAcquisitionHTML):
    """URL Status(200이 아닐 경우) 또는 주소(200일 경우) 호출"""    
    async def async_request_status(self) -> UrlStatusCodeOrUrlAddress:
        self.logging.log_message_sync(logging.INFO, f"URL statue를 요청했습니다")
        return await self.async_type(type_="request")


class AsyncRequestJSON(AsyncRequestAcquisitionHTML):
    """JSON 데이터 호출"""
    
    async def async_fetch_json(self, target: str) -> SelectHtmlOrJson:
        """URL에서 JSON 데이터를 비동기로 가져옴.

        Returns:
            SelectHtmlOrJson: JSON 데이터
        """
        self.logging.log_message_sync(logging.INFO, f"{target}에서 다음과 같은 format을 사용했습니다 --> JSON")
        return await self.async_type(type_="source", source="json")


class AsyncRequestHTML(AsyncRequestAcquisitionHTML):
    """HTML 데이터 호출"""
    
    async def async_fetch_html(self, target) -> SelectHtmlOrJson:
        """URL에서 HTML 데이터를 비동기로 가져옴.

        Returns:
            SelectHtmlOrJson: HTML 데이터
        """
        self.logging.log_message_sync(logging.INFO, f"{target}에서 다음과 같은 format을 사용했습니다 --> HTML")
        return await self.async_type(type_="source", source="html")
