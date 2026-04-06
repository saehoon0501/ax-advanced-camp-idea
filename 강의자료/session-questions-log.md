# Session Questions Log

> Role-play simulation: 20 Vietnamese developers (mixed level)
> Purpose: 강의 흐름 연습 — anticipate student questions per session

---

## Day 1 (4일차)

### Session 1: Intro (20 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Minh | Mid | "Is AI agent like ChatGPT plugin or something different?" | Concept |
| 2 | Trang | Senior | "So the problem is — every new session, the agent starts from zero? No memory at all?" | Concept |
| 3 | Duc | Junior | "Context window... what is that?" (whispered to neighbor) | Terminology |
| 4 | Huy | Junior | "We actually build something? (blog platform)" | Scope |
| 5 | Minh | Mid | "Orchestrator is like a router — doesn't do actual work, just decides where to send?" | Architecture |
| 6 | Lan | Junior | "StateGraph — is this Python library? I only know basic Python..." | Prerequisite |
| 7 | Phong | Mid | "This looks like microservice pattern... separate concerns." | Architecture |
| 8 | Trang | Senior | "Middleware folder — is this like Express middleware concept?" | Concept |
| 9 | Duc | Junior | "6 practices in 2 days... is it enough time?" | Pace |
| 10 | Linh | Mid | "The evals/ folder — we also learn how to test the agent?" | Scope |
| 11 | Nam | Mid | "What is `uv`? I usually use `pip` or `conda`..." | Tooling |
| 12 | Minh | Mid | "AWS Bedrock — do we need AWS account? Or you provide credentials?" | Setup |

---

### Session 2: Context Engineering 소개 (30 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Trang | Senior | "How is Context Engineering different from just prompt engineering?" | Concept |
| 2 | Minh | Mid | "128K tokens sounds like a lot — in practice, how fast does it fill up?" | Practical |
| 3 | Duc | Junior | "Token is like... one word? Or one character?" | Terminology |
| 4 | Phong | Mid | "If context window resets each session, why not just save the full chat history to a file and reload?" | Design |
| 5 | Lan | Junior | "Sorry, what is 'context window' exactly? Like browser window?" | Terminology |
| 6 | Trang | Senior | "You said cost is proportional to tokens — what's the actual cost per 1K tokens for Bedrock?" | Cost |
| 7 | Nam | Mid | "The 3 strategies — compress, inject, control — do we always use all three together?" | Architecture |
| 8 | Huy | Junior | "What happens when agent 'loses its way'? It gives wrong answer or just stops?" | Behavior |
| 9 | Linh | Mid | "Is summarization lossy? Do we lose important details when compressing?" | Tradeoff |
| 10 | Phong | Mid | "In production, who monitors the token usage — the agent itself or external system?" | Operations |

---

### Session 3: LangChain & LangGraph 설명 (30 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Duc | Junior | "What is difference between LangChain and LangGraph? Why we need both?" | Concept |
| 2 | Trang | Senior | "Can we use LangGraph without LangChain? Or they are tightly coupled?" | Architecture |
| 3 | Minh | Mid | "StateGraph — is the state shared between all nodes? Or each node has own state?" | State Mgmt |
| 4 | Lan | Junior | "I don't understand 'node' and 'edge'... can you draw simple example?" | Terminology |
| 5 | Nam | Mid | "How does LangGraph compare to CrewAI or AutoGen?" | Comparison |
| 6 | Phong | Mid | "Conditional edge — is this like if/else in the graph? Who decides the condition?" | Mechanics |
| 7 | Huy | Junior | "Do we need to install LangChain and LangGraph separately?" | Setup |
| 8 | Trang | Senior | "What about error handling in the graph? If a node fails, does the whole graph fail?" | Error Handling |
| 9 | Linh | Mid | "The message types — HumanMessage, AIMessage, SystemMessage — these are LangChain classes?" | API |
| 10 | Minh | Mid | "Can we visualize the graph while developing? Like see the flow?" | Tooling |

---

