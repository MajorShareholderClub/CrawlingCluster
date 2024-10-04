"""모음집"""

import configparser
from pathlib import Path


path_location = Path(__file__)

# key_parser
parser = configparser.ConfigParser()
parser.read(f"{path_location.parent}/url.conf")

naver_id: str = parser.get("naver", "X-Naver-Client-Id")
naver_secret: str = parser.get("naver", "X-Naver-Client-Secret")
naver_url: str = parser.get("naver", "NAVER_URL")


daum_url: str = parser.get("daum", "DAUM_URL")
daum_auth: str = parser.get("daum", "Authorization")

INVESTING_NEWS_BOTTEN = '//*[@id="bottom-nav-row"]/div[1]/nav/ul/li[5]/div[1]/a'
INVESTING_NEWS_NEXT = '//*[@id="__next"]/div[2]/div[2]/div[2]/div[1]/div/div[2]/div'
INVESTING_CATEGORY = '//*[@id="bottom-nav-row"]/div[2]/div/nav/ul'
