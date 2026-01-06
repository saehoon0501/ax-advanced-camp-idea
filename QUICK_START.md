# 🚀 Quick Start Guide

## Welcome to Long-Running AI Agents!

This project teaches you how to build AI agents that can work on complex projects across multiple sessions, based on [Anthropic's production experience](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).

---

## 📖 Read These First (5 minutes)

```
1. README.md                          (Project overview)
   ↓
2. scenarios/MAIN_SCENARIO.md         (What you'll build)
   ↓
3. scenarios/README.md                (Scenarios overview)
```

---

## 🎯 The Main Goal

Build a **Long-Running Web App Builder** that:

- Takes high-level requirements ("Build a blog")
- Breaks them into 200+ testable features
- Implements them incrementally across many sessions
- Maintains state using Git and progress files
- Tests everything end-to-end
- Delivers a working web application

---

## 🏗️ The System You'll Build

```
┌─────────────────────────────────────────────────────────┐
│  User Request: "Build a clone of claude.ai"             │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │   INITIALIZER AGENT           │
         │   (Session 1)                 │
         ├───────────────────────────────┤
         │ ✓ Create feature_list.json    │
         │   (200+ structured features)  │
         │ ✓ Initialize Git repo         │
         │ ✓ Setup progress tracking     │
         │ ✓ Create init.sh script       │
         └────────────┬──────────────────┘
                      │
                      │ Hands off to...
                      ▼
         ┌───────────────────────────────┐
         │   CODING AGENT                │
         │   (Sessions 2, 3, 4, ... N)   │
         ├───────────────────────────────┤
         │                               │
         │ Start of Session:             │
         │   1. Read git log             │
         │   2. Read progress file       │
         │   3. Select ONE feature       │
         │   4. Verify app works         │
         │                               │
         │ During Session:               │
         │   5. Implement feature        │
         │   6. Write tests              │
         │   7. Run E2E tests            │
         │                               │
         │ End of Session:               │
         │   8. Commit work              │
         │   9. Update progress          │
         │  10. Ensure clean state       │
         │                               │
         └────────────┬──────────────────┘
                      │
                      │ Repeat until...
                      ▼
         ┌───────────────────────────────┐
         │   All 200+ features complete! │
         │   🎉 Working web app!         │
         └───────────────────────────────┘
```

---

## 📚 9 Learning Modules (7 Weeks)

### Week 1-2: Session Context Management

Build the foundation for managing conversation context.

| Day | Scenario                   | What You'll Learn                            | File                       |
| --- | -------------------------- | -------------------------------------------- | -------------------------- |
| 1-2 | **1. Rolling Window**      | Keep recent messages, preserve system prompt | `1.rolling_window.md`      |
| 3-4 | **2. Auto Summarizer**     | Compress old history without losing meaning  | `2.auto_summarizer.md`     |
| 5-6 | **3. Tool Output Trimmer** | Trim verbose tool outputs (browser logs)     | `3.tool_output_trimmer.md` |

### Week 3-4: State Persistence & Recovery

Learn how to save and restore state across sessions.

| Day | Scenario                    | What You'll Learn                        | File                        |
| --- | --------------------------- | ---------------------------------------- | --------------------------- |
| 1-2 | **4. Feature List Manager** | Track 200+ features in structured JSON   | `4.feature_list_manager.md` |
| 3-4 | **5. Git Progress Tracker** | Use Git as persistent memory             | `5.git_progress_tracker.md` |
| 5-6 | **6. State Recovery Agent** | Quickly recover context at session start | `6.state_recovery.md`       |

### Week 5-6: Quality Assurance

Ensure every feature works and sessions end cleanly.

| Day | Scenario                | What You'll Learn                        | File                               |
| --- | ----------------------- | ---------------------------------------- | ---------------------------------- |
| 1-2 | **7. Incremental Work** | One feature at a time, no "one-shotting" | `7.incremental_work_controller.md` |
| 3-4 | **8. Test Validator**   | Browser automation E2E testing           | `8.test_validator.md`              |
| 5-6 | **9. Clean State**      | End sessions with working app            | `9.clean_state_committer.md`       |

### Week 7: Integration

Put it all together into a working system.

| Day | What You'll Build                               |
| --- | ----------------------------------------------- |
| 1-2 | Initializer Agent (scenarios 4, 5)              |
| 3-4 | Coding Agent (scenarios 1-9)                    |
| 5   | Integration testing                             |
| 6-7 | Real project: Build a Todo App / Blog / Chat UI |

---

## 💻 Installation (5 minutes)

```bash
# Clone (if not done)
cd ax-incubation-advanced-camp-idea-dexter

# Install dependencies (choose one)

# Option A: Using uv (recommended)
uv sync

# Option B: Using pip
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Install browser automation (for Week 5-6)
playwright install chromium
```

---

## 🏃 Run Your First Scenario (10 minutes)

### Step 1: Read the scenario

```bash
# Open in your editor
code ax_advanced_class/scenarios/1.rolling_window.md

# Or read in terminal
cat ax_advanced_class/scenarios/1.rolling_window.md
```

### Step 2: Look at the test

```bash
# See what's expected
cat tests/test_1_rolling_window.py
```

### Step 3: Run the test (it will fail initially)

```bash
pytest tests/test_1_rolling_window.py -v
```

### Step 4: Implement the solution

```bash
# Edit this file
code ax_advanced_class/rolling_window_middleware.py
```

### Step 5: Test again until it passes

```bash
pytest tests/test_1_rolling_window.py -v
```

### 🎉 Repeat for all 9 scenarios!

---

## 🎓 Learning Approach

### For Each Scenario:

1. **Read** the scenario document (15-30 min)

   - Understand the problem
   - Learn the principles
   - Study the examples

2. **Plan** your implementation (15 min)

   - Sketch the algorithm
   - Identify edge cases
   - Review test requirements

3. **Code** the solution (1-2 hours)

   - Write clean, readable code
   - Add comments for complex logic
   - Handle failure modes

4. **Test** thoroughly (30 min)

   - Run provided tests
   - Add your own test cases
   - Test failure modes

5. **Review** and refine (15 min)
   - Can you simplify?
   - Are edge cases handled?
   - Is it production-ready?

**Total per scenario**: ~3-4 hours  
**Total course**: ~30-35 hours over 7 weeks

---

## 📊 Track Your Progress

```bash
# Check which scenarios you've completed
ls ax_advanced_class/scenarios/*.md

# Run all tests to see progress
pytest tests/ -v

# See git history (after Week 3)
git log --oneline --graph
```

### Progress Checklist

#### Week 1-2: Context Management

- [ ] Scenario 1: Rolling Window
- [ ] Scenario 2: Auto Summarizer
- [ ] Scenario 3: Tool Output Trimmer

#### Week 3-4: State Persistence

- [ ] Scenario 4: Feature List Manager
- [ ] Scenario 5: Git Progress Tracker
- [ ] Scenario 6: State Recovery

#### Week 5-6: Quality Assurance

- [ ] Scenario 7: Incremental Work
- [ ] Scenario 8: Test Validator
- [ ] Scenario 9: Clean State

#### Week 7: Integration

- [ ] Initializer Agent
- [ ] Coding Agent
- [ ] Real project deployed

---

## 🆘 Getting Help

### Stuck on a scenario?

1. Re-read the "Implementation Guide" section
2. Check the "Failure Modes" section
3. Look at similar test cases
4. Review the [Anthropic article](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### Confused about the big picture?

- Read [`scenarios/MAIN_SCENARIO.md`](ax_advanced_class/scenarios/MAIN_SCENARIO.md)
- Review the architecture diagrams
- Trace through a session workflow

### Migration from old structure?

- See [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md)

---

## 🎯 Success Criteria

You'll know you've mastered long-running agents when you can:

✅ Explain why agents need two different modes (Initializer vs Coding)  
✅ Implement state persistence using Git and progress files  
✅ Enforce incremental development (one feature at a time)  
✅ Validate features with end-to-end tests  
✅ Ensure clean handoffs between sessions  
✅ Build a working web app across multiple agent sessions

---

## 🚀 Ready to Start?

```bash
# 1. Read the main scenario (10 min)
open ax_advanced_class/scenarios/MAIN_SCENARIO.md

# 2. Start Scenario 1 (3-4 hours)
open ax_advanced_class/scenarios/1.rolling_window.md
code ax_advanced_class/rolling_window_middleware.py
pytest tests/test_1_rolling_window.py -v

# 3. Keep going! 🎉
```

---

## 📚 Essential Reading

| Order | Document                                                                                               | Time   | Purpose             |
| ----- | ------------------------------------------------------------------------------------------------------ | ------ | ------------------- |
| 1     | [`README.md`](README.md)                                                                               | 5 min  | Project overview    |
| 2     | [`scenarios/MAIN_SCENARIO.md`](ax_advanced_class/scenarios/MAIN_SCENARIO.md)                           | 15 min | Understand the goal |
| 3     | [`scenarios/1.rolling_window.md`](ax_advanced_class/scenarios/1.rolling_window.md)                     | 20 min | Your first scenario |
| 4     | [Anthropic Article](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | 20 min | Original research   |

---

**Let's build amazing long-running agents! 🤖✨**

_Questions? Check the other guides in this repo!_
