import json
from typing import Any


def parse_tool_output(raw_json: str | dict[str, Any], max_len: int = 50) -> str:
    """
    장황한 툴 출력(예: weather API)을 파싱해 핵심 정보만 남긴 짧은 문자열로 압축합니다.

    요구사항:
    - 스키마로 정의된 필드만 사용 (temperature_c 필수, timestamp/location 선택)
    - 결과 문자열 길이는 max_len 미만
    - 입력은 JSON 문자열 또는 dict

    입력 예시 포맷(스키마):

    - Dict form:
      {
        "temperature_c": 25,              # required (int/float or numeric string)
        "timestamp": "2025-12-16T09:15:00Z",  # optional
        "location": "Seoul, KR",          # optional
        "temperature_f": 77               # optional fallback if temperature_c missing
      }

    - JSON string form:
      '{"temperature_c": 25, "location": "Seoul, KR", "timestamp": "2025-12-16T09:15:00Z"}'
    """

    data: dict[str, Any]
    if isinstance(raw_json, str):
        try:
            data = json.loads(raw_json)
        except Exception:
            return _cap("temperature missing", max_len=max_len)
    elif isinstance(raw_json, dict):
        data = raw_json
    else:
        return _cap("temperature missing", max_len=max_len)

    temperature_c = _coerce_number(data.get("temperature_c"))
    if temperature_c is None:
        # Optional fallback: convert F -> C if provided
        temperature_f = _coerce_number(data.get("temperature_f"))
        if temperature_f is not None:
            temperature_c = (temperature_f - 32) * 5 / 9

    if temperature_c is None:
        return _cap("temperature missing", max_len=max_len)

    location = data.get("location")
    timestamp = data.get("timestamp")

    parts: list[str] = [f"Temperature: {_format_temp_c(temperature_c)}"]
    if location:
        parts.append(f"@ {str(location)}")
    if timestamp:
        parts.append(f"({str(timestamp)})")

    return _cap(" ".join(parts), max_len=max_len)


def _coerce_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except Exception:
            return None
    return None


def _format_temp_c(value: float) -> str:
    # Prefer integer-like formatting when possible
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value))}C"
    return f"{value:.1f}C"


def _cap(text: str, *, max_len: int) -> str:
    # Requirement: result length must be strictly < max_len
    if max_len <= 1:
        return ""
    if len(text) < max_len:
        return text
    effective_max = max_len - 1
    if effective_max <= 3:
        return text[:effective_max]
    return text[: effective_max - 3] + "..."


