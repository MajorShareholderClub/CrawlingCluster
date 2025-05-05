from typing import Optional, Any
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
import asyncio

from crawling.src.driver.deep.base_crawler import DeepAsyncWebCrawler
from crawling.src.utils.acquisition import AsyncRequestHTML
from crawling.src.core.types import UrlDictCollect


class RelevantAsyncWebCrawler(DeepAsyncWebCrawler):
    """관련성 필터링을 적용한 비동기 웹 크롤러
    
    키워드와 콘텐츠 유사성을 기반으로 관련된 기사나 웹페이지만 수집하는 크롤러입니다.
    TF-IDF와 코사인 유사도를 활용하여 콘텐츠의 관련성을 대략적으로 판단합니다.
    
    Attributes:
        keywords (list[str]): 관련성을 판단하는 데 사용되는 키워드 목록
        relevance_threshold (float): 콘텐츠를 관련있다고 판단하는 관련성 임계값 (0-1)
        stop_words (set): 분석에서 제외할 어휘(stopwords)
    """

    def __init__(
        self,
        start_url: str,
        max_pages: int,
        max_depth: int,
        keywords: list[str],
        relevance_threshold: float = 0.3,
        language: str = "english"
    ) -> None:
        """생성자
        
        Args:
            start_url: 크롤링을 시작할 URL
            max_pages: 최대 크롤링할 페이지 수
            max_depth: 최대 탐색 깊이
            keywords: 관련성을 판단하는 데 사용될 키워드 목록
            relevance_threshold: 관련성 판단 임계값 (0-1 사이, 기본값: 0.3)
            language: NLTK 어휘 제거를 위한 언어 (기본값: 'english')
        """
        super().__init__(start_url, max_pages, max_depth)
        self.keywords = keywords
        self.relevance_threshold = relevance_threshold
        
        # NLTK 리소스 다운로드 (초기화 시 한 번만 실행)
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download("punkt", quiet=True)
        
        try:
            nltk.data.find(f'corpora/stopwords/{language}')
        except LookupError:
            nltk.download("stopwords", quiet=True)
        
        # 언어에 따른 정지어(stopwords) 설정
        self.stop_words = set(stopwords.words(language))
        
        # 한국어 키워드인 경우 해당 언어에 맞는 처리 추가 가능
        self.is_korean = language == "korean"

    def is_relevant_url(self, url: str) -> bool:
        """간단한 URL 패턴 기반 필터링
        
        Args:
            url: 관련성을 확인할 URL
            
        Returns:
            bool: URL이 키워드와 관련있는지 여부
        """
        url_lower = url.lower()
        # URL에 키워드가 포함되어 있는지 확인
        return any(keyword.lower() in url_lower for keyword in self.keywords)

    def is_relevant_content(self, content: str, title: str) -> bool:
        """콘텐츠 기반 관련성 필터링 (TF-IDF 유사도 기반)
        
        Args:
            content: HTML 콘텐츠
            title: 페이지 제목
            
        Returns:
            bool: 콘텐츠가 키워드와 관련있는지 여부
        """
        if not content:
            return False

        # BeautifulSoup으로 텍스트 추출 (태그 제거)
        soup = BeautifulSoup(content, "lxml")
        text = soup.get_text(separator=" ", strip=True)
        
        # 제목을 텍스트에 추가하여 가중치 부여
        if title:
            text = f"{title} {title} {text}"  # 제목 중복하여 가중치 부여

        # 키워드 문자열 구성
        keywords_text = " ".join(self.keywords)

        # TF-IDF 벡터라이저 초기화 및 변환
        vectorizer = TfidfVectorizer(stop_words=self.stop_words)
        try:
            # 키워드와 콘텐츠를 TF-IDF 벡터로 변환
            tfidf_matrix = vectorizer.fit_transform([keywords_text, text])
            # 코사인 유사도 계산
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return cosine_sim >= self.relevance_threshold
        except Exception as e:
            # 예외 발생 시 단순 키워드 매칭으로 대체
            print(f"TF-IDF 유사도 계산 오류: {e}")
            return any(keyword.lower() in text.lower() for keyword in self.keywords)

    async def crawl(self) -> None:
        """관련성 필터링을 적용한 BFS 크롤링
        
        기본 BFS 알고리즘에 URL 및 콘텐츠 기반 관련성 필터링을 추가한 버전입니다.
        """
        while not self.url_queue.empty() and len(self.visited_urls) < self.max_pages:
            current_url, depth = await self.url_queue.get()

            if current_url in self.visited_urls or depth > self.max_depth:
                continue

            # URL 패턴 기반 필터링 (빠른 필터링)
            # 깊이가 0인 시작 URL은 필터링하지 않고 포함
            if not self.is_relevant_url(current_url) and depth > 0:
                continue

            self.visited_urls.add(current_url)
            content = await AsyncRequestHTML(current_url).async_fetch_html(current_url)

            if content:
                # 콘텐츠 기반 필터링 (상세 필터링)
                soup = BeautifulSoup(content, "lxml")
                title = soup.title.text if soup.title else ""
                
                # 시작 URL 혹은 관련성 있는 콘텐츠인 경우에만 처리
                if (depth == 0) or self.is_relevant_content(content, title):
                    if depth < self.max_depth:
                        new_links, url_format = self.parse_links(content, current_url)
                        self.results[current_url] = url_format
                        
                        # 같은 도메인을 우선순위로 크롤링하도록 정렬
                        from urllib.parse import urlparse
                        base_domain = urlparse(current_url).netloc
                        
                        # 같은 도메인 링크를 우선적으로 추가
                        sorted_links = sorted(
                            new_links, 
                            key=lambda link: 0 if urlparse(link).netloc == base_domain else 1
                        )
                        
                        for link in sorted_links:
                            if link not in self.visited_urls:
                                await self.url_queue.put((link, depth + 1))
