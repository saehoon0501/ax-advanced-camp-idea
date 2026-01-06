# Migration Guide: Old → New Structure

## Quick Reference: What Changed?

This guide helps you understand how the old scenario structure maps to the new structure based on Anthropic's long-running agents article.

---

## 📊 Scenario Mapping Table

| Old # | Old Scenario Name      | Status      | New # | New Scenario Name               | Change Type      |
| ----- | ---------------------- | ----------- | ----- | ------------------------------- | ---------------- |
| 1     | Rolling Window         | ✅ Kept     | 1     | Rolling Window                  | Minor update     |
| 2     | Auto Summarizer        | ✅ Kept     | 2     | Auto Summarizer                 | Minor update     |
| 3     | Tool Output Trimmer    | ✅ Kept     | 3     | Tool Output Trimmer             | Minor update     |
| 4     | RAG Injector           | ❌ Replaced | 4     | **Feature List Manager**        | Complete rewrite |
| 5     | PII Sanitizer          | ❌ Replaced | 5     | **Git Progress Tracker**        | Complete rewrite |
| 6     | State Extractor        | 🔄 Revised  | 6     | **State Recovery Agent**        | Major revision   |
| 7     | Tool Selector          | ❌ Replaced | 7     | **Incremental Work Controller** | Complete rewrite |
| 8     | Thought Scratcher      | ❌ Replaced | 8     | **End-to-End Test Validator**   | Complete rewrite |
| 9     | Dynamic Persona        | ❌ Replaced | 9     | **Clean State Committer**       | Complete rewrite |
| 10    | Task Queue Prioritizer | ❌ Removed  | -     | -                               | Out of scope     |
| 11    | Content Enrichment     | ❌ Removed  | -     | -                               | Out of scope     |
| 12    | Multi-Criteria Scorer  | ❌ Removed  | -     | -                               | Out of scope     |

---

## 🔄 Detailed Changes by Scenario

### Scenario 1: Rolling Window ✅ KEPT

**Change**: Minor context adjustments  
**Why kept**: Still essential for managing conversation length across sessions  
**Update needed**: Examples now reference Coding Agent conversations

**Migration**: ✅ No code changes needed

---

### Scenario 2: Auto Summarizer ✅ KEPT

**Change**: Minor context adjustments  
**Why kept**: Critical for compressing `claude-progress.txt`  
**Update needed**: Examples now show summarizing session notes

**Migration**: ✅ No code changes needed

---

### Scenario 3: Tool Output Trimmer ✅ KEPT

**Change**: Minor context adjustments  
**Why kept**: Essential for compressing browser automation logs (Playwright/Puppeteer)  
**Update needed**: Examples now show trimming test output

**Migration**: ✅ No code changes needed

---

### Scenario 4: RAG Injector → Feature List Manager ❌ REPLACED

**Old focus**: Dynamic document retrieval and injection  
**New focus**: Managing structured JSON feature lists

**Why changed**:

- Long-running agents need explicit feature tracking
- JSON structure is more reliable than dynamic RAG
- Anthropic's article emphasizes feature list as core artifact

**Key concepts**:

```python
# OLD (RAG Injector)
def retrieve_context(query, knowledge_base):
    docs = vector_search(query, knowledge_base)
    return inject_as_system_message(docs)

# NEW (Feature List Manager)
def create_feature_list(project_spec):
    features = parse_requirements(project_spec)
    return structured_json_with_test_steps(features)

def select_next_feature(feature_list):
    return highest_priority_incomplete_feature(feature_list)
```

**Migration**: ⚠️ Complete rewrite needed

---

### Scenario 5: PII Sanitizer → Git Progress Tracker ❌ REPLACED

**Old focus**: Masking personal information  
**New focus**: Using Git commits and progress files for state persistence

**Why changed**:

- State persistence is more critical than PII for this scenario
- Git provides built-in version control and rollback
- Anthropic's article heavily emphasizes Git-based tracking

**Key concepts**:

