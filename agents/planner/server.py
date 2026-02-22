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

from .planner_executor import PlannerExecutor


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.getenv("PLANNER_HOST", "0.0.0.0")
PORT = int(os.getenv("PLANNER_PORT", 8000))
PUBLIC_URL = os.getenv("PLANNER_PUBLIC_URL", f"http://127.0.0.1:{PORT}")

# Initialize the planner agent card and agent skills
def create_planner_agent_card() -> AgentCard:
    return AgentCard(
        name="StudyPlanner",
        description=(
            "Expert agent that generates structured, prerequisite-aware study plans "
            "for any topic, difficulty level, time budget, and learning goal. "
            "Always returns valid JSON matching the StudyPlan schema."
        ),
        url=PUBLIC_URL
,
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
                id="generate_study_plan",
                name="Generate Study Plan",
                description=(
                    "Create a complete, ordered study plan inlcuding subtopics, schedule"
                    "project blueprint (when relevant), and learning advice."
                    "Input: topic, level, time budget, goal. Output: JSON only."
                ),
                tags=["study", "education", "learning"]
            )
        ]
    )

# Initialize the planner server
async def start_planner_server():
    logger.info("Initializing Study Planner A2A Server...")

    agent_card = create_planner_agent_card()

    request_handler = DefaultRequestHandler(
            agent_executor=PlannerExecutor(),
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

    logger.info(f"Starting Study Planner server at http://{HOST}:{PORT}")
    logger.info("Agent Card endpoint: http://localhost:8001/.well-known/agent.json")
    logger.info("Press CTRL+C to stop")

    await uvicorn_server.serve()

# Main function to run the server
def main():
    try:
        asyncio.run(start_planner_server())
    except KeyboardInterrupt:
        logger.info("Shutting down study planner server...")
    except Exception as e:
        logger.error(f"Server failed to start: {e}", exc_info=True)    

if __name__ == "__main__":
    main()

