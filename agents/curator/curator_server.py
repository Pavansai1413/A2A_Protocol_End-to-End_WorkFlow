import asyncio
import logging
import os
from dotenv import load_dotenv
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
)

from .curator_executor import CuratorExecutor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.getenv("CURATOR_HOST", "0.0.0.0")
PORT = int(os.getenv("CURATOR_PORT", 8002))
PUBLIC_URL = os.getenv("CURATOR_PUBLIC_URL", f"http://127.0.0.1:{PORT}")
def create_curator_agent_card() -> AgentCard:
    return AgentCard(
        name="ResourceCurator",
        description=(
            "Specialized agent that curates high-quality, relevant learning resources "
            "(official docs, YouTube videos/playlists, blogs, tutorials, GitHub repos) "
            "for given subtopics. Prioritizes free resources and official documentation."
        ),
        url=PUBLIC_URL,
        version="0.1.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "application/json"],
        capabilities=AgentCapabilities(
            streaming=True,
            pushNotifications=False,
            stateTransitionNotifications=False,
        ),
        skills=[
            AgentSkill(
                id="curate_resources",
                name="Curate Learning Resources",
                description=(
                    "Given a list of subtopics (and optional preferences like 'free only', "
                    "'video first', 'include interview questions'), returns a structured "
                    "JSON list of the best matching resources."
                ),
                tags=["education", "resources", "curation", "learning", "tutorials"],
            )
        ]
    )


async def start_curator_server():
    logger.info("Initializing Resource Curator A2A Server...")

    agent_card = create_curator_agent_card()

    request_handler = DefaultRequestHandler(
        agent_executor=CuratorExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    config = uvicorn.Config(
        server_app.build(),
        host=HOST,
        port=PORT,
        log_level="info",
    )

    uvicorn_server = uvicorn.Server(config)

    logger.info(f"Starting Resource Curator server at http://{HOST}:{PORT}")
    logger.info(f"Agent Card endpoint: http://localhost:{PORT}/.well-known/agent.json")
    logger.info("Press CTRL+C to stop")

    await uvicorn_server.serve()


def main():
    try:
        asyncio.run(start_curator_server())
    except KeyboardInterrupt:
        logger.info("Shutting down Resource Curator server...")
    except Exception as e:
        logger.error(f"Server failed to start: {e}", exc_info=True)

if __name__ == "__main__":
    main()