### Session 4: Orchestrator 구성 실습 (20 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Lan | Junior | "I got ImportError... which package do I need to install?" | Setup |
| 2 | Duc | Junior | "Where do I write the code? Which file should I open?" | Navigation |
| 3 | Minh | Mid | "The router node — does it use LLM to decide routing, or is it rule-based?" | Design |
| 4 | Trang | Senior | "Why not use LangGraph's built-in `Command` for routing instead of conditional edge?" | Alternative |
| 5 | Nam | Mid | "How do we test if routing works correctly before connecting real agents?" | Testing |
| 6 | Phong | Mid | "If router sends to wrong agent, is there a fallback mechanism?" | Error Handling |
| 7 | Huy | Junior | "My code runs but nothing happens... no output" | Debugging |
| 8 | Linh | Mid | "Can we add more agents later? Like a 'Reviewer Agent'?" | Extensibility |

---

### Session 5: Middleware 설명 (30 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Phong | Mid | "This is exactly like Express middleware! Request → middleware chain → handler → response" | Confirmation |
| 2 | Trang | Senior | "What's the execution order of middlewares? Does order matter?" | Architecture |
| 3 | Minh | Mid | "Can middleware modify the messages before they reach the LLM? And also after?" | Mechanics |
| 4 | Duc | Junior | "What is 'middleware'? I never used this concept before..." | Terminology |
| 5 | Nam | Mid | "How many middlewares can we stack? Is there performance overhead?" | Performance |
| 6 | Lan | Junior | "Is middleware same as decorator in Python?" | Concept |
| 7 | Trang | Senior | "In agent_specs.py — the middleware list, is it applied in order or reverse order?" | Implementation |
| 8 | Linh | Mid | "Can we write custom middleware for logging? Like log every LLM call?" | Extensibility |

---

### Session 6: Agent Context + Token / Summarizer (70 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Duc | Junior | "How do I count tokens? Is there a function for that?" | Practical |
| 2 | Trang | Senior | "tiktoken vs model's native tokenizer — which one should we use for Bedrock?" | Implementation |
| 3 | Minh | Mid | "The summarizer — does it summarize the whole conversation or just old parts?" | Design |
| 4 | Lan | Junior | "What is 'threshold'? When does summarization trigger?" | Terminology |
| 5 | Nam | Mid | "If we summarize too aggressively, agent might forget important context. How to balance?" | Tradeoff |
| 6 | Phong | Mid | "Does the summarization itself cost tokens? We're using LLM to summarize LLM output..." | Cost |
| 7 | Trang | Senior | "Can we use different models for summarization? Like cheaper model for summary, expensive for main task?" | Optimization |
| 8 | Huy | Junior | "My summarizer is not working... the message list doesn't change" | Debugging |
| 9 | Linh | Mid | "Should system message ever be summarized? Or always kept intact?" | Design |
| 10 | Minh | Mid | "In production, do companies actually use auto-summarization or just truncate?" | Industry |
| 11 | Duc | Junior | "I'm confused about the TODO in the code... what exactly should I implement?" | Navigation |
| 12 | Trang | Senior | "What about multi-turn tool calls? If we summarize a tool call and its result, agent loses the ability to reference it" | Edge Case |
| 13 | Phong | Mid | "Can we persist the summary to disk so next session starts with it?" | Persistence |
| 14 | Nam | Mid | "The token count includes tool definitions too? Or just messages?" | Mechanics |

---

### Session 7: Prompt 심화 / Dynamic Prompt (70 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Minh | Mid | "Dynamic prompt — so the system message changes every turn? Isn't that expensive?" | Cost |
| 2 | Trang | Senior | "How does dynamic prompt relate to RAG? Both inject context at runtime" | Concept |
| 3 | Lan | Junior | "What is 'system prompt'? Is it the first message we send to AI?" | Terminology |
| 4 | Duc | Junior | "Where do I see the actual prompt? Which file?" | Navigation |
| 5 | Nam | Mid | "The @dynamic_prompt decorator — how does it know what context to inject?" | Implementation |
| 6 | Phong | Mid | "If we inject too much context into prompt, we're back to the token problem..." | Tradeoff |
| 7 | Trang | Senior | "Static rules vs dynamic context — what's the guideline for what goes where?" | Design |
| 8 | Huy | Junior | "Can I see example of what the final prompt looks like after injection?" | Practical |
| 9 | Linh | Mid | "progress.md and feature_list.json — these are read every turn?" | Performance |
| 10 | Minh | Mid | "Soft rules in the prompt — what if the agent ignores them?" | Reliability |
| 11 | Trang | Senior | "Expert activation / MoE concept — does this actually make LLM respond differently?" | Theory |
| 12 | Nam | Mid | "How do we test that prompt changes actually improve agent behavior?" | Evaluation |

