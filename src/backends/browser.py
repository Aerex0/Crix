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

    def _format_step_log(
        self, step_num: int, model_output, action_result, error: Optional[str] = None
    ) -> str:
        """Format a single step into a readable log string."""
        lines = []

        # Step header
        lines.append(f"📍 Step {step_num}:")

        # Agent's thinking and reasoning
        if model_output:
            current_state = model_output.current_state

            if current_state.evaluation_previous_goal:
                lines.append(
                    f"  🎯 Previous goal: {current_state.evaluation_previous_goal}"
                )

            if current_state.memory:
                lines.append(f"  💭 Memory: {current_state.memory}")

            if current_state.next_goal:
                lines.append(f"  🎯 Next goal: {current_state.next_goal}")

            # Actions taken in this step
            if model_output.action:
                for action in model_output.action:
                    action_dict = action.model_dump(exclude_none=True, mode="json")
                    action_name = list(action_dict.keys())[0]
                    action_params = action_dict[action_name]

                    if action_params:
                        params_str = ", ".join(
                            f"{k}={repr(v)}" for k, v in action_params.items()
                        )
                        lines.append(f"  ▶️  {action_name}: {params_str}")
                    else:
                        lines.append(f"  ▶️  {action_name}")

        # Result of the action
        if action_result:
            if action_result.extracted_content:
                content = action_result.extracted_content
                if len(content) > 200:
                    content = content[:197] + "..."
                lines.append(f"  📄 Result: {content}")

            if error:
                lines.append(f"  ❌ Error: {error}")

        return "\n".join(lines)

    async def execute_task(self, task: str, max_steps: int = 30) -> str:
        """
        Execute a web automation task using browser-use agent.

        Args:
            task: Natural language description of what to do
            max_steps: Maximum steps the agent can take

        Returns:
            Detailed result with step-by-step logs, final result, and any errors
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

            # Build step-by-step log
            step_logs = []
            model_outputs = (
                history.model_outputs() if hasattr(history, "model_outputs") else []
            )
            action_results = (
                history.action_results() if hasattr(history, "action_results") else []
            )
            errors = history.errors() if hasattr(history, "errors") else []

            # Get URLs visited
            urls = history.urls() if hasattr(history, "urls") else []

            for i in range(len(history.history)):
                model_output = model_outputs[i] if i < len(model_outputs) else None
                result = action_results[i] if i < len(action_results) else None
                error = errors[i] if i < len(errors) else None

                step_log = self._format_step_log(i + 1, model_output, result, error)
                step_logs.append(step_log)

            # Combine step logs
            step_by_step_log = "\n\n".join(step_logs)

            # Extract the final result from history
            final_result = history.final_result()

            # Build the complete report
            report_parts = []

            # Add step-by-step logs
            if step_by_step_log:
                report_parts.append(step_by_step_log)

            # Add final result section
            if final_result:
                report_parts.append(f"\n📄 Final Result:\n{final_result}")
            else:
                # Check if max_steps was reached
                if len(history.history) >= max_steps:
                    report_parts.append(
                        f"\n⚠️ Reached maximum steps ({max_steps}) without completion"
                    )
                else:
                    report_parts.append("\n⚠️ No final result returned")

            # Add errors summary if any
            if history.has_errors():
                error_list = [e for e in errors if e]
                if error_list:
                    report_parts.append(f"\n⚠️ Warnings/Errors encountered:")
                    for err in error_list:
                        report_parts.append(f"  - {err}")

            # Combine everything
            full_report = "\n\n".join(report_parts)

            # Determine overall status
            if final_result:
                result_str = str(final_result)
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
                    return f"⚠️ Browser task completed with ISSUES:\n\n{full_report}"
                else:
                    return f"✅ Browser task SUCCEEDED:\n\n{full_report}"
            else:
                return f"⚠️ Browser task completed:\n\n{full_report}"

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
