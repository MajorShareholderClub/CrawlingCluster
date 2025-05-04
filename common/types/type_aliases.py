"""전체 프로젝트에서 사용되는 타입 정의

이 모듈은 프로젝트 전체에서 공통으로 사용하는 타입 별칭과 TypedDict들을 정의합니다.
"""

from __future__ import annotations

from typing import Any, TypedDict, TypeVar, Protocol, NewType
from datetime import datetime

# Type Variables
T = TypeVar("T")  # Generic type for any return value

# HTML Type
HTML = NewType("HTML", str)
SelectHtml = HTML


# 크롤링 관련 타입 정의
class UrlStatus(TypedDict):
    """URL 상태 정보"""

    status: int | str


# 크롤링 결과 데이터 타입
SelectJson = dict[str, str | int] | dict[str, Any]
SelectHtmlOrJson = SelectHtml | SelectJson


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
