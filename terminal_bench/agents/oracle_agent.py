from typing import Optional, List
from .base import BaseAgent


class OracleAgent(BaseAgent):
    """
    An agent that executes reference golden solutions step-by-step.
    Used for task authoring verification, ensuring every task is 100% solvable.
    """

    def __init__(self, reference_commands: Optional[List[str]] = None, name: str = "OracleAgent"):
        super().__init__(name=name)
        self.commands = reference_commands or []
        self._current_step = 0

    def set_solution(self, solution_script: str):
        # Filter non-empty, non-comment lines
        lines = [
            line.strip()
            for line in solution_script.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.commands = lines
        self._current_step = 0

    def act(self, observation: str) -> Optional[str]:
        if self._current_step < len(self.commands):
            cmd = self.commands[self._current_step]
            self._current_step += 1
            return cmd
        return "EXIT"

    def reset(self):
        self._current_step = 0
