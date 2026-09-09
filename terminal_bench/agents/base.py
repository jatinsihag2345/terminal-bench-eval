from abc import ABC, abstractmethod
from typing import Optional


class BaseAgent(ABC):
    """
    Abstract interface for agents evaluated on TerminalBench.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def act(self, observation: str) -> Optional[str]:
        """
        Receives environment observation (stdout/stderr of previous command or task description)
        and returns the next bash command to execute, or 'EXIT' to signal task completion.
        """
        pass

    def reset(self):
        """Resets the agent's internal state between tasks."""
        pass
