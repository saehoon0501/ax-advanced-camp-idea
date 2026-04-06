참고 자료:

- [Anthropic: Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)
- [Anthropic: Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [Anthropic: Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [12-Factor Agents: Own Your Context Window](https://github.com/dexhorthy/12-factor-agents/blob/main/content/factor-03-own-your-context-window.md)



목차


Context의 확장
Agent context 구성요소
Context 관리의 중요성
유한한 Context Window
Context rot 현상
Attention Budget
비용과 지연 시간
섹션 별 페이지 링크


Context의 확장
한두 번 호출로 끝나는 task에서는 시스템/유저 프롬프트를 잘 쓰는 것이 핵심이었습니다. → System prompt == Context
하지만 tool 호출, memory/외부 데이터 읽고, 수십수백 턴을 도는 agent loop가 기본 패턴이 되면서, 결과적으로 context window는 이전보다 더욱 빠르게 채워집니다.





Agent context 구성요소
Agent의 Context는 다음 요소들로 구성됩니다.



System prompt
Agent의 역할, 성격, 규칙 정의
"당신은 코딩 에이전트입니다..."

Tool 정의
사용 가능한 도구들에 대한 설명 및 스키마
파라미터, 반환값, 사용법 설명

Retrieved Data(RAG)
외부에서 검색해온 문서, 코드, 정보
벡터 DB, 파일 시스템 등에서 가져옴

Conversation History(대화 이력)
이전 메세지들(User, Assistant, Tool 결과)
작업이 길어질수록 급격히 증가

Working Memory
Todo 리스트, 현재 작업 상태
관련 대화에서 가져온 메모리

Output Format Instructions
응답 형식 지정(JSON, Markdown 등)


매 요청마다 이 모든 요소가 하나의 프롬프트로 조합되어 LLM에 전달됩니다.


통합 다이어그램: 하나의 LLM 호출에 들어가는 것

```
┌─────────────────────────────────────────────────────────┐
│                    Context Window                        │
│                                                          │
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │  System Prompt        │  │  Tool Definitions        │ │
│  │  역할, 규칙, 행동 지침  │  │  도구 스키마, 설명, 파라미터 │ │
│  │                       │  │                          │ │
│  │  ← Section 2에서 다룸  │  │  ← Section 3에서 다룸     │ │
│  └──────────────────────┘  └──────────────────────────┘ │
│                                                          │
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │  Conversation History │  │  Working Memory          │ │
│  │  이전 메시지, Tool 결과  │  │  Todos, 작업 상태         │ │
│  │  (턴이 쌓일수록 증가)    │  │                          │ │
│  │  ← Section 1에서 다룸  │  │                          │ │
│  └──────────────────────┘  └──────────────────────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │  Retrieved Data (RAG) + Output Format Instructions   ││
│  └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

이 6가지 요소가 합쳐져 하나의 Context Window를 구성합니다. 문제는 이 공간이 유한하다는 것입니다.

이 과정에서는 3가지 섹션을 통해 Context를 전략적으로 관리하는 방법을 배웁니다:

| 섹션 | 핵심 질문 | 전략 |
|------|----------|------|
| **Section 1: 토큰** | 컨텍스트를 어떻게 **줄이는가**? | 토큰 효율성, Prompt Caching, 압축(Truncation/Summarization) |
| **Section 2: 프롬프트** | 컨텍스트를 어떻게 **넣는가**? | Expert Activation, Reasoning 모델 활용, 동적 주입 |
| **Section 3: 도구** | 컨텍스트를 어떻게 **통제하는가**? | Defer Loading, Tool Output 크기 제한 |



Context 관리의 중요성
유한한 Context Window
모든 LLM은 처리할 수 있는 토큰 수에 Hard Limit이 있습니다.

GPT 5.2	400K 토큰
Claude 4.5 Opus	200K 토큰
Gemini 3.0 pro	1M 토큰
많아 보이지만, Agent가 Tool을 적극적으로 사용하면 금방 소진됩니다.



Context rot 현상
모델이 발전할 수록 context window의 크기는 증가합니다.
하지만, 이를 "Context window의 크기를 전부 채워서 활용할 수 있다."라 이해한다면, 특정 token 양을 넘었을 때, 성능 저하를 경험할 수 있습니다.
이렇게 길이가 길어질수록 필요한 정보를 정확히 찾아 사용하지 못하는 이른바 context rot 현상이라고 합니다.



이론적인 최대 길이와는 별개로 모델이 안정적으로 집중할 수 있는 실질적인 구간이 존재합니다. 
결과적으로, 내용을 가능한 한 많이 넣는 것이 아니라, 적절히 짧으면서도 영양가 있는 부분만 선별해 넣는 것이 성능과 안정성 면에서 더 유리한 경우가 많습니다.



Attention Budget
Context rot과 연결되는 개념입니다. LLM이 실질적으로 집중할 수 있는 token 양을 의미합니다.



비용과 지연 시간

- 토큰 = 비용: 입력 토큰도 과금됩니다

- 토큰 = 지연: 더 많은 토큰 = 더 긴 응답 시간

따라서  단순히 프롬프트를 잘 쓰는 것을 넘어서, Context의 6가지 구성 요소를 전략적으로 설계하고 관리하는 것이 중요합니다.



섹션 별 페이지 링크
Token	
Section 1: 토큰 (Token)

Prompt	
Section 2: 프롬프트 (Prompt) 심화

Tool	
Section 3: 도구 (Tool)