import time
import logging
from typing import Any, Callable

# ub85cuae45 uc124uc815
logger = logging.getLogger("session.retry")


class RetryStrategy:
    """uc7acuc2dcub3c4 uc804ub7b5uc744 ub2f4ub2f9ud558ub294 ud074ub798uc2a4"""

    def __init__(
        self, max_retries: int = 3, initial_delay: int = 2, backoff_factor: float = 1.5
    ):
        """
        uc7acuc2dcub3c4 uc804ub7b5 ucd08uae30ud654

        Args:
            max_retries: ucd5cub300 uc7acuc2dcub3c4 ud69fuc218
            initial_delay: ucd08uae30 ub300uae30 uc2dcuac04(ucd08)
            backoff_factor: uc9c0uc218 ubc31uc624ud504 uacc4uc218
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        uc9c0uc218 ubc31uc624ud504ub97c uc801uc6a9ud55c uc7acuc2dcub3c4 uba54ucee4ub2c8uc998uc73cub85c ud568uc218 uc2e4ud589
        """
        retries = 0
        delay = self.initial_delay
        last_error = None

        while retries <= self.max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                retries += 1

                if retries <= self.max_retries:
                    logger.warning(
                        f"uc2e4ud589 uc2e4ud328 ({retries}/{self.max_retries}): {e}. {delay}ucd08 ud6c4 uc7acuc2dcub3c4ud569ub2c8ub2e4."
                    )
                    time.sleep(delay)
                    delay *= self.backoff_factor
                else:
                    logger.error(f"ucd5cub300 uc7acuc2dcub3c4 ud69fuc218 ucd08uacfc. uc2e4ud589 uc2e4ud328: {e}")
                    break

        if last_error:
            raise last_error

        return None
