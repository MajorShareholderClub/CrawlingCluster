import httpx
import asyncio
import random

from crawling.src.core.types import (
    SelectHtmlOrJson,
    SelectHtml,
    SelectJson,
    SelectResponseType,
    UrlStatusCodeOrUrlAddress,
)
from crawling.src.core.abstract.abstract_async_request import (
    AbstractAsyncRequestAcquisition,
)


class AsyncRequestAcquisitionHTML(AbstractAsyncRequestAcquisition):
    """비동기 HTML 처리 클래스"""

    async def async_source(
        self, response: httpx.Response, response_type: str
    ) -> SelectHtmlOrJson:
        """
        비동기 HTML 또는 JSON 호출

        Args:
            response (httpx.Response) : response 객체
            response_type (str): 가져올 데이터의 유형 ("html" 또는 "json")

        Returns:
            str | dict: HTML 또는 JSON 데이터
        """
        try:
            if response_type == "html":
                return response.text
            elif response_type == "json":
                return response.json()
        except Exception as error:
            self.logging.error(f"다음과 같은 에러로 가져올 수 없습니다 --> {error}")

    async def async_request(
        self, response: httpx.Response
    ) -> UrlStatusCodeOrUrlAddress:
        """비동기 방식으로 원격 자원에 요청하고 상태 코드를 분류함

        Args:
            response (httpx.Response) : response 객체

        Returns:
          UrlStatusCodeOrUrlAddress : 요청 결과 URL 또는 상태 코드
        """
        if response.status_code == 200:
            return self.url
        else:
            return {"status": response.status_code}

    async def async_type(
        self, type_: str, target: str = "", source: str | None = None
    ) -> SelectResponseType:
        """
        Args:
            type_ (str): html source 를 가지고 올지 url 상태를 가지고올지 선택
            target (str): 어디서 가지고 오는지 (주체)
            source (str | None, optional): html source를 가지고 올 format json or html 선택
        Returns:
            SelectResponseType: 선택한 함수 의 반환값
        """
        # httpx 클라이언트 설정 - 타임아웃, 한계값 등
        limits = httpx.Limits(max_connections=100, max_keepalive_connections=10)
        timeout = httpx.Timeout(30.0, connect=10.0)

        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            response = await client.get(
                url=self.url,
                params=self.params,
                headers=self.headers,
            )
            rs: int = random.randint(1, 5)
            await asyncio.sleep(rs)
            self.logging.info(
                f"""
                {target}에서 다음과 같은 format을 사용했습니다 --> HTML,
                시간 지연은 --> {rs}초 사용합니다,
                """
            )
            if type_ == "source":
                return await self.async_source(response, source)
            elif type_ == "request":
                return await self.async_request(response)


class AsyncRequestUrlStatus(AsyncRequestAcquisitionHTML):
    """URL Status(200이 아닐 경우) 또는 주소(200일 경우) 호출"""

    async def async_request_status(self) -> UrlStatusCodeOrUrlAddress:
        self.logging.info(f"URL statue를 요청했습니다")
        return await self.async_type(type_="request")


class AsyncRequestJSON(AsyncRequestAcquisitionHTML):
    """JSON 데이터 호출"""

    async def async_fetch_json(self, target: str) -> SelectJson:
        """URL에서 JSON 데이터를 비동기로 가져옴.

        Returns:
            SelectJson: JSON 데이터
        """
        self.logging.info(f"{target}에서 다음과 같은 format을 사용했습니다 --> JSON")
        return await self.async_type(type_="source", source="json", target=target)


class AsyncRequestHTML(AsyncRequestAcquisitionHTML):
    """HTML 데이터 호출"""

    async def async_fetch_html(self, target: str) -> SelectHtml:
        """URL에서 HTML 데이터를 비동기로 가져옴.

        Returns:
            SelectHtml: HTML 데이터
        """
        self.logging.info(f"{target}에서 다음과 같은 format을 사용했습니다 --> TEXT")
        return await self.async_type(type_="source", target=target, source="html")
