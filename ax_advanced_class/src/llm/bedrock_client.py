from __future__ import annotations
from typing import Dict, Optional, Any, TypedDict
from langchain_aws.chat_models import ChatBedrock
import functools

from ax_advanced_class.src.config.bedrock_config import LLMConfig, DEFAULT_BOTO_CONFIG


class LLMOverride(TypedDict, total=False):
    model_id: str
    region_name: str
    streaming: bool
    model_kwargs: Dict[str, Any]


class BedrockClient:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()

    def _build_core(self, **overrides: LLMOverride) -> ChatBedrock:
        config = self._effective_config(**overrides)
        return ChatBedrock(
            model_id=config.model_id,
            region_name=config.region_name,
            streaming=config.streaming,
            model_kwargs=config.model_kwargs,
            config=DEFAULT_BOTO_CONFIG,
        )

    @functools.lru_cache(maxsize=8)
    def get_cached_core(self, model_id: str = None) -> ChatBedrock:
        """
        tool이 없는 노드 전용, 바인딩 금지
        """
        return self._build_core(model_id=model_id or self.config.model_id)

    def get_core(self, **overrides) -> ChatBedrock:
        core = self._build_core(**overrides)
        return core

    def _effective_config(self, **overrides: LLMOverride) -> LLMConfig:
        model_kwargs = dict(self.config.model_kwargs)
        model_kwargs.update(overrides.pop("model_kwargs", {}))
        return LLMConfig(
            model_id=overrides.pop("model_id", self.config.model_id),
            region_name=overrides.pop("region_name", self.config.region_name),
            streaming=overrides.pop("streaming", self.config.streaming),
            model_kwargs=model_kwargs,
        )
