from typing import List, Dict, Optional
from ..core.models import Task, TaskCategory, Difficulty


TASK_01 = Task(
    id="task_01_corrupt_git_head",
    title="Recover Orphaned Commits and Repair Detached HEAD",
    description="A git rebase was abruptly interrupted, leaving the repository in a detached HEAD state with 2 orphaned commits containing critical bugfixes not reachable from 'main'. Re-attach the orphaned commits onto main without merge conflicts, ensuring git status is clean.",
    category=TaskCategory.GIT_SCM,
    difficulty=Difficulty.MEDIUM,
    max_steps=10,
    timeout_seconds=120,
    setup_script="""
git init
git config user.name "Test User"
git config user.email "test@example.com"
echo "v1.0" > version.txt
git add version.txt
git commit -m "Initial commit"
git checkout -b feature
echo "fix auth bug" >> auth.py
git add auth.py
git commit -m "Fix authentication bypass"
echo "fix token leak" >> auth.py
git add auth.py
git commit -m "Patch token leakage"
ORPHAN_HASH=$(git rev-parse HEAD)
git checkout --detach HEAD~2
git branch -D feature
echo "$ORPHAN_HASH" > .git/ORPHAN_REF
""",
    eval_script="""
# Check that HEAD is on branch main or master
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ]; then
    echo "HEAD is not on branch main (is on $BRANCH)"
    exit 1
fi

# Check that auth.py exists and contains both fixes
if [ ! -f "auth.py" ]; then
    echo "auth.py does not exist"
    exit 1
fi

grep -q "Fix authentication bypass" <(git log --oneline) || { echo "Missing commit 1"; exit 1; }
grep -q "Patch token leakage" <(git log --oneline) || { echo "Missing commit 2"; exit 1; }

# Working tree must be clean
if ! git diff-index --quiet HEAD --; then
    echo "Working tree is dirty"
    exit 1
fi
echo "Task 01 Passed Successfully"
exit 0
""",
    reference_solution="""
git checkout -B main
ORPHAN_HASH=$(cat .git/ORPHAN_REF) && git cherry-pick $ORPHAN_HASH~1 $ORPHAN_HASH
EXIT
"""
)

TASK_02 = Task(
    id="task_02_systemd_socket_deadlock",
    title="Fix Socket Server TIME_WAIT Deadlock and Bind Error",
    description="The custom backend server fails to start on port 8089 with 'OSError: [Errno 98] Address already in use'. Investigate server.py, fix the socket option to reuse port/address (SO_REUSEADDR), and verify that server.py launches cleanly and responds to healthcheck HTTP requests.",
    category=TaskCategory.SYSADMIN,
    difficulty=Difficulty.MEDIUM,
    max_steps=10,
    timeout_seconds=120,
    setup_script="""
mkdir -p /tmp/socket_task
cat << 'EOF' > server.py
import socket
import sys

def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # BUG: SO_REUSEADDR is missing, leading to port bind lock
    server.bind(("127.0.0.1", 8089))
    server.listen(5)
    print("SERVER_RUNNING", flush=True)
    server.close()

if __name__ == "__main__":
    run_server()
EOF
""",
    eval_script="""
# Check that SO_REUSEADDR is enabled in server.py
grep -q "SO_REUSEADDR" server.py || { echo "SO_REUSEADDR not configured in server.py"; exit 1; }
python3 server.py | grep -q "SERVER_RUNNING" || { echo "Server failed to launch"; exit 1; }
echo "Task 02 Passed Successfully"
exit 0
""",
    reference_solution="""
python3 -c 'content = open("server.py").read().replace("server.bind", "server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\\n    server.bind"); open("server.py", "w").write(content)'
EXIT
"""
)

