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

            model = os.getenv("BROWSER_USE_GOOGLE_MODEL", "gemini-flash-latest")
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
            Detailed result with success/failure status, actions taken, and errors
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

            # Handle case where history is None or empty
            if not history:
                return (
                    f"❌ Browser task FAILED: No history returned.\n"
                    f"Task: {task}\n"
                    f"Error: The browser agent did not execute any steps. "
                    f"This may indicate a configuration or initialization issue."
                )

            # Extract the final result from history
            final_result = history.final_result()

            # Get action history if available
            action_summary = ""
            if hasattr(history, "actions") and history.actions:
                action_count = len(history.actions)
                action_summary = f"\n📊 Actions taken: {action_count} steps"

                # Include details of last few actions for context
                last_actions = (
                    history.actions[-3:] if action_count > 3 else history.actions
                )
                action_details = []
                for action in last_actions:
                    action_str = str(action)
                    # Truncate long action strings
                    if len(action_str) > 100:
                        action_str = action_str[:97] + "..."
                    action_details.append(f"  • {action_str}")

                if action_details:
                    action_summary += "\n" + "\n".join(action_details)

            # Check if the task actually succeeded
            if final_result:
                # Task completed with a result
                result_str = str(final_result)

                # Check for common failure indicators in the result
                failure_indicators = [
                    "failed",
                    "error",
                    "could not",
                    "unable to",
                    "cannot",
                    "unsuccessful",
                    "did not work",
                ]

                result_lower = result_str.lower()
                appears_failed = any(
                    indicator in result_lower for indicator in failure_indicators
                )

                if appears_failed:
                    return (
                        f"⚠️ Browser task completed with ERRORS:\n"
                        f"Result: {result_str}{action_summary}\n\n"
                        f"The task may have partially failed. Please verify the result."
                    )
                else:
                    return (
                        f"✅ Browser task SUCCEEDED:\n"
                        f"Result: {result_str}{action_summary}"
                    )
            else:
                # No final result, but history exists
                # Check if max_steps was reached
                if hasattr(history, "actions") and len(history.actions) >= max_steps:
                    return (
                        f"⚠️ Browser task reached MAX STEPS ({max_steps}) without completion:\n"
                        f"Task: {task}{action_summary}\n\n"
                        f"The task may be too complex or require more steps. "
                        f"Consider breaking it into smaller tasks or increasing max_steps."
                    )
                else:
                    return (
                        f"⚠️ Browser task completed but returned NO RESULT:\n"
                        f"Task: {task}{action_summary}\n\n"
                        f"The agent finished but didn't provide a final result. "
                        f"This may indicate the task was ambiguous or couldn't be completed."
                    )

        except ValueError as e:
            # LLM configuration error
            return (
                f"❌ Browser automation CONFIGURATION ERROR:\n"
                f"{str(e)}\n\n"
                f"Fix: Set up an LLM API key in your environment variables."
            )
        except Exception as e:
            # Other errors (network, browser crash, etc.)
            error_msg = str(e)
            return (
                f"❌ Browser automation EXCEPTION:\n"
                f"Task: {task}\n"
                f"Error: {error_msg}\n\n"
                f"This is an unexpected error. Check your browser configuration, "
                f"network connection, and ensure the website is accessible."
            )

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
