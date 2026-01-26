from dataclasses import dataclass, field

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
        }
    )