TASK_03 = Task(
    id="task_03_python_c_extension_abi",
    title="Fix Python C Extension ABI Incompatibility & Header Conflict",
    description="A legacy C extension 'fastmath' fails to build with gcc due to a missing Python.h include path and deprecated PyUnicode_GET_SIZE call in Python 3.10+. Patch fastmath.c to use PyUnicode_GET_LENGTH and compile the shared object fastmath.so.",
    category=TaskCategory.BUILD_SYSTEMS,
    difficulty=Difficulty.HARD,
    max_steps=12,
    timeout_seconds=180,
    setup_script="""
cat << 'EOF' > fastmath.c
#include <stdio.h>

long get_string_size(const char* s, int legacy_flag) {
    if (legacy_flag == 1) {
        return -1;
    }
    long len = 0;
    while(s[len] != '\\0') len++;
    return len;
}

int main() {
    printf("FAST_MATH_OK:%ld\\n", get_string_size("antigravity", 1));
    return 0;
}
EOF
gcc -O2 fastmath.c -o fastmath_bin
""",
    eval_script="""
gcc -O2 fastmath.c -o fastmath_bin
OUTPUT=$(./fastmath_bin)
if [ "$OUTPUT" != "FAST_MATH_OK:11" ]; then
    echo "Output mismatch: $OUTPUT"
    exit 1
fi
echo "Task 03 Passed Successfully"
exit 0
""",
    reference_solution="""
python3 -c 'content = open("fastmath.c").read().replace("get_string_size(\\"antigravity\\", 1)", "get_string_size(\\"antigravity\\", 0)"); open("fastmath.c", "w").write(content)'
gcc -O2 fastmath.c -o fastmath_bin
EXIT
"""
)

TASK_04 = Task(
    id="task_04_nginx_sni_reverse_proxy",
    title="Resolve Upstream SSL Handshake Failure in Reverse Proxy",
    description="The reverse proxy configuration in nginx_mock.conf causes upstream HTTPS handshake errors because proxy_ssl_server_name is disabled and Host headers are dropped. Fix the configuration file so proxy_ssl_server_name is on and Host header is passed properly.",
    category=TaskCategory.NETWORKING,
    difficulty=Difficulty.MEDIUM,
    max_steps=8,
    timeout_seconds=120,
    setup_script="""
cat << 'EOF' > nginx_mock.conf
server {
    listen 80;
    server_name api.internal.local;

    location /v1/ {
        proxy_pass https://upstream.secure.cloud;
        proxy_ssl_server_name off;
    }
}
EOF
""",
    eval_script="""
grep -q "proxy_ssl_server_name on;" nginx_mock.conf || { echo "proxy_ssl_server_name is not on"; exit 1; }
grep -q "proxy_set_header Host" nginx_mock.conf || { echo "Host header not set"; exit 1; }
echo "Task 04 Passed Successfully"
exit 0
""",
    reference_solution="""
python3 -c 'content = open("nginx_mock.conf").read().replace("proxy_ssl_server_name off;", "proxy_ssl_server_name on;\\n        proxy_set_header Host $host;"); open("nginx_mock.conf", "w").write(content)'
EXIT
"""
)

TASK_05 = Task(
    id="task_05_sqlite_wal_checkpoint_lock",
    title="Repair Locked SQLite WAL File and Perform Checkpoint",
    description="An application crashed leaving an uncommitted write-ahead log (test.db-wal) with an exclusive lock. Run the sqlite3 recovery command or python script to perform a TRUNCATE checkpoint and restore database read/write access.",
    category=TaskCategory.DATABASE_STORAGE,
    difficulty=Difficulty.MEDIUM,
    max_steps=10,
    timeout_seconds=120,
    setup_script="""
python3 -c "
import sqlite3
conn = sqlite3.connect('data.db')
conn.execute('PRAGMA journal_mode=WAL;')
conn.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);')
conn.executemany('INSERT INTO users (name) VALUES (?);', [('Alice',), ('Bob',)])
conn.commit()
conn.close()
"
touch data.db-wal
""",
    eval_script="""
python3 -c "
import sqlite3
conn = sqlite3.connect('data.db')
cur = conn.cursor()
cur.execute('PRAGMA wal_checkpoint(TRUNCATE);')
cur.execute('INSERT INTO users (name) VALUES (?);', ('Charlie',))
conn.commit()
cur.execute('SELECT COUNT(*) FROM users;')
count = cur.fetchone()[0]
if count != 3:
    raise ValueError(f'Expected 3 users, got {count}')
conn.close()
" || { echo "Database query failed"; exit 1; }
echo "Task 05 Passed Successfully"
exit 0
""",
    reference_solution="""
python3 -c 'import sqlite3; conn = sqlite3.connect("data.db"); conn.execute("PRAGMA wal_checkpoint(TRUNCATE);"); conn.close()'
EXIT
"""
)

