"""Pipeline controller for Crix with wake word support."""

import asyncio
import os
import sys
from enum import Enum

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    inference,
    room_io,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from backends.memory import (
    build_memory_context,
    ensure_memory_files,
    flush_session_memory,
)
from config import (
    get_memory_enabled,
    get_memory_flush_enabled,
    get_memory_max_context_chars,
    get_wakeword_enabled,
    get_wakeword_model_path,
    get_wakeword_threshold,
    get_wakeword_debounce,
)
from prompts.crix import SYSTEM_PROMPT
from tools import (
    type_text,
    press_key,
    type_and_submit,
    paste_text,
    move_mouse,
    click,
    double_click,
    scroll,
    switch_workspace,
    focus_window,
    list_open_windows,
    open_app,
    read_screen_text,
    get_clipboard,
    select_all_and_copy,
    run_command_silent,
    get_screen_size,
    web_search,
    get_time,
    browse_web,
    save_memory,
    memory_search,
    memory_get,
)
from wakeword.detector import WakeWordDetector


class PipelineState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"


class PipelineController:
    """Controls the voice assistant pipeline with wake word detection."""

    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.state = PipelineState.IDLE
        self._session: AgentSession | None = None
        self._detector: WakeWordDetector | None = None

    async def run(self):
        """Run the main pipeline loop."""
        wakeword_enabled = get_wakeword_enabled()

        if wakeword_enabled:
            await self._run_with_wakeword()
        else:
            await self._run_direct()

    async def _run_with_wakeword(self):
        """Run with wake word detection."""
        model_path = get_wakeword_model_path()
        threshold = get_wakeword_threshold()
        debounce = get_wakeword_debounce()

        self._detector = WakeWordDetector(
            model_path=model_path,
            threshold=threshold,
            debounce=debounce,
        )

        print(f"[Pipeline] Wake word enabled. Listening for wake word...")

        while True:
            self.state = PipelineState.IDLE
            print("[Pipeline] Waiting for wake word...")

            try:
                detection = await self._detector.wait_for_wake_word()
                print(
                    f"[Pipeline] Wake word detected: {detection.name} ({detection.confidence:.2f})"
                )

                await self._start_agent_session()

            except asyncio.CancelledError:
                print("[Pipeline] Cancelled, shutting down...")
                break
            except Exception as e:
                print(f"[Pipeline] Error in wake word loop: {e}")
                await asyncio.sleep(1)

    async def _start_agent_session(self):
        """Start an agent session after wake word detected."""
        memory_enabled = get_memory_enabled()
        memory_instructions = SYSTEM_PROMPT

        if memory_enabled:
            ensure_memory_files()
            memory_context = build_memory_context(get_memory_max_context_chars())
            if memory_context:
                memory_instructions = (
                    f"{SYSTEM_PROMPT}\n\n"
                    "## Memory Context Snapshot\n"
                    "Use this for continuity, but verify with memory_search/memory_get when needed.\n"
                    f"{memory_context}"
                )

        class Assistant(Agent):
            pass

        assistant = Assistant(
            instructions=memory_instructions,
            tools=[
                type_text,
                press_key,
                type_and_submit,
                paste_text,
                move_mouse,
                click,
                double_click,
                scroll,
                switch_workspace,
                focus_window,
                list_open_windows,
                open_app,
                read_screen_text,
                get_clipboard,
                select_all_and_copy,
                run_command_silent,
                get_screen_size,
                web_search,
                get_time,
                browse_web,
                save_memory,
                memory_search,
                memory_get,
            ],
        )

        self._session = AgentSession(
            stt=inference.STT(model="deepgram/nova-3", language="multi"),
            llm=inference.LLM(model="openai/gpt-4.1-mini"),
            tts=inference.TTS(
                model="elevenlabs/eleven_turbo_v2_5", voice="iP95p4xoKVk53GoZ742B"
            ),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
            preemptive_generation=True,
        )

        await self._session.start(
            room=self.ctx.room,
            agent=assistant,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(
                    noise_cancellation=lambda params: (
                        noise_cancellation.BVCTelephony()
                        if params.participant.kind
                        == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                        else noise_cancellation.BVC()
                    ),
                ),
            ),
        )

        if memory_enabled and get_memory_flush_enabled():

            async def _flush_memory_on_shutdown(reason: str) -> None:
                try:
                    history_dict = self._session.history.to_dict(
                        exclude_image=True,
                        exclude_audio=True,
                        exclude_metrics=True,
                    )
                    result = flush_session_memory(history_dict)
                    print(f"Memory flush on shutdown ({reason}): {result}")
                except Exception as e:
                    print(f"Memory flush failed ({reason}): {e}")

            self.ctx.add_shutdown_callback(_flush_memory_on_shutdown)

        self.state = PipelineState.PROCESSING
        await self._session.generate_reply()

    async def _run_direct(self):
        """Run directly without wake word (console mode)."""
        memory_enabled = get_memory_enabled()
        memory_instructions = SYSTEM_PROMPT

        if memory_enabled:
            ensure_memory_files()
            memory_context = build_memory_context(get_memory_max_context_chars())
            if memory_context:
                memory_instructions = (
                    f"{SYSTEM_PROMPT}\n\n"
                    "## Memory Context Snapshot\n"
                    "Use this for continuity, but verify with memory_search/memory_get when needed.\n"
                    f"{memory_context}"
                )

        class Assistant(Agent):
            pass

        assistant = Assistant(
            instructions=memory_instructions,
            tools=[
                type_text,
                press_key,
                type_and_submit,
                paste_text,
                move_mouse,
                click,
                double_click,
                scroll,
                switch_workspace,
                focus_window,
                list_open_windows,
                open_app,
                read_screen_text,
                get_clipboard,
                select_all_and_copy,
                run_command_silent,
                get_screen_size,
                web_search,
                get_time,
                browse_web,
                save_memory,
                memory_search,
                memory_get,
            ],
        )

        session = AgentSession(
            stt=inference.STT(model="deepgram/nova-3", language="multi"),
            llm=inference.LLM(model="openai/gpt-4.1-mini"),
            tts=inference.TTS(
                model="elevenlabs/eleven_turbo_v2_5", voice="iP95p4xoKVk53GoZ742B"
            ),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
            preemptive_generation=True,
        )

        await session.start(
            room=self.ctx.room,
            agent=assistant,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(
                    noise_cancellation=lambda params: (
                        noise_cancellation.BVCTelephony()
                        if params.participant.kind
                        == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                        else noise_cancellation.BVC()
                    ),
                ),
            ),
        )

        if memory_enabled and get_memory_flush_enabled():

            async def _flush_memory_on_shutdown(reason: str) -> None:
                try:
                    history_dict = session.history.to_dict(
                        exclude_image=True,
                        exclude_audio=True,
                        exclude_metrics=True,
                    )
                    result = flush_session_memory(history_dict)
                    print(f"Memory flush on shutdown ({reason}): {result}")
                except Exception as e:
                    print(f"Memory flush failed ({reason}): {e}")

            self.ctx.add_shutdown_callback(_flush_memory_on_shutdown)

        await session.generate_reply()