---

### Session 8: Tool 설계 / Filesystem Middleware (70 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Trang | Senior | "7 tools seems like a lot — does more tools confuse the LLM?" | Design |
| 2 | Minh | Mid | "How does LLM decide which tool to call? Is it reliable?" | Reliability |
| 3 | Duc | Junior | "Tool is like... a function that AI can call? Like API?" | Terminology |
| 4 | Phong | Mid | "Soft rules injection with tools — the rules go into tool description or system prompt?" | Implementation |
| 5 | Lan | Junior | "I created a tool but agent never uses it..." | Debugging |
| 6 | Nam | Mid | "Large tool output (5KB JSON) — should we truncate or summarize?" | Design |
| 7 | Trang | Senior | "Tool output trimming — do we define schema per tool, or one generic trimmer?" | Architecture |
| 8 | Huy | Junior | "Can the agent call multiple tools at once? Or one at a time?" | Mechanics |
| 9 | Linh | Mid | "If bash tool runs dangerous command like `rm -rf`, how do we prevent it?" | Safety |
| 10 | Minh | Mid | "The file tools — read, write, list — do they work with any file on the system?" | Security |
| 11 | Phong | Mid | "Defer loading — load tool description only when needed? How does LLM know it exists?" | Design |
| 12 | Trang | Senior | "In production, how do you handle tool timeout? What if bash command hangs?" | Operations |

---

## Day 2 (5일차)

### Session 9: Tool Permission System (100 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Minh | Mid | "DENY > ALLOW > ASK — why this specific priority order?" | Design |
| 2 | Trang | Senior | "Pattern matching for permissions — regex or glob? How granular can we get?" | Implementation |
| 3 | Duc | Junior | "What does 'ASK' mean? Ask who? The user?" | Terminology |
| 4 | Lan | Junior | "I don't understand the permission config file... too many rules" | Navigation |
| 5 | Phong | Mid | "Is this like RBAC (Role-Based Access Control)? Or more like ACL?" | Concept |
| 6 | Nam | Mid | "Can permissions change at runtime? Like user grants permission mid-session?" | Mechanics |
| 7 | Trang | Senior | "How do you handle permission for chained tool calls? Tool A output feeds Tool B — if B is denied, what happens?" | Edge Case |
| 8 | Huy | Junior | "My validation middleware blocks everything... nothing works" | Debugging |
| 9 | Linh | Mid | "The deny-with-message — can we customize the message per rule?" | Implementation |
| 10 | Minh | Mid | "In Claude Code, how does the permission system work? Similar pattern?" | Comparison |
| 11 | Trang | Senior | "What about implicit permissions? Like if agent has write_file, it can effectively execute code by writing a script..." | Security |
| 12 | Phong | Mid | "Should we log permission denials? For audit trail?" | Operations |
| 13 | Nam | Mid | "always-allow list — isn't that dangerous? What if tool behavior changes?" | Security |
| 14 | Duc | Junior | "Can you show the full flow? User message → tool call → permission check → result?" | Walkthrough |
| 15 | Trang | Senior | "How do production agents handle this? Do they all build custom permission systems?" | Industry |

---

### Session 10: Agent Harness 이론 (30 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Trang | Senior | "Implicit vs Explicit state — can you give concrete example of each?" | Concept |
| 2 | Minh | Mid | "Cold start recovery — does the agent really read progress.md every session? That's the whole trick?" | Design |
| 3 | Duc | Junior | "What is 'harness'? Like horse harness? Why this name?" | Terminology |
| 4 | Phong | Mid | "One feature per session — what if feature is too big for one session?" | Edge Case |
| 5 | Nam | Mid | "Git as communication medium — you mean the agent reads git log to understand history?" | Mechanics |
| 6 | Lan | Junior | "So the agent is like a new employee every morning who reads notes from yesterday?" | Analogy |
| 7 | Trang | Senior | "How does this compare to Anthropic's original article? Did you modify the pattern?" | Reference |
| 8 | Linh | Mid | "What if progress.md gets corrupted? Is there a recovery mechanism?" | Reliability |

---

