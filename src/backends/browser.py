"""
Browser automation backend using browser-use.
Provides high-level web automation for the Crix voice assistant.

Supports multiple LLM providers:
- OpenAI (gpt-4o-mini, gpt-4o) - via OPENAI_API_KEY
- Anthropic (claude-3-5-sonnet) - via ANTHROPIC_API_KEY
- Google (gemini-2.0-flash) - via GOOGLE_API_KEY
- Ollama (local models) - via OLLAMA_MODEL env var
"""

import asyncio
import os
from typing import Optional
from browser_use import Agent, Browser
from config import get_chrome_profile


class BrowserBackend:
    """Manages browser-use agent for web automation tasks."""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self._browser_lock = asyncio.Lock()

    def _get_llm(self):
        """
        Get the configured LLM for browser automation.
        Checks environment variables in order:
        1. OPENAI_API_KEY → ChatOpenAI
        2. ANTHROPIC_API_KEY → ChatAnthropic
        3. GOOGLE_API_KEY → ChatGoogle
        4. OLLAMA_MODEL → ChatOllama

        Falls back to a helpful error message if none configured.
        """
        # Try OpenAI first
        if os.getenv("OPENAI_API_KEY"):
            from browser_use import ChatOpenAI

            model = os.getenv("BROWSER_USE_OPENAI_MODEL", "gpt-4o-mini")
            return ChatOpenAI(model=model)

        # Try Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            from browser_use import ChatAnthropic

            model = os.getenv(
                "BROWSER_USE_ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"
            )
            return ChatAnthropic(model=model)

        # Try Google Gemini
        if os.getenv("GOOGLE_API_KEY"):
            from browser_use import ChatGoogle

            model = os.getenv("BROWSER_USE_GOOGLE_MODEL", "gemini-2.0-flash-exp")
            return ChatGoogle(model=model)

        # Try Ollama (local)
        ollama_model = os.getenv("OLLAMA_MODEL")
        if ollama_model:
            from browser_use import ChatOllama

            return ChatOllama(model=ollama_model)

        # No LLM configured
        raise ValueError(
            "No LLM configured for browser automation. Set one of:\n"
            "  OPENAI_API_KEY=sk-... (recommended: gpt-4o-mini)\n"
            "  ANTHROPIC_API_KEY=sk-... (claude-3-5-sonnet)\n"
            "  GOOGLE_API_KEY=... (gemini-2.0-flash)\n"
            "  OLLAMA_MODEL=llama2 (local, free)\n"
            "\n"
            "Optional model overrides:\n"
            "  BROWSER_USE_OPENAI_MODEL=gpt-4o\n"
            "  BROWSER_USE_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022\n"
            "  BROWSER_USE_GOOGLE_MODEL=gemini-2.0-flash-exp"
        )

    async def _get_or_create_browser(self) -> Browser:
        """
        Get existing browser instance or create a new one.
        Connects to the user's real Chrome profile by default.
        """
        async with self._browser_lock:
            if self.browser is None:
                chrome_profile = get_chrome_profile()

                try:
                    # Connect to system Chrome with user's profile
                    self.browser = Browser.from_system_chrome(
                        profile_directory=chrome_profile
                    )
                except Exception as e:
                    # Fallback: headless browser if Chrome profile fails
                    print(
                        f"Warning: Could not connect to Chrome profile '{chrome_profile}': {e}"
                    )
                    print("Falling back to headless browser (no saved logins)")
                    self.browser = Browser()

            return self.browser

    async def execute_task(self, task: str, max_steps: int = 30) -> str:
        """
        Execute a web automation task using browser-use agent.

        Args:
            task: Natural language description of what to do
            max_steps: Maximum steps the agent can take

        Returns:
            Result summary of what was accomplished
        """
        try:
            browser = await self._get_or_create_browser()
            llm = self._get_llm()

            # Create browser-use agent with the task
            agent = Agent(
                task=task,
                browser=browser,
                llm=llm,
                max_steps=max_steps,
            )

            # Run the agent
            history = await agent.run()

            # Extract meaningful result
            if history and history.final_result():
                return f"Browser task completed: {history.final_result()}"
            else:
                return f"Browser task '{task}' completed successfully."

        except ValueError as e:
            # LLM configuration error
            return f"Browser automation configuration error: {str(e)}"
        except Exception as e:
            return f"Browser automation error: {str(e)}"

    async def close(self):
        """Close the browser instance."""
        if self.browser:
            # browser-use handles cleanup automatically
            self.browser = None


# Global browser backend instance
_browser_backend: Optional[BrowserBackend] = None


async def get_browser_backend() -> BrowserBackend:
    """Get or create the global browser backend."""
    global _browser_backend
    if _browser_backend is None:
        _browser_backend = BrowserBackend()
    return _browser_backend


async def execute_browser_task(task: str, max_steps: int = 30) -> str:
    """
    High-level function to execute browser automation tasks.

    Examples:
        - "Search for 'best Linux laptops 2026' and summarize the top results"
        - "Go to Amazon and add Logitech MX Master 3S to cart"
        - "Fill out the job application at example.com with my resume data"
        - "Check my Gmail inbox and read unread emails"

    Args:
        task: Natural language task description
        max_steps: Maximum automation steps (default 30)
    """
    backend = await get_browser_backend()
    return await backend.execute_task(task, max_steps)
