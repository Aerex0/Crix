from dotenv import load_dotenv
from prompts.crix import SYSTEM_PROMPT

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
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
)
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

load_dotenv(".env")


class Assistant(Agent):
    def __init__(self, instructions: str = SYSTEM_PROMPT) -> None:
        super().__init__(
            instructions=instructions,
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


server = AgentServer()


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
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
        room=ctx.room,
        agent=Assistant(instructions=memory_instructions),
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

        ctx.add_shutdown_callback(_flush_memory_on_shutdown)

    await session.generate_reply(
        instructions="Welcome your boss and offer your assistance."
    )


if __name__ == "__main__":
    cli.run_app(server)