```python
# OLD (PII Sanitizer)
def sanitize_input(text):
    text = mask_emails(text)
    text = mask_phone_numbers(text)
    return text

# NEW (Git Progress Tracker)
def commit_progress(feature_id, description):
    git_commit(f"feat: {description}")
    update_progress_file(feature_id)
    return commit_hash

def recover_from_git():
    commits = git_log(limit=10)
    progress = read_progress_file()
    return combined_context
```

**Migration**: ⚠️ Complete rewrite needed

---

### Scenario 6: State Extractor → State Recovery Agent 🔄 REVISED

**Old focus**: Extracting entities from conversation to structured state  
**New focus**: Recovering full context at session start

**Why changed**:

- Recovery is the #1 challenge in long-running agents
- Multi-source reconstruction (git + progress + features)
- Anthropic's "getting up to speed" section is crucial

**Key concepts**:

```python
# OLD (State Extractor)
def extract_entities(message):
    name = extract_name(message)
    preferences = extract_preferences(message)
    return UserProfile(name=name, prefs=preferences)

# NEW (State Recovery Agent)
def recover_session_state():
    git_context = read_git_log(limit=10)
    progress_context = read_progress_file()
    feature_context = load_feature_list()
    app_status = run_basic_test()

    return SessionState(
        last_completed=git_context.latest_feature,
        next_priority=feature_context.next_incomplete,
        is_healthy=app_status.success
    )
```

**Migration**: ⚠️ Major revision needed (expand scope)

---

### Scenario 7: Tool Selector → Incremental Work Controller ❌ REPLACED

**Old focus**: Selecting relevant tools dynamically  
**New focus**: Enforcing one-feature-at-a-time discipline

**Why changed**:

- "One-shotting" is the biggest failure mode in the article
- Scope control is more important than tool selection
- Feature-level checkpoints enable clean sessions

**Key concepts**:

```python
# OLD (Tool Selector)
def select_tools(query, all_tools):
    if "calculate" in query:
        return [MathTool]
    if "email" in query:
        return [EmailTool]

# NEW (Incremental Work Controller)
def select_next_feature(feature_list):
    incomplete = [f for f in features if not f.passes]
    return max(incomplete, key=lambda f: PRIORITY[f.priority])

def enforce_scope(feature_id, changed_files):
    expected_scope = feature_id_to_files(feature_id)
    violations = set(changed_files) - expected_scope
    if violations:
        raise ScopeViolation(f"Modified out-of-scope files: {violations}")
```

**Migration**: ⚠️ Complete rewrite needed

---

### Scenario 8: Thought Scratcher → End-to-End Test Validator ❌ REPLACED

**Old focus**: Separating reasoning from output  
**New focus**: Browser automation testing

**Why changed**:

- Anthropic found Claude marks features "done" without testing
- E2E testing is mandatory in their solution
- Browser automation (Puppeteer) is core to their approach

**Key concepts**:

```python
# OLD (Thought Scratcher)
def parse_output(model_output):
    thought = extract_section(model_output, "THOUGHT")
    answer = extract_section(model_output, "ANSWER")
    log_thought(thought)  # Don't include in context
    return answer

# NEW (End-to-End Test Validator)
async def run_e2e_test(feature):
    async with playwright() as browser:
        page = await browser.new_page()

        for step in feature.steps:
            await execute_step(page, step)

        screenshot = await page.screenshot()
        return TestResult(
            passed=all_steps_passed,
            screenshot=screenshot
        )
```

**Migration**: ⚠️ Complete rewrite needed, requires Playwright

---

### Scenario 9: Dynamic Persona → Clean State Committer ❌ REPLACED

**Old focus**: Switching agent personas/modes  
**New focus**: Ensuring clean state at session end

**Why changed**:

- "Clean handoff" is critical for next session
- Broken states waste next session's context
- Anthropic emphasizes git commits + verification

**Key concepts**:

```python
# OLD (Dynamic Persona)
def route_persona(message):
    if "code" in message:
        return CoderPersona
    if "sad" in message:
        return FriendPersona

# NEW (Clean State Committer)
def end_session(feature_id):
    # 1. Verify clean state
    report = verify_clean_state()
    if not report.is_clean:
        fix_issues(report)

    # 2. Commit work
    git_commit(f"feat: {feature_id}")

    # 3. Update progress
    update_progress_file(feature_id)

    # 4. Final verification
    assert run_basic_test().passed
```

