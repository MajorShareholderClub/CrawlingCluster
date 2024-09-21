from typing import Union, TypedDict, Any, Deque

import undetected_chromedriver as uc


class UrlStatus(TypedDict):
    status: int | str


SelectHtmlOrJson = Union[str, dict[str, Any]]
UrlStatusCodeOrUrlAddress = Union[str, UrlStatus]

SelectResponseType = Union[SelectHtmlOrJson, UrlStatusCodeOrUrlAddress] | None
UrlDictCollect = Deque[dict[str, str]]


ChromeDriver = uc.Chrome
