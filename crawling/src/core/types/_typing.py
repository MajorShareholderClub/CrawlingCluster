from common.types._typing_crawling import *  # noqa: F401,F403

# This module now re-exports all crawling-related typing aliases from the shared
# `common` package so that existing imports such as
#     from crawling.src.core.types import UrlDictCollect
# continue to work without changes, while ensuring a **single source of truth**
# for these type definitions across the entire code-base.

__all__ = [
    # Re-export every symbol explicitly defined in the shared typing module.
    *(__dict__ for __dict__ in globals().keys() if not __dict__.startswith("__")),
]
