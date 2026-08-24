import os
import shutil
import tempfile
import subprocess
import time
from typing import Tuple, Optional, Dict


class SandboxEnvironment:
    """
    Isolated execution environment for benchmark tasks.
    Supports both native Docker sandboxes and isolated temporary chroot/directory environments.
    """

    def __init__(self, task_id: str, image: str = "ubuntu:22.04", use_docker: bool = False):
        self.task_id = task_id
        self.image = image
        self.use_docker = use_docker
        self.container_id: Optional[str] = None
        self.temp_workdir: Optional[str] = None
        self._docker_client = None

        if self.use_docker:
            try:
                import docker
                self._docker_client = docker.from_env()
            except Exception:
                # Fallback to local sandbox if docker daemon is unavailable
                self.use_docker = False

    def setup(self, setup_script: str, env_vars: Optional[Dict[str, str]] = None) -> bool:
        """Sets up the initial broken environment state."""
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        if self.use_docker and self._docker_client:
            return self._setup_docker(setup_script, env)
        else:
            return self._setup_local(setup_script, env)

    def _setup_local(self, setup_script: str, env: Dict[str, str]) -> bool:
        self.temp_workdir = tempfile.mkdtemp(prefix=f"termbench_{self.task_id}_")
        script_path = os.path.join(self.temp_workdir, "_setup.sh")
        with open(script_path, "w") as f:
            f.write("#!/bin/bash\nset -e\n" + setup_script)
        os.chmod(script_path, 0o755)

        res = subprocess.run(
            ["/bin/bash", script_path],
            cwd=self.temp_workdir,
            env=env,
            capture_output=True,
            text=True
        )
        return res.returncode == 0

    def _setup_docker(self, setup_script: str, env: Dict[str, str]) -> bool:
        # Start container in detached mode
        container = self._docker_client.containers.run(
            self.image,
            command="tail -f /dev/null",
            detach=True,
            environment=env,
            network_mode="bridge"
        )
        self.container_id = container.id
        exit_code, output = container.exec_run(f"/bin/bash -c '{setup_script}'")
        return exit_code == 0

    def execute_command(self, command: str, timeout: int = 30) -> Tuple[int, str, str, float]:
        """
        Executes a bash command in the sandbox.
        Returns: (exit_code, stdout, stderr, duration_ms)
        """
        start = time.time()
        if self.use_docker and self.container_id:
            try:
                container = self._docker_client.containers.get(self.container_id)
                exec_res = container.exec_run(["/bin/bash", "-c", command], demux=True)
                duration_ms = (time.time() - start) * 1000.0
                stdout = exec_res.output[0].decode("utf-8", errors="replace") if exec_res.output[0] else ""
                stderr = exec_res.output[1].decode("utf-8", errors="replace") if exec_res.output[1] else ""
                return exec_res.exit_code, stdout, stderr, duration_ms
            except Exception as e:
                duration_ms = (time.time() - start) * 1000.0
                return 1, "", str(e), duration_ms
        else:
            try:
                res = subprocess.run(
                    ["/bin/bash", "-c", command],
                    cwd=self.temp_workdir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                duration_ms = (time.time() - start) * 1000.0
                return res.returncode, res.stdout, res.stderr, duration_ms
            except subprocess.TimeoutExpired:
                duration_ms = (time.time() - start) * 1000.0
                return 124, "", "Command timed out", duration_ms
            except Exception as e:
                duration_ms = (time.time() - start) * 1000.0
                return 1, "", str(e), duration_ms

    def teardown(self):
        """Cleans up the sandbox container or temporary directory."""
        if self.use_docker and self.container_id:
            try:
                container = self._docker_client.containers.get(self.container_id)
                container.stop(timeout=1)
                container.remove(force=True)
            except Exception:
                pass
            self.container_id = None

        if self.temp_workdir and os.path.exists(self.temp_workdir):
            try:
                shutil.rmtree(self.temp_workdir, ignore_errors=True)
            except Exception:
                pass
            self.temp_workdir = None
