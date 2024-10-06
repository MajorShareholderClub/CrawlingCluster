from typing import Union, TypedDict, Any, Deque, NewType
import undetected_chromedriver as uc


HTML = NewType("HTML", str)


class UrlStatus(TypedDict):
    status: int | str


SelectHtml = HTML
SelectJson = dict[str, str | int]
SelectHtmlOrJson = SelectHtml | SelectJson

UrlStatusCodeOrUrlAddress = Union[str, UrlStatus]

SelectResponseType = Union[SelectHtmlOrJson, UrlStatusCodeOrUrlAddress] | None
UrlDictCollect = list[dict[str, str]]


ChromeDriver = uc.Chrome
