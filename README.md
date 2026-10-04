# 🖥️ TerminalBench-Eval

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue)]()
[![Docker](https://img.shields.io/badge/Docker-Sandboxed-2496ED?logo=docker)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)]()
[![Leaderboard](https://img.shields.io/badge/Leaderboard-Top%20Models-orange)]()

**A rigorous, sandboxed CLI and OS benchmark harness for evaluating autonomous coding and sysadmin agents.**

TerminalBench-Eval measures how well frontier language models can solve complex, multi-step Linux engineering problems—spanning corrupted Git states, network proxy deadlocks, ABI header conflicts, and database lockouts—with **deterministic, reproducible verification**.

---

## 🎯 Benchmark Overview

Frontier models often score high on isolated coding benchmarks (HumanEval, MBPP) but struggle in persistent shell environments where they must:
1. Parse unstructured CLI stderr / stdout.
2. Backtrack after executing broken commands.
3. Reason across file descriptors, environment variables, socket states, and kernel cgroups.
4. Adhere to strict non-interactive constraints.

TerminalBench-Eval provides isolated sandboxes (Docker or temporary virtual environments) and grades agent trajectories with deterministic assertions.

```
       ┌────────────────┐
       │ Benchmark Task │
       └───────┬────────┘
               │ (setup_script)
               ▼
   ┌───────────────────────┐
   │ Docker/Local Sandbox  │◄───┐
   │ (Corrupt state built) │    │ Bash Actions (tool loop)
   └───────────┬───────────┘    │
               │ Observation    │
               ▼                │
     ┌──────────────────┐       │
     │ Autonomous Agent ├───────┘
     │ (ReAct / LLM)    │
     └─────────┬────────┘
               │ (EXIT)
               ▼
     ┌──────────────────┐
     │  Deterministic   │
     │ Evaluator (Pytest│
     └─────────┬────────┘
               ▼
     [Pass@1 Score & Report]
```

---

## 🏆 Current Leaderboard (v1.0)

| Rank | Model | Pass@1 (%) | Avg. Steps | Avg. Duration (s) | Cost / Task ($) |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 🥇 | **Claude 3.5 Sonnet** (20241022) | **75.0%** | 5.4 | 42.1s | $0.048 |
| 🥈 | **GPT-4o** (2024-08-06) | **62.5%** | 6.8 | 48.7s | $0.036 |
| 🥉 | **DeepSeek-V3** | **62.5%** | 7.1 | 54.2s | $0.010 |
| 4 | **Gemini 1.5 Pro** | **50.0%** | 8.0 | 61.0s | $0.027 |
| 5 | **Llama-3.1-70B-Instruct** | **37.5%** | 9.5 | 75.3s | $0.015 |

---

## 📋 Task Suite Taxonomy

| Task ID | Domain | Difficulty | Max Steps | Description |
| :--- | :--- | :---: | :---: | :--- |
| `task_01_corrupt_git_head` | Git / SCM | **Medium** | 10 | Recover orphaned bugfix commits after an aborted rebase and restore clean HEAD. |
| `task_02_systemd_socket_deadlock` | Sysadmin | **Medium** | 10 | Fix `SO_REUSEADDR` TIME_WAIT socket deadlock in backend daemon. |
| `task_03_python_c_extension_abi` | Build / Compilers | **Hard** | 12 | Resolve deprecated Python 3.10+ PEP 590 ABI mismatch in legacy C extension. |
| `task_04_nginx_sni_reverse_proxy` | Networking | **Medium** | 8 | Fix missing `proxy_ssl_server_name` and Host headers causing 502 Bad Gateway. |
| `task_05_sqlite_wal_checkpoint_lock` | Database | **Medium** | 10 | Recover locked SQLite database by forcing a `wal_checkpoint(TRUNCATE)`. |
| `task_06_docker_layer_cache_bust` | Build Systems | **Easy** | 8 | Refactor multi-stage Dockerfile to fix pip dependency cache busting. |
| `task_07_cron_path_env_isolation` | Sysadmin | **Easy** | 6 | Debug cron silent backup failure caused by missing `$PATH` and locale. |
| `task_08_dns_search_domain_leak` | Networking | **Medium** | 8 | Resolve DNS NXDOMAIN retry storms caused by `ndots:5` in `resolv.conf`. |

---

## 🚀 Quickstart

### 1. Installation
```bash
git clone https://github.com/jatinsihag2345/terminal-bench-eval.git
cd terminal-bench-eval
pip install -e .
```

### 2. Verify Benchmark Integrity (Oracle Run)
Verify that all tasks are solvable using the built-in reference oracle solutions:
```bash
terminal-bench test-oracle
```

### 3. List All Tasks
```bash
terminal-bench list-tasks
```

### 4. Evaluate an LLM Agent
Set your API key and evaluate a model:
```bash
export OPENAI_API_KEY="sk-..."
terminal-bench run --model gpt-4o

# Or evaluate Claude 3.5 Sonnet
export ANTHROPIC_API_KEY="sk-ant-..."
terminal-bench run --model claude-3-5-sonnet-20241022
```

---

## 🛠️ Task Schema & Authoring

Tasks are defined declaratively in `terminal_bench/tasks/task_registry.py` with 3 core scripts:

1. **`setup_script`**: Injects the broken environment state.
2. **`eval_script`**: Deterministic test asserting system state (must exit 0 on success).
3. **`reference_solution`**: Golden steps achieving 100% Pass@1 to verify task correctness.

```python
Task(
    id="task_custom_example",
    title="Example Challenge",
    description="Instructions provided to the agent...",
    category=TaskCategory.SYSADMIN,
    difficulty=Difficulty.MEDIUM,
    max_steps=10,
    timeout_seconds=120,
    setup_script="...",
    eval_script="...",
    reference_solution="..."
)
```

---

## 📄 License
Apache License 2.0. Authored by [Jatin Sihag](https://github.com/jatinsihag2345).
