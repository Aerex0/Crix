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
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from tavily import TavilyClient

load_dotenv(".env")

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
        )

    @function_tool
    async def web_search(self, context: RunContext, query: str):
        """Whenever the user asks for information that requires searching the web, use this tool.
           Do not use your own knowledge, always search for the most up-to-date information.
        Args:
            query: The search query
        """
        client = TavilyClient()
        response = client.search(query, search_depth="advanced")
        return response
    
    @function_tool
    async def run_bash(self, context: RunContext, command: str):
        """
        You have access to a tool called `run_bash` that executes shell commands.

        Rules you must follow:
        - Before running ANY command, say out loud what you are about to run and why, then wait for the user to confirm with "yes".
        - Never run destructive commands such as rm, rmdir, mv, dd, mkfs, chmod, chown, kill, or anything that modifies or deletes files unless the user has explicitly and clearly requested it by name.
        - If the user's request is ambiguous, ask a clarifying question instead of guessing.
        - You are only allowed to run read/write only commands (ls, cat, grep, ps, df, echo) unless told otherwise.
        - You can switch  workspaces, close them or open them when the user asks that's it.
        - If a command might take a long time (e.g. find on /, large downloads), warn the user first.
        - Never chain commands with && or | , never do it.
        - If you  are asked to read or write a content from or to a file, then first use bash to find out it's actual path(if it exists or if it doesn't exist then ask the user where to create it) then use that path to read or write content
        """

        result = subprocess.run(
            command, shell=True, capture_output=True, text=True
        )
        return result.stdout or result.stderr

    @function_tool
    async def get_time(self, context: RunContext):
        return time.ctime()

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