TASK_06 = Task(
    id="task_06_docker_layer_cache_bust",
    title="Optimize Multi-Stage Dockerfile Layer Caching",
    description="Inspect Dockerfile.app. The build time is excessively slow because source code is copied before dependencies, invalidating the pip install cache on every edit. Refactor Dockerfile.app to copy requirements.txt first, run pip install, and then copy the remaining source files.",
    category=TaskCategory.BUILD_SYSTEMS,
    difficulty=Difficulty.EASY,
    max_steps=8,
    timeout_seconds=120,
    setup_script="""
cat << 'EOF' > Dockerfile.app
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
EOF
""",
    eval_script=r"""
# Assert that requirements.txt is copied before COPY . .
FIRST_COPY=$(grep -n "COPY requirements.txt" Dockerfile.app | cut -d: -f1)
SECOND_COPY=$(grep -n "COPY \. \." Dockerfile.app | cut -d: -f1)
if [ -z "$FIRST_COPY" ]; then
    echo "COPY requirements.txt not found"; exit 1
fi
if [ -z "$SECOND_COPY" ]; then
    echo "COPY . . not found"; exit 1
fi
if [ "$FIRST_COPY" -ge "$SECOND_COPY" ]; then
    echo "COPY requirements.txt must precede COPY . ."; exit 1
fi
echo "Task 06 Passed Successfully"
exit 0
""",
    reference_solution=r"""
printf "FROM python:3.10-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD [\"python\", \"app.py\"]\n" > Dockerfile.app
EXIT
"""
)

TASK_07 = Task(
    id="task_07_cron_path_env_isolation",
    title="Fix Cron Job Missing Environment & Silent Failure",
    description="A cron backup script backup.sh fails silently when executed by crond because standard commands (pg_dump, aws, tar) are not in cron's minimal /usr/bin:/bin default PATH. Fix backup.sh by adding an explicit PATH export and strict bash error handling (set -euo pipefail).",
    category=TaskCategory.SYSADMIN,
    difficulty=Difficulty.EASY,
    max_steps=6,
    timeout_seconds=120,
    setup_script="""
cat << 'EOF' > backup.sh
tar -czf backup.tar.gz data/
echo "BACKUP_DONE"
EOF
""",
    eval_script="""
grep -q "set -euo pipefail" backup.sh || { echo "Missing set -euo pipefail"; exit 1; }
grep -q "PATH=" backup.sh || { echo "Missing explicit PATH definition"; exit 1; }
echo "Task 07 Passed Successfully"
exit 0
""",
    reference_solution="""
python3 -c 'content = open("backup.sh").read(); open("backup.sh", "w").write("#!/bin/bash\\nset -euo pipefail\\nexport PATH=/usr/local/bin:/usr/bin:/bin\\n" + content)'
EXIT
"""
)

TASK_08 = Task(
    id="task_08_dns_search_domain_leak",
    title="Fix DNS Search Domain Loop and Resolution Timeout",
    description="The DNS configuration in resolv.conf has ndots:5 with 4 search domains, causing single-label host resolution to generate 5 sequential NXDOMAIN timeouts before trying the authoritative domain. Fix resolv.conf to set ndots:1 and order search domains cleanly.",
    category=TaskCategory.NETWORKING,
    difficulty=Difficulty.MEDIUM,
    max_steps=8,
    timeout_seconds=120,
    setup_script="""
cat << 'EOF' > resolv.conf
nameserver 8.8.8.8
search corp.internal staging.internal dev.internal prod.internal
options ndots:5 timeout:2 attempts:3
EOF
""",
    eval_script="""
grep -q "options ndots:1" resolv.conf || { echo "ndots not set to 1"; exit 1; }
echo "Task 08 Passed Successfully"
exit 0
""",
    reference_solution="""
python3 -c 'content = open("resolv.conf").read().replace("ndots:5", "ndots:1"); open("resolv.conf", "w").write(content)'
EXIT
"""
)


ALL_TASKS: List[Task] = [
    TASK_01,
    TASK_02,
    TASK_03,
    TASK_04,
    TASK_05,
    TASK_06,
    TASK_07,
    TASK_08
]


def get_task_by_id(task_id: str) -> Optional[Task]:
    for t in ALL_TASKS:
        if t.id == task_id:
            return t
    return None
