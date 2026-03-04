from dotenv import load_dotenv
from prompts.crix import SYSTEM_PROMPT

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