from typing import TypedDict


class FunctionParameter(TypedDict):
    """FunctionParameter 클래스는 함수 매개변수를 정의하는 클래스"""

    type: str
    description: str


class FunctionCallingParameter(TypedDict):
    """FunctionCallingParameter 클래스는 함수 호출 매개변수를 정의하는 클래스"""

    type: str
    properties: dict[str, FunctionParameter]
    required: list[str]


class FunctionCallingMeta(TypedDict):
    """FunctionCallingMeta 클래스는 함수 호출 메타데이터를 정의하는 클래스"""

    name: str
    description: str
    parameters: FunctionCallingParameter


class LLMComponent(TypedDict):
    """LLMComponent 클래스는 LLM 메시지의 구성 요소"""

    role: str
    content: str
