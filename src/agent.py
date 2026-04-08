from dotenv import load_dotenv

from livekit.agents import (
    AgentServer,
    JobContext,
    cli,
)

from wakeword.pipeline import PipelineController

load_dotenv(".env")


server = AgentServer()


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    controller = PipelineController(ctx)
    await controller.run()


if __name__ == "__main__":
    cli.run_app(server)
