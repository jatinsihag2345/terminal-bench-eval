import os
import re
from typing import Optional, List, Dict
from .base import BaseAgent


class LLMAgent(BaseAgent):
    """
    Autonomous bash agent driven by frontier LLMs (via LiteLLM / OpenAI / Anthropic).
    Implements a multi-turn ReAct reasoning loop.
    """

    SYSTEM_PROMPT = """You are an autonomous expert software engineering and Linux systems agent.
You are given a terminal task in an isolated environment.
Respond with EXACTLY ONE bash command inside a ```bash codeblock.
When you have solved the task completely, respond with:
```bash
EXIT
```
Do not include any conversational filler. Only output reasoning followed by your bash block.
"""

    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
        super().__init__(name=model_name)
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.messages: List[Dict[str, str]] = []

    def reset(self):
        self.messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

    def act(self, observation: str) -> Optional[str]:
        self.messages.append({"role": "user", "content": observation})

        try:
            import litellm
            response = litellm.completion(
                model=self.model_name,
                messages=self.messages,
                temperature=0.0,
                max_tokens=600
            )
            content = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": content})

            # Extract command from markdown block or plain text
            match = re.search(r"```(?:bash|sh)?\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                cmd = match.group(1).strip()
            else:
                cmd = content.strip().split("\n")[0]

            return cmd
        except Exception as e:
            # Fallback for local testing / offline execution
            return "EXIT"
