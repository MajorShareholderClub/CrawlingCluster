from __future__ import annotations

# Any 사용: 다양한 타입을 허용하는 동적 컨텍스트에 필요
import asyncio
import json
import logging
import os
import queue
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from functools import wraps
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from pathlib import Path
from typing import (
    Any,  # Any 사용: 다양한 타입을 허용하는 동적 컨텍스트에 필요
    Callable,
    TypeVar,
    ParamSpec,
)

# Type definitions
T = TypeVar("T")
P = ParamSpec("P")
LoggerFunc = Callable[[str], None]
LogLevel = int | str


class LogFormat(Enum):
    """로그 출력 형식"""

    TEXT = auto()
    JSON = auto()


@dataclass
class LogContext:
    """로그 컨텍스트 정보"""

    transaction_id: str = ""
    user_id: str = ""
    category: str = ""
    extra: dict[str, Any] = field(
        default_factory=dict
    )  # Any 사용: 로깅 시 문자열, 숫자, 객체 등 모든 타입의 부가 정보 저장 필요

    def update(
        self, **kwargs: Any
    ) -> None:  # Any 사용: 모든 타입의 컨텍스트 값 업데이트 허용
        """컨텍스트 정보 업데이트"""
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                self.extra[k] = v


class EnhancedLogger:
    """향상된 로깅 기능을 제공하는 로거 클래스"""

    def __init__(
        self,
        name: str,
        log_level: LogLevel = logging.INFO,
        log_format: LogFormat = LogFormat.TEXT,
        log_dir: str = "logs",
        file_name: str | None = None,
        max_bytes: int = 10_485_760,  # 10 MB
        backup_count: int = 5,
        console: bool = True,
        context: LogContext | None = None,
    ) -> None:
        """
        향상된 로거 초기화
        # Any 사용: 문자열(str), 숫자(int/float), 딕셔너리(dict), 리스트(list), 사용자 정의 객체 등
        # 모든 타입의 컨텍스트 데이터를 로깅할 수 있도록 지원
        # Any 사용: 파이썬 컨텍스트 관리자 프로토콜은 모든 예외 타입을 처리할 수 있어야 함
        Args:
            name: 로거 이름
            log_level: 로깅 레벨 (logging.INFO, logging.DEBUG 등)
            log_format: 로그 출력 형식 (TEXT 또는 JSON)
            log_dir: 로그 파일 디렉토리
            file_name: 로그 파일명 (None인 경우 name.log로 설정)
            max_bytes: 로그 파일 최대 크기
            backup_count: 백업 파일 수
            console: 콘솔 출력 여부
            context: 기본 로그 컨텍스트
        """
        self.name = name
        self.log_level = self._resolve_log_level(log_level)
        self.log_format = log_format
        self.log_dir = Path(log_dir)
        self.file_name = file_name or f"{name.lower().replace(' ', '_')}.log"
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.console = console
        self.context = context or LogContext()

        # 로그 설정
        self._setup_logger()

    def _resolve_log_level(self, level: LogLevel) -> int:
        """문자열 로그 레벨을 정수형으로 변환"""
        if isinstance(level, str):
            return getattr(logging, level.upper())
        return level

    def _setup_logger(self) -> None:
        """로거 설정"""
        # 로그 큐 생성
        self.log_queue: queue.Queue = queue.Queue()

        # 로거 인스턴스 생성
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.log_level)

        # 기존 핸들러 제거
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # 큐 핸들러 추가
        queue_handler = QueueHandler(self.log_queue)
        self.logger.addHandler(queue_handler)

        # 핸들러 설정
        handlers = self._setup_handlers()

        # 큐 리스너 설정 및 시작
        self.queue_listener = QueueListener(
            self.log_queue, *handlers, respect_handler_level=True
        )
        self.queue_listener.start()

        # 스레드 풀 설정
        self.executor = ThreadPoolExecutor(max_workers=2)

        # 비동기 지원을 위한 루프 설정
        try:
            self.loop = (
                asyncio.get_event_loop()
                if asyncio.get_event_loop_policy().get_event_loop().is_running()
                else None
            )
        except RuntimeError:
            # 스레드에서 실행 중일 때 새 이벤트 루프를 생성하지 않고 None으로 설정
            self.loop = None

    def _setup_handlers(self) -> list[logging.Handler]:
        """로그 핸들러 설정"""
        handlers = []

        # 포맷터 설정
        text_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] [%(module)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        class JsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_record = {
                    "timestamp": datetime.now().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "module": record.module,
                    "line": record.lineno,
                    "message": record.getMessage(),
                }

                # Extra 필드 추가
                if hasattr(record, "context"):
                    context_data = record.context
                    if isinstance(context_data, LogContext):
                        log_record.update(asdict(context_data))
                    elif isinstance(context_data, dict):
                        log_record.update(context_data)

                return json.dumps(log_record)

        json_formatter = JsonFormatter()

        # 콘솔 핸들러
        if self.console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(
                json_formatter if self.log_format == LogFormat.JSON else text_formatter
            )
            handlers.append(console_handler)

        # 파일 핸들러
        if self.file_name:
            # 로그 디렉토리 생성
            os.makedirs(self.log_dir, exist_ok=True)

            # 로그 파일 경로
            log_path = self.log_dir / self.file_name

            # 파일 핸들러 설정
            file_handler = RotatingFileHandler(
                filename=log_path,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(
                json_formatter if self.log_format == LogFormat.JSON else text_formatter
            )
            handlers.append(file_handler)

        return handlers

    def with_context(self, **kwargs: Any) -> EnhancedLogger:
        """컨텍스트가 추가된 로거 인스턴스 반환"""
        # Any 사용: 로그 컨텍스트에 추가될 수 있는 다양한 타입의 값 지원
        new_logger = EnhancedLogger(
            name=self.name,
            log_level=self.log_level,
            log_format=self.log_format,
            log_dir=str(self.log_dir),
            file_name=self.file_name,
            max_bytes=self.max_bytes,
            backup_count=self.backup_count,
            console=self.console,
            context=LogContext(**asdict(self.context)),
        )
        new_logger.context.update(**kwargs)
        return new_logger

    def _add_context_to_record(self, record: logging.LogRecord) -> None:
        """로그 레코드에 컨텍스트 추가"""
        setattr(record, "context", self.context)

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """로깅 수행"""
        # Any usage: Allow various data types as logging context (str, int, dict, etc.)
        # 컨텍스트 업데이트
        if kwargs:
            context_copy = LogContext(**asdict(self.context))
            context_copy.update(**kwargs)
        else:
            context_copy = self.context

        # 로거를 통한 로깅 (컨텍스트 추가)
        record = logging.LogRecord(
            name=self.name,
            level=level,
            pathname=__file__,
            lineno=0,
            msg=message,
            args=(),
            exc_info=None,
        )
        setattr(record, "context", context_copy)
        self.logger.handle(record)

    async def _log_async(self, level: int, message: str, **kwargs: Any) -> None:
        """비동기 로깅"""
        # Any usage: Support dynamic logging context with various data types
        if self.loop:
            await self.loop.run_in_executor(
                self.executor, self._log, level, message, **kwargs
            )
        else:
            # 루프가 없으면 동기식으로 처리
            self._log(level, message, **kwargs)

    # 로깅 메서드
    def debug(self, message: str, **kwargs: Any) -> None:
        """디버그 레벨 로깅"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """정보 레벨 로깅"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """경고 레벨 로깅"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """에러 레벨 로깅"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """심각한 에러 레벨 로깅"""
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """예외 로깅 (스택 트레이스 포함)"""
        exc_info = sys.exc_info()
        kwargs["exception"] = "".join(traceback.format_exception(*exc_info))
        self._log(logging.ERROR, message, **kwargs)

    # 비동기 로깅 메서드
    async def debug_async(self, message: str, **kwargs: Any) -> None:
        """비동기 디버그 레벨 로깅"""
        await self._log_async(logging.DEBUG, message, **kwargs)

    async def info_async(self, message: str, **kwargs: Any) -> None:
        """비동기 정보 레벨 로깅"""
        await self._log_async(logging.INFO, message, **kwargs)

    async def warning_async(self, message: str, **kwargs: Any) -> None:
        """비동기 경고 레벨 로깅"""
        await self._log_async(logging.WARNING, message, **kwargs)

    async def error_async(self, message: str, **kwargs: Any) -> None:
        """비동기 에러 레벨 로깅"""
        await self._log_async(logging.ERROR, message, **kwargs)

    async def critical_async(self, message: str, **kwargs: Any) -> None:
        """비동기 심각한 에러 레벨 로깅"""
        await self._log_async(logging.CRITICAL, message, **kwargs)

    async def exception_async(self, message: str, **kwargs: Any) -> None:
        """비동기 예외 로깅 (스택 트레이스 포함)"""
        exc_info = sys.exc_info()
        kwargs["exception"] = "".join(traceback.format_exception(*exc_info))
        await self._log_async(logging.ERROR, message, **kwargs)

    def __enter__(self) -> EnhancedLogger:
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """컨텍스트 매니저 종료"""
        self.close()

    async def __aenter__(self) -> EnhancedLogger:
        """비동기 컨텍스트 매니저 진입"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """비동기 컨텍스트 매니저 종료"""
        self.close()

    def close(self) -> None:
        """리소스 정리"""
        if hasattr(self, "queue_listener") and self.queue_listener:
            self.queue_listener.stop()

        if hasattr(self, "executor") and self.executor:
            self.executor.shutdown(wait=False)

    def __del__(self) -> None:
        """소멸자"""
        self.close()


# 데코레이터
def log_function(logger: EnhancedLogger) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """함수 호출 로깅 데코레이터"""

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            func_name = func.__name__
            logger.debug(f"함수 시작: {func_name}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"함수 종료: {func_name}")
                return result
            except Exception as e:
                logger.exception(
                    f"함수 실패: {func_name}", error=str(e)
                )  # Any 사용: error 파라미터는 다양한 예외 타입의 문자열 표현을 허용
                raise

        return wrapper

    return decorator


def log_async_function(
    logger: EnhancedLogger,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """비동기 함수 호출 로깅 데코레이터"""

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            func_name = func.__name__
            await logger.debug_async(f"비동기 함수 시작: {func_name}")
            try:
                result = await func(*args, **kwargs)
                await logger.debug_async(f"비동기 함수 종료: {func_name}")
                return result
            except Exception as e:
                await logger.exception_async(
                    f"비동기 함수 실패: {func_name}",
                    error=str(
                        e
                    ),  # Any 사용: error 파라미터는 다양한 예외 타입의 문자열 표현을 허용
                )
                raise

        return wrapper

    return decorator


# 유틸리티 함수
def get_logger(
    name: str,
    level: LogLevel = logging.INFO,
    log_format: LogFormat = LogFormat.TEXT,
    file_prefix: str | None = None,
    console: bool = True,
) -> EnhancedLogger:
    """편리한 로거 생성 함수"""
    return EnhancedLogger(
        name=name,
        log_level=level,
        log_format=log_format,
        file_name=f"{file_prefix or name.lower().replace(' ', '_')}.log",
        console=console,
    )
