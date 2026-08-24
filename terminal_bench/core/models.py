from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


class Difficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    FRONTIER = "Frontier"


class TaskCategory(str, Enum):
    GIT_SCM = "Git / SCM"
    SYSADMIN = "System Administration"
    NETWORKING = "Networking & Protocols"
    BUILD_SYSTEMS = "Build & Compilers"
    DATABASE_STORAGE = "Database & Storage"
    KERNEL_OS = "Kernel & Cgroups"
    SECURITY = "Security & Certificates"


@dataclass
class Task:
    id: str
    title: str
    description: str
    category: TaskCategory
    difficulty: Difficulty
    setup_script: str
    eval_script: str
    max_steps: int = 15
    timeout_seconds: int = 300
    reference_solution: Optional[str] = None
    environment_variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class AgentAction:
    step: int
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExecutionTrace:
    task_id: str
    agent_id: str
    actions: List[AgentAction] = field(default_factory=list)
    total_duration_s: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    completed: bool = False
    error: Optional[str] = None


@dataclass
class EvaluationResult:
    task_id: str
    agent_id: str
    passed: bool
    score: float
    steps_taken: int
    duration_s: float
    trace: ExecutionTrace
    failure_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BenchmarkSummary:
    agent_id: str
    total_tasks: int
    passed_tasks: int
    pass_at_1: float
    avg_steps_per_task: float
    avg_duration_s: float
    benchmark_name: str = "TerminalBench-Eval"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    task_results: List[EvaluationResult] = field(default_factory=list)
