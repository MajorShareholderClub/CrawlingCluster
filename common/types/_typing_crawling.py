from datetime import datetime
from typing import TypedDict, Any, NewType
import undetected_chromedriver as uc


HTML = NewType("HTML", str)


class UrlStatus(TypedDict):
    status: int | str


SelectHtml = HTML
SelectJson = dict[str, str | int] | dict[str, Any]
SelectHtmlOrJson = SelectHtml | SelectJson

UrlStatusCodeOrUrlAddress = str | UrlStatus

SelectResponseType = SelectHtmlOrJson | UrlStatusCodeOrUrlAddress | None

CrawlingAPIND = list[dict[str, dict[str, list[dict[str, str]]]]]
ChromeDriver = uc.Chrome


# 기사 URL 및 메타데이터
class UrlDict(TypedDict):
    """URL 및 관련 메타데이터"""

    url: str
    title: str
    source: str
    domain: str
    summary: str
    time_ago: str


UrlDictCollect = list[UrlDict]
KeywordDictionary = dict[str, dict[str, dict[str, UrlDictCollect]]]


# Article 데이터 타입 정의
class ArticleDict(TypedDict, total=False):
    """기사 데이터 타입"""

    url: str
    title: str
    content: str
    source: str
    pub_date: datetime | str
    timestamp: datetime
    keywords: list[str]
    summary: str
    quality_score: float
    relevance_score: float
    time_ago: str
