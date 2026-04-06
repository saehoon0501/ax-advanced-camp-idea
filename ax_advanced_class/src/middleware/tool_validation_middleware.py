"""
Tool Validation Middleware

Provides validation for all tool calls using LangChain's @wrap_tool_call middleware.
Uses tree-sitter-bash for robust command parsing and security validation.

학습 목표:
- DENY -> ALLOW -> ASK 3단계 검증 패턴 이해
- 경로 기반 권한 검증 구현
- interrupt()를 활용한 사용자 확인 흐름 구현
- Read-before-write 패턴으로 파일 안전성 보장
"""

import os
from typing import Callable, List

from langchain_core.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest
from langgraph.errors import GraphInterrupt
from langgraph.types import Command, interrupt

from ax_advanced_class.src.config.tool_permission_config import (
    PermissionLevel,
    PermissionConfig,
    PermissionRule,
    CommandValidationResult,
)
from ax_advanced_class.src.middleware._internals.tool_validation_helpers import (
    _BashValidatorBase,
    ToolValidationMiddlewareBase,
    _BASH_TOOL_NAMES,
    _FILE_TOOL_NAMES,
    _WRITE_FILE_TOOLS,
)


class _BashValidator(_BashValidatorBase):
    """
    Bash command & path validator.

    validate_command: 명령어 문자열을 검증하여 DENY/ALLOW/ASK 결정
    validate_path: 파일 경로를 검증하여 DENY/ALLOW/ASK 결정

    Hint: 부모 클래스(_BashValidatorBase)에 다음 헬퍼가 있습니다:
    - self.config: PermissionConfig (blocked_raw_patterns, blocked_paths, allowed_paths 등)
    - self._parser: BashParser (parse 메서드로 명령어 파싱)
    - self._check_rules(command): deny/allow rule 매칭
    - self._validate_parsed_command(parsed): 개별 파싱 결과 검증
    - self._get_highest_priority_result(results, command): 가장 높은 우선순위 결과 반환
    """

    def validate_command(self, command: str) -> CommandValidationResult:
        """
        셸 명령어를 검증합니다.

        Returns:
            CommandValidationResult - DENY, ALLOW, 또는 ASK
        """
        # TODO 1: DENY -> ALLOW -> ASK 3단계 검증
        #
        # Step 1: 빈 명령어 -> ALLOW (CommandValidationResult 반환)
        # Step 2: self.config.blocked_raw_patterns 순회 -> 매치되면 DENY
        #         (blocked_items에 매치된 pattern 포함)
        # Step 3: self._check_rules(command) -> 결과 있으면 반환
        # Step 4: self._parser.parse(command) -> 파싱 실패(빈 리스트)면 DENY
        #         (reason: "Could not parse command structure")
        # Step 5: 각 파싱 명령어에 self._validate_parsed_command() 호출
        #         -> DENY면 즉시 반환, 아니면 results 리스트에 추가
        # Step 6: self._get_highest_priority_result(results, command)
        # Step 1: 빈 명령어
        if not command or not command.strip():
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=command,
                reason="Empty command",
            )

        # Step 2: 원시 패턴 차단 (파싱 전)
        for pattern in self.config.blocked_raw_patterns:
            if pattern in command:
                return CommandValidationResult(
                    level=PermissionLevel.DENY,
                    command=command,
                    reason="Command contains blocked pattern",
                    blocked_items=[pattern],
                )

        # Step 3: PermissionRule 기반 매칭
        rule_result = self._check_rules(command)
        if rule_result:
            return rule_result

        # Step 4: 명령어 파싱
        parsed_commands = self._parser.parse(command)
        if not parsed_commands:
            return CommandValidationResult(
                level=PermissionLevel.DENY,
                command=command,
                reason="Could not parse command structure",
            )

        # Step 5: 각 파싱된 명령어 검증
        results: List[CommandValidationResult] = []
        for parsed in parsed_commands:
            result = self._validate_parsed_command(parsed)
            results.append(result)
            if result.level == PermissionLevel.DENY:
                return result

        # Step 6: 최종 결과
        return self._get_highest_priority_result(results, command)

    def validate_path(self, path: str, is_write: bool = True) -> CommandValidationResult:
        """
        파일 경로를 검증합니다.

        Args:
            path: 검증할 파일 경로
            is_write: True이면 쓰기 작업, False이면 읽기 작업

        Returns:
            CommandValidationResult - DENY, ALLOW, 또는 ASK
        """
        # TODO 2: 경로 기반 DENY -> ALLOW -> ASK
        #
        # Step 1: 빈 경로 -> ALLOW (reason: "Empty path defaults to workspace")
        # Step 2: os.path.abspath(os.path.expanduser(path))로 정규화
        # Step 3: self.config.blocked_paths 순회
        #         -> os.path.abspath(blocked)와 비교, normalized.startswith면 DENY
        #         (blocked_items에 blocked 포함)
        # Step 4: [self.config.workspace_root] + self.config.allowed_paths 순회
        #         -> os.path.abspath(os.path.expanduser(allowed))와 비교
        #         -> normalized == allowed_abs 또는 normalized.startswith(allowed_abs + os.sep)면 ALLOW
        # Step 5: 위 어디에도 해당 안 되면 (외부 경로):
        #         -> is_write이면 ASK (reason에 normalized 경로 포함)
        #         -> !is_write이면 ALLOW
        # Step 1: 빈 경로
        if not path:
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=path,
                reason="Empty path defaults to workspace",
            )

        # Step 2: 경로 정규화
        normalized = os.path.abspath(os.path.expanduser(path))

        # Step 3: 차단 경로 체크
        for blocked in self.config.blocked_paths:
            blocked_abs = os.path.abspath(blocked)
            if normalized.startswith(blocked_abs):
                return CommandValidationResult(
                    level=PermissionLevel.DENY,
                    command=path,
                    reason=f"Path is in blocked directory: {blocked}",
                    blocked_items=[blocked],
                )

        # Step 4: 허용 경로 체크
        allowed_roots = [self.config.workspace_root] + self.config.allowed_paths
        for allowed in allowed_roots:
            allowed_abs = os.path.abspath(os.path.expanduser(allowed))
            if normalized == allowed_abs or normalized.startswith(allowed_abs + os.sep):
                return CommandValidationResult(
                    level=PermissionLevel.ALLOW,
                    command=path,
                    reason=f"Path is in allowed directory: {allowed}",
                )

        # Step 5: 외부 경로 — 읽기/쓰기 구분
        if is_write:
            return CommandValidationResult(
                level=PermissionLevel.ASK,
                command=path,
                reason=f"Write to external path requires approval: {normalized}",
            )
        else:
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=path,
                reason="Read from external path is allowed",
            )


