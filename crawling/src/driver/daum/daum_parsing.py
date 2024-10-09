import re
from bs4 import BeautifulSoup


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
