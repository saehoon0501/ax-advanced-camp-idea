# AI Agent 개발 심화 노트 (Advanced Engineering Notes)

> 특정 상황이나 고급 엔지니어링 단계에서 반드시 고려해야 할 심화 주제들을 정리한 노트입니다.

---

## 1. LangGraph 구현 시 구체적인 주의사항 (Implementation Pitfalls)

LangGraph는 강력하지만, 실제 구현 시 마주치는 프레임워크 특유의 함정들이 있습니다.

### A. `create_supervisor` 헬퍼 함수의 한계
LangGraph가 제공하는 `create_supervisor` 같은 편의성 함수는 초기 프로토타이핑에는 좋지만 운영 환경에서는 위험할 수 있습니다.
- **느슨한 라우팅:** 제어가 명확하지 않아 예상치 못한 노드로 튀는 경우가 발생합니다.
- **무한 루프:** 이미 방문한 노드를 Supervisor가 다시 배정하여 무한 루프에 빠지는 이슈가 보고된 바 있습니다 (2025.09 기준).
- **조기 종료:** 다음 절차가 남아있음에도 Supervisor가 임의로 판단하여 종료하는 경우가 있습니다.
- **대안:** 정확도가 중요한 엔터프라이즈 시스템에서는 헬퍼 함수 대신 **명시적인 조건부 엣지(Conditional Edge)와 커스텀 라우터 노드**를 직접 구현하는 것을 권장합니다.

### B. Edge API vs Command API
- **Edge API:** 복잡한 조건 처리가 번거롭고 코드가 길어집니다.
- **Command API:** 직관적이지만, 존재하지 않는 노드로 연결하거나 로직 실수로 인한 휴먼 에러 발생 가능성이 높습니다.
- **권장:** 팀 내에서 연결 방식을 통일하고, 그래프 구조를 시각화하여 리뷰하는 절차가 필수적입니다.

---

## 2. Advanced UX: 디바이스 간 상태 공유 및 재접속 (Cross-Device State)

웹앱 환경에서 가장 까다로운 문제 중 하나는 **"생성 중에 사용자가 새로고침을 하거나 다른 기기로 접속했을 때"**입니다.

### 문제 상황
- 사용자가 긴 리포트 생성을 요청하고 브라우저를 닫음.
- 1분 후 모바일로 접속.
- 서버에서는 LLM이 여전히 생성 중이지만, 클라이언트는 연결이 끊겨 아무것도 보이지 않음.
- 사용자는 생성이 안 된 줄 알고 다시 요청 -> **중복 과금 및 자원 낭비**.

### 해결 아키텍처: 스트림 분리 (Decoupled Streaming)
이 문제를 해결하려면 **"생성(Generation)"**과 **"송출(Transmission)"**을 분리해야 합니다.

1.  **Backend Worker:** LLM 응답을 생성하면서 토큰 단위로 Redis Pub/Sub 채널이나 DB의 임시 버퍼에 씁니다. 동시에 진행 상태(status: `generating`)를 기록합니다.
2.  **Client Connection:** 클라이언트가 접속하면 DB에서 현재 작업 상태를 조회합니다.
3.  **Resume:** 상태가 `generating`이라면, 즉시 Redis Pub/Sub 채널을 구독하여 **중간부터 스트리밍을 이어받습니다.**
4.  **Completion:** 생성이 완료되면 완성된 결과를 DB에 저장하고 Pub/Sub을 종료합니다.

> **Note:** 구현 복잡도가 상당히 높으므로, 정말 필요한 기능인지(Long-running task 인지) 검토 후 도입해야 합니다.

---

## 3. Prompt Engineering Ops (PromptOps)

단순히 프롬프트를 잘 쓰는 것을 넘어, 시스템적으로 관리하는 방법입니다.

### A. 프롬프트 의존성 관리 (Dependency Mapping)
코드는 함수 호출 관계를 IDE가 찾아주지만, 프롬프트는 수정 시 영향도를 파악하기 어렵습니다.
- **문제:** "요약 프롬프트"를 수정했는데, 이를 바탕으로 동작하는 "분류 에이전트"가 오작동.
- **해결:** 프롬프트 ID와 이를 사용하는 워크플로우/에이전트 간의 **매핑 테이블**을 관리해야 합니다.
- 프롬프트 변경 시, 연관된 모든 Golden Set 테스트가 자동으로 수행되어야 합니다.

### B. 동적 프롬프트 저장소 (Dynamic Prompt Store)
- 하드코딩된 프롬프트는 배포 없이 수정이 불가능합니다.
- DB에 프롬프트를 저장하고, 애플리케이션 시작 시(또는 주기적으로) 로딩하여 사용하는 구조를 구축하면 운영 대응 속도가 빨라집니다.

---

## 4. Vendor Specific & Future Trends

특정 벤더나 미래 기술 트렌드에 관한 내용으로, 현재 시점의 아키텍처 결정에 참고가 될 수 있습니다.

### A. AWS AI DLC (Development LifeCycle) & Kiro
- **Steering & Agent Hooks:** AWS Kiro(2025.11 출시)와 같은 도구는 `Claude Code Skills`와 유사하게, 상황별로 필요한 Rule Set(Steering)을 동적으로 로딩합니다.
- **MSA 접근법:** 거대한 단일 프롬프트 대신, 도메인별로 컴포넌트와 서비스를 나누고 각각에 맞는 Rule Prompt를 적용하는 **AIDD(AI-Driven Development)** 방식이 부상하고 있습니다.

### B. 차세대 모델 아키텍처 (Beyond Transformers)
현재의 LLM(Transformer)은 입력 토큰이 길어지면 느려지고(Quadratic complexity), 스트리밍이 필수적입니다. 이를 극복하기 위한 연구들이 진행 중입니다.
- **CALM (Continuous Autoregressive Language Models):** 생성 속도와 일관성을 개선하려는 시도.
- **DLM (Diffusion-based Language Model):** 이미지를 생성하듯 텍스트를 생성하여, 왼쪽에서 오른쪽으로 순차 생성하는 제약을 넘어서려는 시도.
- **시사점:** 현재는 Transformer가 주류이지만, 미래에는 "스트리밍 없이 한 번에 결과가 나오는" 모델이 등장할 수 있으므로, 아키텍처를 너무 스트리밍에만 종속되게(Coupling) 만들지 않는 유연함이 필요할 수 있습니다.

