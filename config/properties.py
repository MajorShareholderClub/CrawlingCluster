"""모음집"""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import yaml
from typing import TypedDict, Literal

resource_path = Path(__file__).parent / "cy"


class RedisClusterConfig(TypedDict):
    """Redis 클러스터 설정"""

    id: str
    host: str
    port: int
    role: Literal["reader", "writer", "backup"]


class ConfigBaseSettings(BaseSettings):
    """설정 기본 클래스"""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="_",
        extra="allow",
    )


class SiteAPISettings(ConfigBaseSettings):
    """API 설정"""

    naver_id: str | None = Field(alias="naver_id", default_factory=str)
    naver_secret: str | None = Field(alias="naver_secret", default_factory=str)
    naver_url: str | None = Field(alias="naver_url", default_factory=str)
    daum_url: str | None = Field(alias="daum_url", default_factory=str)
    daum_auth: str | None = Field(alias="daum_auth", default_factory=str)
    mongo_uri: str | None = Field(alias="mongo_uri", default_factory=str)
    with_time: int = 5

    model_config: SettingsConfigDict = ConfigBaseSettings.model_config.copy()
    model_config.update(env_file=str(resource_path / "url.conf"))


class DatabaseSettings(ConfigBaseSettings):
    """데이터베이스 설정"""

    database_url: str | None = Field(alias="database_url", default_factory=str)
    root_password: str | None = Field(alias="root_password", default_factory=str)
    database: str | None = Field(alias="database", default_factory=str)
    user: str | None = Field(alias="user", default_factory=str)
    password: str | None = Field(alias="password", default_factory=str)

    model_config: SettingsConfigDict = ConfigBaseSettings.model_config.copy()
    model_config.update(env_file=str(resource_path / ".env"))


class RedisSettings(ConfigBaseSettings):
    """Redis 설정"""

    redis_clusters: dict[str, list[RedisClusterConfig]] = Field(
        alias="redis_clusters", default_factory=dict
    )

    @classmethod
    def from_config(cls) -> RedisSettings:
        """redis 설정 파일에서 RedisSettings 인스턴스 생성"""
        with open(str(resource_path / "database.yaml"), "r") as file:
            redis_clusters = yaml.safe_load(file)
        return cls(redis_clusters=redis_clusters)


class BaseUrlSettings(ConfigBaseSettings):
    """URL 설정 기본 클래스"""

    @classmethod
    def load_yaml_config(cls, key: str) -> dict:
        """YAML 파일에서 설정 로드

        Args:
            key (str): YAML 파일에서 가져올 설정의 키

        Returns:
            dict: 로드된 설정 데이터
        """
        with open(str(resource_path / "sites.yaml"), "r") as file:
            return yaml.safe_load(file)[key]


class SeleniumSearchUrlSettings(BaseUrlSettings):
    """검색 엔진 URL 설정"""

    daum_url: str = Field(alias="daum_url", default_factory=str)
    google_url: str = Field(alias="google_url", default_factory=str)

    @classmethod
    def from_config(cls) -> SeleniumSearchUrlSettings:
        """search_url 설정에서 인스턴스 생성"""
        search_url = cls.load_yaml_config("search_url")
        return cls(**search_url)


# 설정 로드
site_api_settings = SiteAPISettings()
database_settings = DatabaseSettings()
redis_settings = RedisSettings().from_config()
# selenium_search_url_settings = SeleniumSearchUrlSettings().from_config()

# 기존 변수들을 settings 객체로 대체
naver_id = site_api_settings.naver_id
naver_secret = site_api_settings.naver_secret
naver_url = site_api_settings.naver_url
daum_url = site_api_settings.daum_url
daum_auth = site_api_settings.daum_auth
mongo_uri = site_api_settings.mongo_uri
with_time = site_api_settings.with_time

# Redis 및 데이터베이스 설정
database_url = database_settings.database_url
root_password = database_settings.root_password
database = database_settings.database
user = database_settings.user
password = database_settings.password
redis_clusters = redis_settings.redis_clusters


# Investing 관련 상수 (crawling/config/properties.py에서 이동)
INVESTING_NEWS_BUTTON = '//*[@id="bottom-nav-row"]/div[1]/nav/ul/li[5]/div[1]/a'
INVESTING_NEWS_NEXT = '//*[@id="__next"]/div[2]/div[2]/div[2]/div[1]/div/div[2]/div'
INVESTING_CATEGORY = '//*[@id="bottom-nav-row"]/div[2]/div/nav/ul'
