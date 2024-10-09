import re
from bs4 import BeautifulSoup
from crawling.src.utils.parsing_util import parse_time_ago


class GoogleNewsCrawlingParsingSelenium:
    """
    Google News Parsing Drive
    """

    def extract_content_div(self, div_tag: BeautifulSoup) -> list[BeautifulSoup]:
        """google page 요소 두번째 접근 단계

        <div data-hveid="CA~QHw">
            <div class="MjjYud"> --> 현 위치 [구글 페이지는 맨 마지막에 MjjYud 전체 묶임]

        Returns:
            list[BeautifulSoup]: ["요소들", ~~]
        """
        return div_tag.find_all("div", {"class": "MjjYud"})

    def extract_links_from_div(self, a_tag: BeautifulSoup) -> list[BeautifulSoup]:
        """google page 요소 세번째 접근 단계

        <div data-hveid="CA~QHw">
            <div class="SoaBEf">
                <div> ~
                    <a jsname="YKoRaf"> --> 현위치

        Returns:
            list[BeautifulSoup]: ["요소들", ~~]
        """
        return a_tag.find_all("a", {"jsname": "YKoRaf"})

    def news_create_time_from_div(self, div_tag: BeautifulSoup) -> str:
        """기사 날짜
        <div class="OSrXXb rbYSKb LfVVr" style="bottom:0px">
            <span>8시간 전 ( 이부분 ) </span>
        </div>

        Returns:
            str: ex) %Y-%m-%d
        """
        return parse_time_ago(
            div_tag.find("div", {"class": "OSrXXb rbYSKb LfVVr"}).text
        )

    def div_in_data_hveid(self, html: str) -> list[BeautifulSoup]:
        """첫번째 요소 추출 시작점"""
        # 요소별 무작위 난수이므로 정규표현식 사용
        google_hveid = {
            "data-hveid": re.compile(r"CA|QHw|CA[0-9a-zA-Z]+|CB[0-9a-zA-Z]+")
        }

        soup = BeautifulSoup(html, "lxml")
        return soup.find_all("div", google_hveid)


class GoogleNewsCrawlingParsingRequest:
    def extract_content_url(self, div_tag: BeautifulSoup) -> str:
        """URL 추출
        <div class="Gx5Zad xpd EtOod pkphOe"><a data-ved=string + 뒤쪽 4자리 무작위 난수 href=target></div>
        """
        a_tags = div_tag.find("a")
        urls = re.search(r"/url\?q=(https?://[^\s&]+)", a_tags["href"])
        return urls.group(1)

    def news_create_time_from_div(self, div_tag: BeautifulSoup) -> str:
        """날짜 추출
        <div class="BNeawe s3v9rd AP7Wnd">
            <div>
                <div class="BNeawe s3v9rd AP7Wnd">
                    <span class="r0bn4c rQMQod">
                        target
                    </spen>
                </div>
            </div>
        </div
        """
        return parse_time_ago(div_tag.find("span", {"class": "r0bn4c rQMQod"}).text)

    def div_start(self, html: str) -> list[BeautifulSoup]:
        """첫번째 요소 추출 시작점"""
        soup = BeautifulSoup(html, "lxml")
        return soup.find_all("div", {"class": "Gx5Zad xpd EtOod pkphOe"})
