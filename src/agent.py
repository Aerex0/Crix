from dotenv import load_dotenv
from prompts.crix import SYSTEM_PROMPT
import subprocess
import time

from livekit import agents, rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    cli,
    function_tool,
    inference,
    room_io,
    RoomInputOptions,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from tavily import TavilyClient

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
    get_mouse_position,
    web_search,
    get_time,
)

load_dotenv(".env")

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
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
                get_mouse_position,
                web_search,
                get_time,
            ],
        )

server = AgentServer()

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="multi"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="elevenlabs/eleven_turbo_v2_5",voice="iP95p4xoKVk53GoZ742B"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        preemptive_generation=True,
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
                if params.participant.kind 
                == rtc.ParticipantKind.PARTICIPANT_KIND_SIP 
                else noise_cancellation.BVC(),
            ),
        ),
    )

    await session.generate_reply(
        instructions="Welcome your boss and offer your assistance."
    )


if __name__ == "__main__":
    cli.run_app(server)