**Migration**: ⚠️ Complete rewrite needed

---

## 🎯 The Big Picture: From Toolkit → System

### Old Approach (Generic Toolkit)

```
┌─────────────────────────────────────┐
│  Generic Context Engineering Patterns │
├─────────────────────────────────────┤
│  • Rolling Window                    │
│  • RAG Injection                     │
│  • PII Sanitization                  │
│  • Tool Selection                    │
│  • Persona Switching                 │
│  • ... etc                           │
└─────────────────────────────────────┘
         ↓
   Use in any agent
```

### New Approach (Integrated System)

```
┌───────────────────────────────────────────────┐
│  GOAL: Build Web App Across Multiple Sessions │
├───────────────────────────────────────────────┤
│  Initializer Agent (Session 1)                │
│    ├─ Feature List Manager                    │
│    └─ Git Progress Tracker                    │
│                                                │
│  Coding Agent (Sessions 2-N)                  │
│    ├─ State Recovery (start of session)       │
│    ├─ Incremental Work Controller             │
│    ├─ Rolling Window (during work)            │
│    ├─ Tool Output Trimmer (testing)           │
│    ├─ Test Validator (verification)           │
│    └─ Clean State Committer (end of session)  │
└───────────────────────────────────────────────┘
         ↓
   Complete working system
```

---

## ✅ Migration Checklist

For each old scenario you've implemented:

- [ ] **Scenarios 1, 2, 3**: Minor updates only

  - [ ] Update examples to reference long-running agent context
  - [ ] Update test cases if needed
  - [ ] ✅ Core implementation can stay

- [ ] **Scenario 4 (RAG → Feature List)**: Complete rewrite

  - [ ] Read new scenario document
  - [ ] Implement JSON-based feature tracking
  - [ ] Create new tests for feature selection/updates
  - [ ] ❌ Old code is not reusable

- [ ] **Scenario 5 (PII → Git Tracker)**: Complete rewrite

  - [ ] Read new scenario document
  - [ ] Implement Git commit automation
  - [ ] Implement progress file management
  - [ ] ❌ Old code is not reusable

- [ ] **Scenario 6 (State Extract → Recovery)**: Major revision

  - [ ] Read new scenario document
  - [ ] Expand to multi-source recovery
  - [ ] Add git log parsing
  - [ ] ⚠️ Some concepts reusable, but scope is much larger

- [ ] **Scenarios 7, 8, 9**: Complete rewrites
  - [ ] Read new scenario documents
  - [ ] Implement from scratch
  - [ ] ❌ Old code is not reusable

---

## 🚀 Getting Started with New Structure

### Step 1: Understand the Main Scenario

Read [`scenarios/MAIN_SCENARIO.md`](ax_advanced_class/scenarios/MAIN_SCENARIO.md) first to understand the big picture.

### Step 2: Follow the 7-Week Roadmap

Work through scenarios in order:

- Week 1-2: Scenarios 1, 2, 3
- Week 3-4: Scenarios 4, 5, 6
- Week 5-6: Scenarios 7, 8, 9
- Week 7: Integration

### Step 3: Test as You Go

Each scenario has corresponding tests in `tests/test_N_*.py`.

### Step 4: Build the Full System

In Week 7, integrate all components into working Initializer and Coding agents.

---

## 💡 FAQ

### Q: Can I still use the old scenarios?

**A**: The old files are deleted, but the concepts remain useful in other contexts. For this course, use the new structure.

### Q: Why such big changes?

**A**: The new structure is based on real production experience (Anthropic's article) and provides a more cohesive learning experience.

### Q: Do I need to start over?

**A**: Scenarios 1, 2, 3 need minimal changes. Scenarios 4-9 require new implementations, but this is part of the learning process.

### Q: Where can I learn more?

**A**: Read the [Anthropic article](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) and the new scenario documents.

---

**Questions? Check [`CHANGES.md`](CHANGES.md) for more details!**
