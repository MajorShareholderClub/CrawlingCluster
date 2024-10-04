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
            list[BeautifulSoup]: ["요소들"]
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

        def process_html(html: str) -> list[BeautifulSoup]:
            """무직위 난수에셔 div 관련 요소 뽑기"""
            soup = BeautifulSoup(html, "lxml")
            return soup.find_all("div", google_hveid)

        return process_html(html=html)


class InvestingNewsCrawlingParsingSelenium:

    def extract_content_url(self, li_tag: BeautifulSoup) -> str:
        """기사의 URL을 추출"""
        return li_tag.find("a", {"data-test": "article-title-link"})

    def extract_timestamp(self, li_tag: BeautifulSoup) -> str:
        """기사의 게시 날짜 (timestamp) 추출"""
        return li_tag.find("time", {"data-test": "article-publish-date"})

    def find_article_elements(self, html: str) -> list[BeautifulSoup]:
        """HTML에서 기사의 주요 요소들을 추출"""
        soup = BeautifulSoup(html, "lxml")
        return soup.find_all(
            "div", {"class": "news-analysis-v2_content__z0iLP w-full text-xs sm:flex-1"}
        )


class InvestingNewsCrawlingTargetNews:
    def extract_news_textdiv(self, div_tag: BeautifulSoup) -> str:
        """기사의 게시 날짜 (timestamp) 추출"""
        time_tag = div_tag.find("div", {"class": "textDiv"})
        return time_tag

    def find_article_elements(self, html: str) -> list[BeautifulSoup]:
        """HTML에서 기사의 주요 요소들을 추출"""
        soup = BeautifulSoup(html, "lxml")
        return soup.find_all("div", {"class": "articleItem"})


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


class DaumNewsCrawlingParsingDrive:
    """Daum 뉴스 크롤링 파싱 드라이버"""

    def ul_in_class(self, element: BeautifulSoup) -> list[BeautifulSoup]:
        """
        Args:
            <ul class="c-list-basic"> <---- 탐색 지점
                <li data-docid=26이후 무작위 난수>   <---- 리턴값
                <li data-docid=26이후 무작위 난수>
                <li data-docid=26이후 무작위 난수>
            </ul>
        Returns:
            list[BeautifulSoup]: 클래스가 'c-list-basic'인 'ul' 요소들의 리스트.
        """
        return element.find_all("ul", {"class": "c-list-basic"})

    def li_in_data_docid(self, element: BeautifulSoup) -> list[BeautifulSoup]:
        """
        Args:
            <li data-docid=26이후 무작위 난수>
        Returns:
            list[BeautifulSoup]: 정규식 패턴과 일치하는 'data-docid' 속성을 가진 'li' 요소들의 리스트.
        """
        match = re.compile(r"^26.*")
        return element.find_all("li", {"data-docid": match})

    def strong_in_class(self, element: BeautifulSoup) -> BeautifulSoup:
        """
        Args:
            <li data-docid=26이후 무작위 난수>
                <div class="item-title">
                    <strong class=tit-g clamp-g>  <----- 탐색 지점
                        <a href=URL></a> <----- 리턴값
                    </strong>
                </div>
            </li>

        Returns:
            BeautifulSoup : 클래스가 'tit-g clamp-g'인 'strong' 요소.
        """
        return element.find("strong", {"class": "tit-g clamp-g"})

    def span_in_class(self, element: BeautifulSoup) -> BeautifulSoup:
        """
        Args:
            <li data-docid=26이후 무작위 난수>
                <div class="item-contents">
                    <span class="gem-subinfo"> <---- 탐색 지점
                        <span class="txt_info"> </span> <--- 리턴값
                    </span>
                </div>
            </li>

        Returns:
            BeautifulSoup: 클래스가 'gem-subinfo'인 'span' 요소.
        """
        return element.find("span", {"class": "gem-subinfo"})

    def ul_class_c_list_basic(self, html: str, attrs: dict) -> list[BeautifulSoup]:
        """첫번째 요소 추출 시작점"""
        soup = BeautifulSoup(html, "lxml")
        return soup.find_all("ul", attrs)
