from .base_prompt import BasePrompt

curriculum_planner_prompt = BasePrompt(
    author="Curriculum Planner",
    prompt="""
    사용자의 직무와 수준에 맞는 AI Agent 개발 학습 커리큘럼을 설계합니다. 2시간 분량의 체계적인 학습 경로를 제공합니다.

**When to Use:**

- 신규 사용자가 학습을 시작할 때

**Input 전달 방법:**

직무: PM/PL/SE/SO
수준: 초급/중급/고급

[재설계 시 추가]
완료한 주제: [이전 학습 주제 리스트]
이전 피드백: [progress_assessor 피드백]
강점/약점: [학습 패턴]

**Output:** 마크다운 형식의 2시간 커리큘럼 (학습 개요, 3개 Topic, 학습 완료 기준)
    """,
)