class ToolValidationMiddleware(ToolValidationMiddlewareBase):
    """
    도구 호출을 가로채 검증하는 미들웨어.

    Features:
    - Bash 명령어: validate_command로 DENY/ALLOW/ASK 검증
    - 파일 도구: validate_path로 경로 검증 + read-before-write 보장
    - ASK인 경우 interrupt()로 사용자에게 확인 요청

    Hint: 부모 클래스(ToolValidationMiddlewareBase)에 다음 헬퍼가 있습니다:
    - self._validator: _BashValidator 인스턴스
    - self._read_files: dict[str, float] (경로 -> 읽은 시점의 mtime)
    - self._is_allowed(tool_name, content): 세션 규칙 매칭 확인
    - self._add_allow_rule(tool_name, content): 세션 규칙 추가
    - self._enforce_timeout_limits(args): 타임아웃 제한 적용
    - self._truncate_output(result): 출력 자르기
    - self._format_tool_error(tool_name, args, error): 에러 메시지 포맷
    """

    def __init__(self, config: PermissionConfig):
        super().__init__(config)
        self._validator = _BashValidator(config)  # 학생이 구현한 validator 사용

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """도구 호출을 가로채 검증합니다."""
        tool_name = request.tool_call["name"]
        args = request.tool_call["args"]
        tool_call_id = request.tool_call["id"]

        try:
            # --- Bash Tool Validation ---
            if tool_name in _BASH_TOOL_NAMES:
                # TODO 3: Bash 검증 + ASK 처리
                #
                # Step 1: self._enforce_timeout_limits(args)
                # Step 2: "command"가 args에 있으면 self._validator.validate_command(args["command"])
                # Step 3: result.level == DENY -> ToolMessage(status="error") 반환
                #         content: f"Error: Command denied. {result.reason}"
                # Step 4: result.level == ASK:
                #   4a. self._is_allowed(tool_name, command)가 False이면:
                #       - cmd_prefix = command.split()[0] (빈 문자열이면 command 그대로)
                #       - interrupt() 호출 (question, tool_call_id, command, tool_name, allow_rule 포함)
                #       - response == "always" -> self._add_allow_rule(tool_name, command)
                #       - response가 falsy 또는 "deny:"로 시작 -> ToolMessage(status="error") 반환
                self._enforce_timeout_limits(args)

                if "command" in args:
                    result = self._validator.validate_command(args["command"])

                    if result.level == PermissionLevel.DENY:
                        return ToolMessage(
                            content=f"Error: Command denied. {result.reason}",
                            tool_call_id=tool_call_id,
                            status="error",
                        )

                    if result.level == PermissionLevel.ASK:
                        command = args["command"]
                        if not self._is_allowed(tool_name, command):
                            cmd_prefix = command.split()[0] if command.strip() else command
                            response = interrupt(
                                {
                                    "question": f"Command '{command}' requires confirmation",
                                    "tool_call_id": tool_call_id,
                                    "command": command,
                                    "tool_name": tool_name,
                                    "allow_rule": f"{tool_name}({cmd_prefix}:*)",
                                }
                            )
                            if response == "always":
                                self._add_allow_rule(tool_name, command)
                            elif not response or (isinstance(response, str) and response.startswith("deny:")):
                                feedback = response[5:] if isinstance(response, str) and response.startswith("deny:") else ""
                                reason = f"User feedback: {feedback}" if feedback else result.reason
                                return ToolMessage(
                                    content=f"Error: Command denied. {reason}",
                                    tool_call_id=tool_call_id,
                                    status="error",
                                )

            # --- File Tool Validation ---
            elif tool_name in _FILE_TOOL_NAMES:
                # TODO 4: 경로 검증 + Read-before-write
                #
                # Part A: 경로 검증
                #   A1. args에서 경로 추출 (키 우선순위: "file_path" > "validated_path" > "path")
                #   A2. 절대경로가 아니면 os.path.join(self._config.workspace_root, path)
                #   A3. normalized_path = self._validator.get_normalized_path(path)
                #   A4. is_write = tool_name in _WRITE_FILE_TOOLS
                #   A5. self._validator.validate_path(path, is_write=is_write)
                #   A6. DENY -> ToolMessage(status="error", content="Error: Path denied. ...")
                #   A7. ASK -> self._is_allowed 확인 -> interrupt() -> response 처리
                #       (allow_rule에 parent_dir 사용: os.path.dirname(normalized_path))
                #       response == "always" -> self._allow_rules.append(PermissionRule(...))
                #   A8. args[path_key] = normalized_path (정규화된 경로로 업데이트)
                #
                # Part B: Read-before-write 검증 (is_write가 True일 때만)
                #   B1. os.path.exists(normalized_path) 확인
                #   B2. 파일 존재 + normalized_path가 self._read_files에 없음
                #       -> ToolMessage(status="error") "You must read the file first..."
                #   B3. 파일 존재 + os.path.getmtime > self._read_files[normalized_path]
                #       -> ToolMessage(status="error") "File has been modified since..."
                if "file_path" in args or "path" in args or "validated_path" in args:
                    path_key = "file_path" if "file_path" in args else ("validated_path" if "validated_path" in args else "path")
                    path = args[path_key]

                    if not os.path.isabs(path):
                        path = os.path.join(self._config.workspace_root, path)

                    normalized_path = self._validator.get_normalized_path(path)
                    is_write = tool_name in _WRITE_FILE_TOOLS

                    result = self._validator.validate_path(path, is_write=is_write)

                    if result.level == PermissionLevel.DENY:
                        return ToolMessage(
                            content=f"Error: Path denied. {result.reason}",
                            tool_call_id=tool_call_id,
                            status="error",
                        )

                    if result.level == PermissionLevel.ASK:
                        if not self._is_allowed(tool_name, normalized_path):
                            parent_dir = os.path.dirname(normalized_path)
                            response = interrupt(
                                {
                                    "question": f"Path '{normalized_path}' requires confirmation",
                                    "tool_call_id": tool_call_id,
                                    "path": normalized_path,
                                    "tool_name": tool_name,
                                    "allow_rule": f"{tool_name}({parent_dir}:*)",
                                }
                            )
                            if response == "always":
                                self._allow_rules.append(
                                    PermissionRule(tool_name=tool_name, pattern=f"{parent_dir}:*")
                                )
                            elif not response or (isinstance(response, str) and response.startswith("deny:")):
                                feedback = response[5:] if isinstance(response, str) and response.startswith("deny:") else ""
                                reason = f"User feedback: {feedback}" if feedback else result.reason
                                return ToolMessage(
                                    content=f"Error: Path denied. {reason}",
                                    tool_call_id=tool_call_id,
                                    status="error",
                                )

                    # Read-before-write check
                    if is_write:
                        file_exists = os.path.exists(normalized_path)
                        if file_exists:
                            if normalized_path not in self._read_files:
                                operation = "writing to" if tool_name == "write_file" else "editing"
                                return ToolMessage(
                                    content=f"Error: You must read the file first before {operation} it. Use the read_file tool first.",
                                    tool_call_id=tool_call_id,
                                    status="error",
                                )
                            try:
                                current_mtime = os.path.getmtime(normalized_path)
                                read_mtime = self._read_files[normalized_path]
                                if current_mtime > read_mtime:
                                    operation = "writing to" if tool_name == "write_file" else "editing"
                                    return ToolMessage(
                                        content=f"Error: File has been modified since you last read it. Please read the file again before {operation} it.",
                                        tool_call_id=tool_call_id,
                                        status="error",
                                    )
                            except OSError:
                                pass

                    args[path_key] = normalized_path

            # --- Execute handler + post-processing ---
            handler_result = handler(request)

            # Track reads after successful read operations
            if tool_name == "read_file":
                if isinstance(handler_result, ToolMessage) and handler_result.status != "error":
                    if "file_path" in args or "path" in args or "validated_path" in args:
                        path_key = "file_path" if "file_path" in args else ("validated_path" if "validated_path" in args else "path")
                        normalized_path = self._validator.get_normalized_path(args[path_key])
                        try:
                            self._read_files[normalized_path] = os.path.getmtime(normalized_path)
                        except OSError:
                            pass

            # Update tracking after successful write/edit
            if tool_name in _WRITE_FILE_TOOLS:
                if isinstance(handler_result, ToolMessage) and handler_result.status != "error":
                    if "file_path" in args or "path" in args or "validated_path" in args:
                        path_key = "file_path" if "file_path" in args else ("validated_path" if "validated_path" in args else "path")
                        normalized_path = self._validator.get_normalized_path(args[path_key])
                        try:
                            self._read_files[normalized_path] = os.path.getmtime(normalized_path)
                        except OSError:
                            pass

            # Apply output truncation (hard limit)
            handler_result = self._truncate_output(handler_result)

            return handler_result

        except GraphInterrupt:
            raise
        except Exception as e:
            error_msg = self._format_tool_error(tool_name, args, e)
            return ToolMessage(
                content=error_msg,
                tool_call_id=tool_call_id,
                status="error",
            )
