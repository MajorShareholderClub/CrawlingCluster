from __future__ import annotations

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

import openai
from dotenv import load_dotenv
from common.types._typing_llm import (
    FunctionCallingMeta,
    FunctionCallingParameter,
    FunctionParameter,
    LLMComponent,
)


@dataclass
class FunctionCallingMetaBuilder:
    """LLM 함수 호출 메타데이터를 생성하는 빌더 클래스입니다.

    Attributes:
        name (str): 함수의 이름
        description (str): 함수의 설명
        parameters (dict): 함수의 파라미터 정보를 담은 딕셔너리
        required (list): 필수로 입력해야 하는 파라미터 목록

    Examples:
        1. 생성자를 통한 초기화:
            >>> meta_builder = FunctionCallingMetaBuilder(
            ...     name="extract_keywords_from_article",
            ...     description="뉴스 기사에서 키워드를 추출합니다.",
            ...     parameters={
            ...         "article_text": FunctionParameter(
            ...             type="string",
            ...             description="뉴스 기사 본문"
            ...         ),
            ...         "num_keywords": FunctionParameter(
            ...             type="integer",
            ...             description="추출할 키워드의 수"
            ...         ),
            ...     },
            ...     required=["article_text", "num_keywords"],
            ... )

        2. 메서드 체이닝을 통한 파라미터 추가:
            >>> meta_builder.add_function_parameter(
            ...     name="article_text",
            ...     parameter=FunctionParameter(
            ...         type="string",
            ...         description="뉴스 기사 본문"
            ...     )
            ... ).add_function_parameter(
            ...     name="num_keywords",
            ...     parameter=FunctionParameter(
            ...         type="integer",
            ...         description="추출할 키워드의 수"
            ...     )
            ... ).add_function_parameter(
            ...     name="signature_keywords",
            ...     parameter=FunctionParameter(
            ...         type="list",
            ...         description="시그니처 키워드 목록"
            ...     )
            ... ).build()
    """

    name: str
    description: str
    parameters: dict[str, FunctionParameter] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)

    # fmt: off
    def add_function_parameter(self, name: str, parameter: FunctionParameter) -> FunctionCallingMetaBuilder:
        """파라미터 추가"""
        self.parameters[name] = parameter
        return self

    def build(self) -> list[FunctionCallingMeta]:
        """함수 메타데이터 생성"""
        return [
            FunctionCallingMeta(
                name=self.name,
                description=self.description,
                parameters=FunctionCallingParameter(
                    type="object",
                    properties=self.parameters,
                    required=self.required,
                ),
            )
        ]


