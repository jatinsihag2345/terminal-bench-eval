import pytest
from terminal_bench.core.models import Task, TaskCategory, Difficulty
from terminal_bench.tasks.task_registry import ALL_TASKS, get_task_by_id
from terminal_bench.agents.oracle_agent import OracleAgent
from terminal_bench.core.runner import BenchmarkRunner


def test_task_registry_integrity():
    assert len(ALL_TASKS) >= 8
    task_ids = [t.id for t in ALL_TASKS]
    assert len(task_ids) == len(set(task_ids)), "Task IDs must be unique"
    for task in ALL_TASKS:
        assert task.setup_script.strip(), f"Task {task.id} missing setup script"
        assert task.eval_script.strip(), f"Task {task.id} missing eval script"
        assert task.reference_solution.strip(), f"Task {task.id} missing reference solution"


def test_oracle_agent_task_01():
    task = get_task_by_id("task_01_corrupt_git_head")
    assert task is not None
    agent = OracleAgent()
    agent.set_solution(task.reference_solution)

    runner = BenchmarkRunner(use_docker=False)
    result = runner.run_task(task, agent)
    assert result.passed is True
    assert result.score == 1.0


def test_oracle_agent_task_06():
    task = get_task_by_id("task_06_docker_layer_cache_bust")
    assert task is not None
    agent = OracleAgent()
    agent.set_solution(task.reference_solution)

    runner = BenchmarkRunner(use_docker=False)
    result = runner.run_task(task, agent)
    assert result.passed is True
    assert result.score == 1.0
