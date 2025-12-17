from __future__ import annotations
from typing import Dict, Optional, Any, TypedDict
from langchain_aws.chat_models import ChatBedrock
from dataclasses import dataclass, field
import functools


# TODO: 모델 변경 시 수정 필요
DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"
DEFAULT_REGION = "us-east-1"


@dataclass(frozen=True)
class LLMConfig:
    model_id: str = DEFAULT_MODEL_ID
    region_name: str = DEFAULT_REGION
    streaming: bool = True
    model_kwargs: Dict[str, Any] = field(
        default_factory=lambda: {
            "max_tokens": 8192,
            "temperature": 0.8,
            "top_p": 0.9,
            "anthropic_version": "bedrock-2023-05-31",
            # "timeout": 60, # 필요 시
        }
    )


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