class LLMKeywordExtractor:
    """LLMKeywordExtractor 클래스는 LLM을 사용하여 키워드를 추출하는 클래스"""

    def __init__(self, meta: FunctionCallingMetaBuilder | None = None) -> None:
        """LLMKeywordExtractor 클래스의 생성자입니다. API 키를 로드

        Args:
            meta (FunctionCallingMetaBuilder): 함수 호출 메타데이터
        """
        self._load_api_key()
        self.meta = meta

    def _load_api_key(self) -> None:
        """api_key load"""
        key_path = Path(__file__).parent.parent / "config/cy/.env"
        load_dotenv(key_path)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        openai.api_key = api_key

    async def async_calling_llm_gpt(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 1500,
        force_function_call: bool = False,
    ) -> str:
        """gpt 비동기 호출

        Args:
            prompt: 프롬프트 텍스트
            model: 사용할 모델
            max_tokens: 최대 토큰 수
            force_function_call: 함수 호출 강제

        Returns:
            LLM 응답 텍스트
        """
        try:
            # OpenAI API의 비동기 클라이언트 생성
            aclient = openai.AsyncOpenAI(api_key=openai.api_key)

            # 함수 호출 파라미터 설정
            functions_param = self.meta.build() if self.meta else None
            function_call_param = (
                {"name": self.meta.name} if self.meta and force_function_call else None
            )

            response = await aclient.chat.completions.create(
                model=model,
                messages=[
                    LLMComponent(
                        role="system",
                        content="You are an assistant that summarizes data.",
                    ),
                    LLMComponent(
                        role="user",
                        content=prompt,
                    ),
                ],
                max_tokens=max_tokens,
                functions=functions_param,
                function_call=function_call_param,
            )

            # 함수 호출 응답 처리
            if (
                hasattr(response.choices[0].message, "function_call")
                and response.choices[0].message.function_call
            ):
                function_name = response.choices[0].message.function_call.name
                function_args = json.loads(
                    response.choices[0].message.function_call.arguments
                )
                return json.dumps(
                    {"function": function_name, "parameters": function_args}
                )
            else:
                # 일반 응답 처리
                return response.choices[0].message.content.strip()
        except Exception as e:
            # 오류 발생 시 처리
            error_msg = f"LLM API 호출 중 오류 발생: {str(e)}"
            return json.dumps({"error": error_msg})

    def _get_keywords_prompt(self, article_text: str) -> str:
        """키워드 추출 프롬프트 생성"""
        return f"""
        다음은 뉴스 기사 본문입니다:
        "{article_text}"

        이 본문을 다음 기준으로 수행해주세요:
        1. 이 기사에서 가장 중요한 10개의 키워드를 추출하세요.
        2. 키워드는 문맥을 반영하여 의미 있는 단어 또는 구문으로 구성되어야 합니다.
        """

    def _get_evaluation_prompt(
        self, text: str, source: str, date: str, signature_keywords: list[str]
    ) -> str:
        """기사 평가 프롬프트 생성"""
        return f"""
        다음은 뉴스 기사 문서입니다:
        출처: {source}
        날짜: {date}
        본문: "{text}"

        시그니처 키워드 목록: {', '.join(signature_keywords)}

        이 문서를 다음 기준으로 평가해주세요:
        1. 시그니처 키워드의 중요도 (0~5점)
        2. 문서가 최신 AI 트렌드와 얼마나 관련이 있는지 (0~5점)
        3. 출처의 신뢰도 점수 (0~5점)
        4. 종합 점수 (0~100점): 위 기준을 종합해서 부여

        출력 형식 (JSON):
        {{
            "키워드 중요도": [점수],
            "AI 트렌드 관련도": [점수],
            "출처 신뢰도": [점수],
            "종합 점수": [점수]
        }}
        """

    async def advanced_analysis(
        self, article_text: str, source: str = "Unknown", date: str = None
    ) -> dict:
        """Function Calling을 활용하면서 기존 프롬프트 구조를 유지하는 분석 메서드

        Args:
            article_text: 분석할 기사 텍스트
            source: 출처 정보
            date: 기사 날짜

        Returns:
            분석 결과
        """
        # 날짜 기본값 설정
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        # 1. 기사 분석을 위한 Function Calling 메타데이터 설정
        article_analysis_meta = FunctionCallingMetaBuilder(
            name="analyze_article",
            description="뉴스 기사를 분석하여 키워드와 평가를 수행합니다.",
        )

        # 파라미터 설정 (메서드 체이닝 활용)
        article_analysis_meta.add_function_parameter(
            name="keywords",
            parameter=FunctionParameter(
                type="array", description="추출된 중요 키워드 목록"
            ),
        ).add_function_parameter(
            name="evaluation",
            parameter=FunctionParameter(type="object", description="기사 품질 평가"),
        ).add_function_parameter(
            name="summary",
            parameter=FunctionParameter(
                type="string", description="기사 요약 (3문장 이내)"
            ),
        ).build()

        # 필수 파라미터 설정
        article_analysis_meta.required = ["keywords", "evaluation"]

        # 원래 메타데이터 저장
        original_meta = self.meta
        self.meta = article_analysis_meta

        try:
            # 2. 기존 프롬프트 활용하여 통합 프롬프트 작성
            keywords_prompt = self._get_keywords_prompt(article_text)

            # 시그니처 키워드 추출
            # 이 부분은 현재 force_function_call이 없기 때문에 일단 너무 복잡해져 있음
            # 나중에 필요하면 구현할 수 있음

            # 평가 프롬프트 생성 (시그니처 키워드 없이)
            evaluation_prompt = self._get_evaluation_prompt(
                article_text, source, date, []
            )

            # 3. 통합 프롬프트 작성
            prompt = f"""
            다음 기사를 분석해주세요:
            
            출처: {source}
            날짜: {date}
            본문: "{article_text}"
            
            아래 작업을 수행해주세요:
            
            1. 키워드 추출:
            {keywords_prompt}
            
            2. 품질 평가:
            {evaluation_prompt}
            
            3. 기사 요약:
            이 기사를 3문장 이내로 요약해주세요.
            
            
            analyze_article 함수를 호출하여 결과를 반환해주세요.
            """

            # 4. LLM 호출 (force_function_call=True 사용)
            result = await self.async_calling_llm_gpt(
                prompt=prompt, max_tokens=2000, force_function_call=True
            )

            # 5. 결과 처리
            try:
                # JSON 형식으로 파싱
                json_result = json.loads(result)

                # Function Calling 응답인지 확인
                if (
                    isinstance(json_result, dict)
                    and "function" in json_result
                    and json_result["function"] == "analyze_article"
                ):
                    # Function Calling 성공
                    parameters = json_result.get("parameters", {})
                    return {
                        "keywords": parameters.get("keywords", []),
                        "evaluation": parameters.get("evaluation", {}),
                        "summary": parameters.get("summary", ""),
                        "entities": parameters.get("entities", []),
                    }
                else:
                    # 일반 JSON 응답
                    return json_result

            except json.JSONDecodeError:
                # 평가 결과 파싱 실패
                return {
                    "error": "응답 처리 실패",
                    "raw_result": result,
                }

        finally:
            # 원래 메타데이터 복원
            self.meta = original_meta
