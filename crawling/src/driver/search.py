from typing import List, Set, Dict, Optional
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords


class EnhancedDeepAsyncWebCrawler(DeepAsyncWebCrawler):
    def __init__(
        self,
        start_url: str,
        max_pages: int,
        max_depth: int,
        keywords: List[str],
        relevance_threshold: float = 0.3,
    ):
        super().__init__(start_url, max_pages, max_depth)
        self.keywords = keywords
        self.relevance_threshold = relevance_threshold
        # NLTK 리소스 다운로드
        nltk.download("punkt")
        nltk.download("stopwords")
        self.stop_words = set(stopwords.words("english"))

    def is_relevant_url(self, url: str) -> bool:
        """URL이 키워드와 관련있는지 확인 (단순 패턴 매칭)"""
        url_lower = url.lower()
        return any(keyword.lower() in url_lower for keyword in self.keywords)

    def is_relevant_content(self, content: str, title: str) -> bool:
        """콘텐츠와 제목이 키워드와 관련있는지 확인 (TF-IDF 유사도 계산)"""
        if not content:
            return False

        # BeautifulSoup으로 텍스트 추출
        soup = BeautifulSoup(content, "lxml")
        text = soup.get_text(separator=" ", strip=True)

        # 키워드와 텍스트 전처리
        keywords_text = " ".join(self.keywords)

        # TF-IDF 벡터라이저 초기화 및 변환
        vectorizer = TfidfVectorizer(stop_words=self.stop_words)
        try:
            tfidf_matrix = vectorizer.fit_transform([keywords_text, text])
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return cosine_sim >= self.relevance_threshold
        except:
            # 벡터라이징 실패 시 단순 키워드 매칭으로 대체
            return any(keyword.lower() in text.lower() for keyword in self.keywords)

    async def crawl(self) -> None:
        while not self.url_queue.empty() and len(self.visited_urls) < self.max_pages:
            current_url, depth = await self.url_queue.get()

            if current_url in self.visited_urls or depth > self.max_depth:
                continue

            # URL 패턴 기반 필터링 (빠른 필터링)
            if (
                not self.is_relevant_url(current_url) and depth > 0
            ):  # 시작 URL은 항상 포함
                continue

            self.visited_urls.add(current_url)
            content = await AsyncRequestHTML(current_url).async_fetch_html(current_url)

            if content:
                # 콘텐츠 기반 필터링 (상세 필터링)
                soup = BeautifulSoup(content, "lxml")
                title = soup.title.text if soup.title else ""

                if (depth == 0) or self.is_relevant_content(
                    content, title
                ):  # 시작 URL은 항상 포함
                    if depth < self.max_depth:
                        new_links, url_format = self.parse_links(content, current_url)
                        self.results[current_url] = url_format
                        for link in new_links:
                            if link not in self.visited_urls:
                                await self.url_queue.put((link, depth + 1))
