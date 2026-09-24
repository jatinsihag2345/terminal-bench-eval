import sys
import argparse
from .tasks.task_registry import ALL_TASKS, get_task_by_id
from .agents.oracle_agent import OracleAgent
from .agents.llm_agent import LLMAgent
from .core.runner import BenchmarkRunner


def list_tasks():
    print(f"\n{'Task ID':<35} {'Category':<22} {'Difficulty':<10} {'Steps':<6} Title")
    print("=" * 95)
    for task in ALL_TASKS:
        print(f"{task.id:<35} {task.category.value:<22} {task.difficulty.value:<10} {task.max_steps:<6} {task.title}")
    print("=" * 95 + "\n")


def test_oracle(task_id: str = None):
    tasks_to_run = [get_task_by_id(task_id)] if task_id else ALL_TASKS
    if not tasks_to_run or tasks_to_run[0] is None:
        print(f"Error: Task '{task_id}' not found.")
        sys.exit(1)

    runner = BenchmarkRunner(use_docker=False)
    for task in tasks_to_run:
        agent = OracleAgent()
        if task.reference_solution:
            agent.set_solution(task.reference_solution)
        res = runner.run_task(task, agent)
        if not res.passed:
            print(f"Oracle verification failed for {task.id}: {res.failure_reason}")
            sys.exit(1)

    print("All tasks successfully verified with OracleAgent!")


def run_benchmark(model: str = "gpt-4o", task_id: str = None, docker: bool = False):
    tasks_to_run = [get_task_by_id(task_id)] if task_id else ALL_TASKS
    if not tasks_to_run or tasks_to_run[0] is None:
        print(f"Error: Task '{task_id}' not found.")
        sys.exit(1)

    agent = LLMAgent(model_name=model)
    runner = BenchmarkRunner(use_docker=docker)
    summary = runner.run_suite(tasks_to_run, agent)
    return summary


def main():
    parser = argparse.ArgumentParser(description="TerminalBench: CLI & OS Benchmark Suite for Autonomous Agents")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to run")

    # list-tasks
    subparsers.add_parser("list-tasks", help="List all benchmark tasks")

    # test-oracle
    oracle_parser = subparsers.add_parser("test-oracle", help="Verify tasks using reference oracle agent")
    oracle_parser.add_argument("--task-id", default=None, help="Specific task ID to verify")

    # run
    run_parser = subparsers.add_parser("run", help="Run benchmark against an agent")
    run_parser.add_argument("--model", default="gpt-4o", help="Model name (e.g. gpt-4o, claude-3-5-sonnet)")
    run_parser.add_argument("--task-id", default=None, help="Specific task ID to run")
    run_parser.add_argument("--docker", action="store_true", help="Run inside Docker containers")

    args = parser.parse_args()

    if args.command == "list-tasks":
        list_tasks()
    elif args.command == "test-oracle":
        test_oracle(args.task_id)
    elif args.command == "run":
        run_benchmark(args.model, args.task_id, args.docker)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
