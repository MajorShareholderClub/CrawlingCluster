from bs4 import BeautifulSoup


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
