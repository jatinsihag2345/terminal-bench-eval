import time
from typing import List, Optional

from .models import Task, EvaluationResult, ExecutionTrace, BenchmarkSummary
from .docker_env import SandboxEnvironment
from .evaluator import DeterministicEvaluator
from ..agents.base import BaseAgent


class BenchmarkRunner:
    """
    Orchestrates the execution of a suite of terminal benchmark tasks against an agent.
    """

    def __init__(self, evaluator: Optional[DeterministicEvaluator] = None, use_docker: bool = False):
        self.evaluator = evaluator or DeterministicEvaluator()
        self.use_docker = use_docker

    def run_task(self, task: Task, agent: BaseAgent) -> EvaluationResult:
        """
        Runs a single task from setup to agent execution and deterministic grading.
        """
        sandbox = SandboxEnvironment(task_id=task.id, use_docker=self.use_docker)
        trace = ExecutionTrace(task_id=task.id, agent_id=agent.name)

        try:
            # 1. Setup phase
            setup_success = sandbox.setup(task.setup_script, task.environment_variables)
            if not setup_success:
                return EvaluationResult(
                    task_id=task.id,
                    agent_id=agent.name,
                    passed=False,
                    score=0.0,
                    steps_taken=0,
                    duration_s=0.0,
                    trace=trace,
                    failure_reason="Task environment setup failed."
                )

            # 2. Agent Execution Loop
            start_time = time.time()
            agent.reset()
            observation = f"Task Description: {task.description}\nAvailable tools: Bash shell."

            for step in range(1, task.max_steps + 1):
                if time.time() - start_time > task.timeout_seconds:
                    trace.error = "Task timed out before agent completed."
                    break

                # Get agent's next bash command
                command = agent.act(observation)
                if command is None or command.strip() == "EXIT":
                    trace.completed = True
                    break

                # Execute in sandbox
                exit_code, stdout, stderr, duration_ms = sandbox.execute_command(command)
                from .models import AgentAction
                action = AgentAction(
                    step=step,
                    command=command,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    duration_ms=duration_ms
                )
                trace.actions.append(action)

                # Feed observation back to agent
                observation = f"Exit code: {exit_code}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"

            trace.total_duration_s = time.time() - start_time

            # 3. Deterministic Evaluation
            eval_result = self.evaluator.evaluate(task, sandbox, trace)
            return eval_result

        finally:
            sandbox.teardown()

    def run_suite(self, tasks: List[Task], agent: BaseAgent) -> BenchmarkSummary:
        """
        Runs all tasks in the suite and aggregates summary metrics.
        """
        results: List[EvaluationResult] = []
        for task in tasks:
            print(f"Running task: {task.id} - {task.title}")
            res = self.run_task(task, agent)
            results.append(res)
            status_text = "PASSED" if res.passed else "FAILED"
            print(f" -> Result: {status_text} (Steps: {res.steps_taken}, Score: {res.score:.2f})\n")

        passed_count = sum(1 for r in results if r.passed)
        total = len(tasks)
        pass_at_1 = (passed_count / total) * 100.0 if total > 0 else 0.0
        avg_steps = sum(r.steps_taken for r in results) / total if total > 0 else 0.0
        avg_duration = sum(r.duration_s for r in results) / total if total > 0 else 0.0

        summary = BenchmarkSummary(
            agent_id=agent.name,
            total_tasks=total,
            passed_tasks=passed_count,
            pass_at_1=pass_at_1,
            avg_steps_per_task=avg_steps,
            avg_duration_s=avg_duration,
            task_results=results
        )

        self._print_summary_table(summary)
        return summary

    def _print_summary_table(self, summary: BenchmarkSummary):
        print(f"\n==================== TerminalBench Results: {summary.agent_id} ====================")
        print(f"{'Task ID':<35} {'Status':<10} {'Steps':<8} {'Score':<8} {'Notes'}")
        print("-" * 80)
        for r in summary.task_results:
            status = "PASS" if r.passed else "FAIL"
            notes = r.failure_reason if r.failure_reason else "Verified"
            print(f"{r.task_id:<35} {status:<10} {r.steps_taken:<8} {r.score:<8.2f} {notes[:30]}")
        print("-" * 80)
        print(f"Pass@1: {summary.pass_at_1:.1f}% | Total: {summary.passed_tasks}/{summary.total_tasks}\n")
