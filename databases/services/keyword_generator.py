from pathlib import Path
from dataclasses import dataclass
import itertools
import yaml


@dataclass(frozen=True)
class BaseCountry:
    """
    국가별 키워드 및 템플릿 데이터를 관리하는 클래스.
    """

    name: str
    domain: str
    core_keywords: list[str]
    context_keywords: list[str]
    templates: list[str]

    def generate_search_queries(self) -> list[tuple[str, str]]:
        """
        키워드 조합 생성

        Returns:
            list[tuple[str, str]]: 키워드 조합 결과
        """
        return list(itertools.product(self.core_keywords, self.context_keywords))

    def apply_question_templates(self, queries: list[tuple[str, str]]) -> set[str]:
        """
        질문 템플릿 적용

        Args:
            queries (list[tuple[str, str]]): 키워드 조합 결과

        Returns:
            set[str]: 질문 템플릿 적용 결과
        """
        questions = []
        for template in self.templates:
            questions.extend(
                [
                    template.format(core, context)  # 위치 기반 포맷팅으로 수정
                    for core, context in queries
                ]
            )
        return set(questions)


def load_countries_from_yaml() -> dict[str, BaseCountry]:
    """
    YAML 파일에서 국가별 데이터를 로드하고 BaseCountry 객체 생성

    Returns:
        Dict[str, BaseCountry]: 국가 이름을 키로 하는 BaseCountry 객체 딕셔너리
    """
    keyword_yaml_path = Path(__file__).parent / "data/keyword.yaml"
    with open(keyword_yaml_path, "r", encoding="utf-8") as file:
        data: dict = yaml.safe_load(file)

    countries: dict[str, BaseCountry] = {
        country_code: BaseCountry(
            name=country_code,
            domain=country_data["domain"],
            core_keywords=country_data["core_keywords"],
            context_keywords=country_data["context_keywords"],
            templates=country_data["templates"],
        )
        for country_code, country_data in data["countries"].items()
    }
    return countries
