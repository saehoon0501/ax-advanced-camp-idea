from __future__ import annotations

import re
from typing import Any, Iterable

from langchain_core.tools import BaseTool, tool


@tool
def math_tool(expression: str) -> str:
    """간단한 사칙연산 표현식(예: '25 * 50')을 계산해 결과 문자열을 반환합니다."""
    # NOTE: 실습용으로 의도적으로 단순화했습니다. 프로덕션에서는 eval 사용 금지.
    safe = re.fullmatch(r"[0-9+\-*/(). %]+", expression.strip())
    if not safe:
        return "error: invalid expression"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception:
        return "error: invalid expression"


@tool
def email_tool(to: str, subject: str, body: str) -> str:
    """이메일 발송 요청(payload)을 생성하는 데모 툴입니다. 확인용 문자열을 반환합니다."""
    return f"email queued to={to!r} subject={subject!r}"


def select_relevant_tools(query: str, all_tools: list[BaseTool | dict[str, Any]]) -> list[BaseTool | dict[str, Any]]:
    """
    사용자 질의를 기반으로 **노출할 툴 목록(all_tools의 부분집합)**을 선택합니다.

    요구사항:
    - 계산/수식 질의 → MathTool(`math_tool`)만 반환
    - 이메일 질의 → EmailTool(`email_tool`)만 반환

    정책:
    - 복합 질의(예: "계산해서 이메일로 보내줘")는 `math_tool` + `email_tool`을 함께 반환(최대 2개)
    - 모호한 질의는 빈 리스트(`[]`) 반환
    """

    q = (query or "").lower()
    wants_math = _looks_like_math(q)
    wants_email = _looks_like_email(q)

    wanted_names: list[str] = []
    if wants_math:
        wanted_names.append("math_tool")
    if wants_email:
        wanted_names.append("email_tool")

    if not wanted_names:
        return []

    selected: list[BaseTool | dict[str, Any]] = []
    for name in wanted_names:
        tool_obj = _find_tool_by_name(all_tools, name)
        if tool_obj is not None:
            selected.append(tool_obj)

    return selected


def _looks_like_math(q: str) -> bool:
    if any(k in q for k in ("calculate", "calc", "compute", "math")):
        return True
    # Heuristic: contains at least one arithmetic operator and a digit
    if any(op in q for op in ("+", "-", "*", "/", "%")) and any(ch.isdigit() for ch in q):
        return True
    return False


def _looks_like_email(q: str) -> bool:
    if any(k in q for k in ("send email", "email", "mail", "inbox", "gmail", "outlook")):
        return True
    if "send" in q and "email" in q:
        return True
    return False


def _find_tool_by_name(tools: Iterable[BaseTool | dict[str, Any]], name: str) -> BaseTool | dict[str, Any] | None:
    for t in tools:
        if isinstance(t, dict):
            if t.get("name") == name:
                return t
        else:
            if getattr(t, "name", None) == name:
                return t
    return None


