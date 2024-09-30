import re

from bs4 import BeautifulSoup

from crawling.src.utils.parsing_util import parse_time_ago


class GoogleNewsCrawlingParsingDrive:
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


class BingNewsCrawlingParsingDrive:
    """
    bing News Parsing Drive

    """

    def __init__(self, target: str, count: int) -> None:
        """크롤링 초기화
        Args:
            target (str): 긁어올 타겟
            count (int): 횟수
        """
        super().__init__(target, count)

    def div_in_class(self, element: BeautifulSoup, target: str) -> list[BeautifulSoup]:
        """bing page 요소 두번째 접근 단계

        Args:
            element (BeautifulSoup)
        Returns:
            list[BeautifulSoup]: ["요소들", ~~]
        """
        return element.find_all("div", {"class": target})

    def detection_element(
        self, html_source: str, *element: str
    ) -> tuple[BeautifulSoup]:
        """Bing HTML element 요소 추출하기

        Args:
            html_source (str) : HTML
            element (tuple[BeautifulSoup]) : HTML에 div new를 담기고 있는 후보들
                - ex)
                \n
                <div class="algocore">
                    <div class="news-card newsitem cardcommon">
                        뉴스
                    </div>
                </div>

                <div class="nwscnt">
                    <div class="newscard vr">
                        뉴스
                    </div>
                </div<

        Return: (tuple[str, str])
            - 파악된 요소들
        """
        pattern = r'class="([^"]+)"'
        class_values: set[BeautifulSoup] = set(
            element for element in re.findall(pattern, html_source)
        )
        data: tuple[str, ...] = tuple(elem for elem in element if elem in class_values)
        return data

    def news_create_time_from_div(self, element: BeautifulSoup) -> str:
        """날짜 추출
        >>> <div class="t_t">
                <div class="source set_top">
                    <span aria-label="55 minutes ago" tabindex="0">
                        55m (이부분)
                    </span>
                </div>
            </div>

        Return: (str)
            - 3d, 3h~~
        """
        return element.find("div", {"class": "t_t"}).find("span", {"tabindex": "0"})

    def div_class_algocore(self, html: str, attrs: dict) -> list[BeautifulSoup]:
        """첫번째 요소 추출 시작점"""
        soup = BeautifulSoup(html, "lxml")
        return soup.find_all("div", attrs)


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
