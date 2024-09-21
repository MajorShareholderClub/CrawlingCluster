"""
[AsyncLogger Class]

이 파일은 비동기 로깅을 지원하는 AsyncLogger 클래스를 정의한 타입 힌팅 파일입니다. 
AsyncLogger 클래스는 비동기 환경에서 효과적으로 로그를 처리하기 위해 설계되었으며, 
동기 및 비동기 방식으로 로그 메시지를 기록하는 기능을 제공합니다. 
이 파일은 주로 애플리케이션의 로깅 구성을 쉽게하고, 큐를 사용하여 효율적인 로그 처리를 가능하게 합니다.

----------------------------
| AsyncLogger Class        |
----------------------------
- __init__(self, log_file: str | None) -> None: 
    --->  클래스 초기화 함수입니다. 로그 파일의 경로를 설정합니다.
- _setup_queue_handler(self) -> QueueHandler: 
    --->  큐 기반 핸들러를 설정하여 로그 메시지를 비동기적으로 처리합니다.
- _setup_handlers(self) -> tuple[logging.StreamHandler, logging.FileHandler | None]: 
    --->  로그 메시지를 출력할 핸들러(스트림 또는 파일 핸들러)를 설정합니다.
- _setup_formatter(self) -> logging.Formatter: 
    --->  로그 메시지의 형식을 정의하는 포매터를 설정합니다.
- _setup_queue_listener(self) -> QueueListener: 
    --->  QueueListener를 설정하여, 큐에 들어온 로그 메시지를 수신하고 처리합니다.
- _setup_logger(self) -> logging.Logger: logging.Logger 
    --->  객체를 생성 및 설정하고 반환합니다.
- get_logger(self) -> logging.Logger: 설정된 로거 인스턴스를 반환합니다.
- async def log_message(self, level: int, message: str) -> None: 
    --->  비동기 환경에서 로그 메시지를 기록하는 함수입니다.
- def log_message_sync(self, level: int, message: str) -> None: 
    --->  동기 환경에서 로그 메시지를 기록하는 함수입니다.
- _log_message(self, level: int, message: str) -> None: 
    --->  실제 로그 메시지를 기록하는 내부 함수입니다.

----------------------------
| Logging Features         |
----------------------------
AsyncLogger 클래스는 다음과 같은 로깅 기능을 제공합니다:

1. 큐 기반 로그 처리: QueueHandler와 QueueListener를 이용해 비동기적인 로그 처리가 가능하며, 대규모 애플리케이션에서도 성능 저하 없이 로깅을 처리할 수 있습니다.
2. 비동기 및 동기 로깅: 비동기 및 동기 환경 모두에서 사용할 수 있도록 설계되었습니다.
3. 포맷 지정 가능: 로그 메시지의 포맷을 설정하여, 개발자가 원하는 형식대로 로그를 출력할 수 있습니다.
4. 파일 또는 콘솔 출력: 로그 메시지는 파일로 저장되거나 콘솔에 출력될 수 있으며, 핸들러를 설정하여 유연하게 관리할 수 있습니다.
"""

import logging
from logging.handlers import QueueHandler, QueueListener

# fmt: off
class AsyncLogger:
    def __init__(self, log_file: str | None) -> None: ...
    def _setup_queue_handler(self) -> QueueHandler: ...
    def _setup_handlers(self) -> tuple[logging.StreamHandler, logging.FileHandler | None]: ...
    def _setup_formatter(self) -> logging.Formatter: ...
    def _setup_queue_listener(self) -> QueueListener: ...
    def _setup_logger(self) -> logging.Logger: ...
    def get_logger(self) -> logging.Logger: ... 
    async def log_message(self, level: int, message: str) -> None: ... 
    def log_message_sync(self, level: int, message: str) -> None: ...
    def _log_message(self, level: int, message: str) -> None: ... 