### Session 11: TodoMiddleware 실습 (35 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Minh | Mid | "write_todos tool — does the agent decide when to create todos, or we force it?" | Design |
| 2 | Duc | Junior | "What is the format of todo items? JSON? Markdown?" | Implementation |
| 3 | Trang | Senior | "Todo state management — is this persisted to file or only in memory?" | Persistence |
| 4 | Lan | Junior | "I implemented the tool but agent writes weird todo items..." | Debugging |
| 5 | Nam | Mid | "Can agent mark todos as complete? Or only create them?" | Mechanics |
| 6 | Phong | Mid | "What prevents the agent from creating 50 todos and never finishing any?" | Reliability |
| 7 | Huy | Junior | "My middleware doesn't inject the todos into messages..." | Debugging |
| 8 | Trang | Senior | "Should todos survive across sessions? Or reset each session?" | Design |

---

### Session 12: Harness Prompting 실습 (35 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Trang | Senior | "PHASE 1/2/3 — does the agent actually follow these? How reliable is prompt-based control?" | Reliability |
| 2 | Minh | Mid | "Phase 1 is recovery, Phase 2 is implementation, Phase 3 is commit — what triggers the transition?" | Mechanics |
| 3 | Duc | Junior | "The prompt is very long... does the LLM actually read all of it?" | Concern |
| 4 | Phong | Mid | "How do we know the agent is in the right phase? Can we observe it?" | Observability |
| 5 | Nam | Mid | "If agent skips Phase 1 and goes straight to coding, what happens?" | Edge Case |
| 6 | Lan | Junior | "Can I see the actual prompt? I want to understand each section..." | Navigation |
| 7 | Trang | Senior | "Prompt-based behavior rules vs code-based enforcement — when to use which?" | Design |
| 8 | Linh | Mid | "The commit message format — is it enforced by prompt or by code?" | Implementation |

---

### Session 13: deepagents 소개 + 과정 마무리 (30 min)

| # | Student | Level | Question | Category |
|---|---------|-------|----------|----------|
| 1 | Minh | Mid | "deepagents — is this a library we can use in production?" | Practical |
| 2 | Trang | Senior | "How does deepagents compare to what we built? Does it abstract all the middleware?" | Comparison |
| 3 | Duc | Junior | "So everything we built by hand... deepagents does automatically?" | Concept |
| 4 | Phong | Mid | "Can we extend deepagents with custom middleware?" | Extensibility |
| 5 | Nam | Mid | "Is deepagents production-ready? Or still experimental?" | Maturity |
| 6 | Lan | Junior | "After this course, what should I study next?" | Career |
| 7 | Trang | Senior | "For our company's use case (not coding agent), can we apply these patterns? Like customer service agent?" | Application |
| 8 | Huy | Junior | "Can we get the course materials? And the code repository?" | Logistics |
| 9 | Linh | Mid | "Will there be advanced course after this? Like agent evaluation deep dive?" | Follow-up |
| 10 | Minh | Mid | "Thank you teacher! One last question — what's your recommendation for first real project using these patterns?" | Advice |

---

## Summary Statistics

| Category | Count | Notes |
|----------|-------|-------|
| **Concept / Theory** | 28 | "What is X?", "How does X relate to Y?" |
| **Terminology** | 14 | Students unfamiliar with terms (mostly juniors) |
| **Implementation** | 16 | "How do I code this?", "Which file?" |
| **Design / Architecture** | 22 | "Why this approach?", "What goes where?" |
| **Debugging** | 10 | "My code doesn't work..." |
| **Edge Cases / Tradeoffs** | 14 | Senior developers probing boundaries |
| **Security / Safety** | 6 | Permission, dangerous commands |
| **Operations / Production** | 8 | "How does this work in real world?" |
| **Setup / Tooling** | 6 | uv, packages, credentials |
| **Total** | ~124 | |

## Key Patterns Observed

1. **Juniors (Duc, Lan, Huy)** — struggle with terminology first, need analogies and visual examples
2. **Mid-level (Minh, Nam, Linh, Phong)** — ask practical "how" questions, want to see working code
3. **Senior (Trang)** — probes edge cases, compares with industry patterns, asks "why not X?"
4. **Common pain points**: Token concept, middleware concept, permission flow, prompt reliability
5. **Energy dips**: After lunch (Session 6-8 afternoon), mid-morning Day 2 (Session 9 is 100 min — needs a break)
6. **Highest engagement**: Hands-on sessions (Orchestrator, Summarizer, TodoMiddleware)
7. **Needs visual aids**: Architecture diagrams, token counting demo, permission flow diagram
