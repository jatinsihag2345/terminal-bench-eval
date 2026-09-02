import time
from .models import Task, ExecutionTrace, EvaluationResult
from .docker_env import SandboxEnvironment


class DeterministicEvaluator:
    """
    Executes post-task deterministic assertions inside the sandbox
    and produces verified evaluation metrics.
    """

    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds

    def evaluate(self, task: Task, sandbox: SandboxEnvironment, trace: ExecutionTrace) -> EvaluationResult:
        """
        Runs the verification script in the sandbox after the agent concludes its actions.
        """
        start_time = time.time()
        exit_code, stdout, stderr, _ = sandbox.execute_command(
            task.eval_script,
            timeout=self.timeout_seconds
        )
        duration_s = time.time() - start_time

        passed = (exit_code == 0)
        failure_reason = None
        if not passed:
            err_msg = stderr.strip() if stderr.strip() else stdout.strip()
            failure_reason = f"Verification script exited with code {exit_code}: {err_msg[:400]}"

        score = 1.0 if passed else 0.0

        return EvaluationResult(
            task_id=task.id,
            agent_id=trace.agent_id,
            passed=passed,
            score=score,
            failure_reason=failure_reason,
            steps_taken=len(trace.actions),
            duration_s=duration_s,
            trace=trace
        )
