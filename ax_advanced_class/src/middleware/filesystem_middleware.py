"""Middleware for providing filesystem tools to an agent.

이 파일에는 3개의 TODO가 있습니다:
  TODO 1: _get_edit_file_description() - edit_file 도구의 설명 작성
  TODO 2: wrap_model_call()            - 시스템 프롬프트 주입 + 도구 필터링
  TODO 3: wrap_tool_call()             - 큰 Tool 결과를 파일로 교체 (eviction)

모든 production 코드는 _internals/filesystem_helpers.py의 FilesystemMiddlewareBase에
구현되어 있습니다. 여기서는 3개의 메서드만 override하면 됩니다.
"""

from collections.abc import Callable

from langchain.agents.middleware.types import (
    ContextT,
    ModelRequest,
    ModelResponse,
    ResponseT,
)
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from ax_advanced_class.src.middleware._internals.filesystem_helpers import (
    EDIT_FILE_TOOL_DESCRIPTION,
    EXECUTION_SYSTEM_PROMPT,
    FILESYSTEM_SYSTEM_PROMPT,
    TOOLS_EXCLUDED_FROM_EVICTION,
    FilesystemMiddlewareBase,
    _supports_execution,
    append_to_system_message,
)

# Re-export public types so existing imports keep working
from ax_advanced_class.src.middleware._internals.filesystem_helpers import (  # noqa: F401
    BACKEND_TYPES,
    FileData,
    FilesystemState,
    _file_data_reducer,
)


class FilesystemMiddleware(FilesystemMiddlewareBase):
    """Filesystem middleware with 3 TODO exercises.

    Base class(``FilesystemMiddlewareBase``)가 ls, read_file, write_file, glob,
    grep, execute 도구를 생성합니다. 아래 3개 메서드를 구현하세요.
    """

    # ------------------------------------------------------------------
    # TODO 1: edit_file 도구의 설명을 작성하세요
    # ------------------------------------------------------------------
    def _get_edit_file_description(self) -> str:
        # TODO 1: edit_file 도구의 설명(description)을 반환하세요
        #
        # LLM은 도구의 코드가 아니라 description을 읽고 사용 여부를 판단합니다.
        # 좋은 Tool 설명의 체크리스트:
        #   - 목적(Purpose): 이 도구가 무엇을 하는지
        #   - 사용 조건(When to use): 먼저 Read 해야 함
        #   - 실패 케이스(Failure): old_string이 고유하지 않으면 실패
        #   - 해결법(Resolution): 더 많은 컨텍스트 포함 or replace_all
        #
        # 힌트: EDIT_FILE_TOOL_DESCRIPTION 상수를 참고하거나 직접 작성하세요
        #   self._custom_tool_descriptions.get("edit_file")이 있으면 그것을 우선 사용
        #
        # StructuredTool 생성은 부모 클래스가 자동으로 처리합니다.
        # 여기서는 설명 문자열만 반환하면 됩니다.
        #
        return ""

    # ------------------------------------------------------------------
    # TODO 2: 시스템 프롬프트 주입 + 도구 필터링
    # ------------------------------------------------------------------
    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT]:
        # TODO 2: 시스템 프롬프트를 주입하고 도구를 필터링하세요
        #
        # Step 1: execute 도구가 있는지 확인
        # Step 2: backend가 execution 미지원이면 execute를 tools에서 제거
        # Step 3: 시스템 프롬프트 구성
        #   self._custom_system_prompt이 있으면 그것을 사용
        #   없으면 FILESYSTEM_SYSTEM_PROMPT + (execute 가능하면 EXECUTION_SYSTEM_PROMPT)
        # Step 4: append_to_system_message()로 시스템 메시지에 추가
        # Step 5: return handler(request)
        return handler(request)

    # ------------------------------------------------------------------
    # TODO 3: 큰 Tool 결과를 파일로 교체 (eviction)
    # ------------------------------------------------------------------
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        # TODO 3: Tool 결과가 너무 크면 파일로 교체하세요
        #
        # Step 1: self._tool_token_limit_before_evict가 None이면 → 그대로 handler(request)
        # Step 2: tool name이 TOOLS_EXCLUDED_FROM_EVICTION에 있으면 → 그대로 handler(request)
        # Step 3: tool_result = handler(request)
        # Step 4: return self._intercept_large_tool_result(tool_result, request.runtime)
        return handler(request)
