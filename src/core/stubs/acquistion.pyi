"""
[AsyncRequestAcquisitionHTML and Derived Classes]

이 파일은 비동기 HTTP 요청을 관리하는 AsyncRequestAcquisitionHTML 클래스를 비롯한 여러 관련 클래스를 정의한 타입 힌팅 파일입니다.
비동기적으로 HTML 및 JSON 데이터를 처리하고, URL의 상태 코드를 확인하는 기능을 제공합니다. 
이 클래스를 활용하면 대규모 네트워크 호출을 효율적으로 수행할 수 있습니다.

-------------------------------------
| AsyncRequestAcquisitionHTML Class |
-------------------------------------
- __init__(self, url: str, params: dict[str, str] | None = None, headers: dict[str, str] | None = None) -> None: 
    ---> 클래스 초기화 함수로, 요청할 URL과 선택적인 파라미터, 헤더를 설정합니다.
- async def async_source(self, response: aiohttp.ClientSession, response_type: str) -> SelectHtmlOrJson: 
    ---> 비동기적으로 HTML 또는 JSON 소스를 가져오는 함수입니다.
- async def async_request(self, response: aiohttp.ClientSession) -> UrlStatusCodeOrUrlAddress: 
    ---> 비동기적으로 요청을 실행하여 상태 코드나 URL을 반환합니다.
- async def async_type(self, type_: str, source: str | None = None) -> SelectResponseType: 
    ---> 응답 형식을 선택하여 반환하는 비동기 함수입니다.

-------------------------------
| AsyncRequestUrlStatus Class |
-------------------------------
- async def async_request_status(url: str) -> UrlStatusCodeOrUrlAddress: 
    ---> 주어진 URL에 대한 상태 코드를 비동기적으로 확인하는 함수입니다.

----------------------------
| AsyncRequestHTML Class |
----------------------------
- async def async_fetch_content(url: str) -> SelectHtmlOrJson: 
    ---> 주어진 URL에서 HTML 데이터를 비동기적으로 가져오는 함수입니다.

----------------------------
| AsyncRequestJSON Class |
----------------------------
- async def async_fetch_content(url: str) -> SelectHtmlOrJson: 
    ---> 주어진 URL에서 JSON 데이터를 비동기적으로 가져오는 함수입니다.

------------
| Features |
------------
1. 비동기 HTTP 요청 처리: aiohttp 라이브러리를 기반으로 하여 비동기 HTTP 요청을 수행하고, 대규모 네트워크 호출을 비효율 없이 처리할 수 있습니다.
2. 다양한 응답 형식 지원: HTML 및 JSON 형식의 데이터를 처리할 수 있으며, URL 상태 코드도 확인할 수 있습니다.
3. 유연한 요청 옵션: 요청 시 파라미터와 헤더를 자유롭게 설정하여 유연한 HTTP 요청이 가능합니다.
4. 확장 가능성: 추가적인 요청 기능을 구현할 수 있도록 AsyncRequestAcquisitionHTML 클래스를 상속하여 확장 가능합니다.

"""

import aiohttp

from src.core.types import (
    SelectHtmlOrJson,
    UrlStatusCodeOrUrlAddress,
    SelectResponseType,
)

# fmt: off
class AsyncRequestAcquisitionHTML:
    """비동기 호출의 기본 클래스"""
    
    def __init__(
        self, 
        url: str, 
        params: dict[str, str] | None = None, 
        headers: dict[str, str] | None = None, 
    ) -> None:
        ...
    
    async def async_source(self, response: aiohttp.ClientSession, response_type: str) -> SelectHtmlOrJson: ...
    async def async_request(self, response: aiohttp.ClientSession) -> UrlStatusCodeOrUrlAddress: ...
    async def async_type(self, type_: str, source: str | None = None) -> SelectResponseType: ...


class AsyncRequestUrlStatus(AsyncRequestAcquisitionHTML):
    async def async_request_status(url: str) -> UrlStatusCodeOrUrlAddress: ...


class AsyncRequestHTML(AsyncRequestAcquisitionHTML):
    async def async_fetch_content(url: str) -> SelectHtmlOrJson: ...

    
class AsyncRequestJSON(AsyncRequestAcquisitionHTML):
    async def async_fetch_content(url: str) -> SelectHtmlOrJson: ...
