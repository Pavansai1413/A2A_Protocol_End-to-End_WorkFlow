import asyncio
import uuid
import logging
from typing import Any

from a2a.types import (
    Message,
    Task,
    Part,
    TaskState,
    TextPart,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types

from .planner_agent import planner_agent


logger = logging.getLogger(__name__)

class PlannerExecutor(AgentExecutor):
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.memory_service = InMemoryMemoryService()
        self.artifact_service = InMemoryArtifactService()

        self.runner = Runner(
            app_name = planner_agent.name,
            agent = planner_agent,
            session_service = self.session_service,
            memory_service = self.memory_service,
            artifact_service = self.artifact_service,
        )


    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.warning(f"Cancel requested but not implemented for PlannerExecutor - context {context.context_id}")
        await event_queue.enqueue_event(
            new_agent_text_message("Cancellation is not supported yet for this agent")
        )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        session_id = context.context_id

        if not session_id:
            session_id = str(uuid.uuid4())

        user_id = f"planner-user-{uuid.uuid4().hex[:8]}"

        await self.session_service.create_session(
            app_name=self.runner.app_name,
            user_id=user_id,
            session_id=session_id,
            state={},
        )

        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )

        full_response = ""
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        chunk = part.text
                        full_response += chunk
                        await event_queue.enqueue_event(
                            new_agent_text_message(chunk)
                        )
        
        if full_response:
            await event_queue.enqueue_event(
                new_agent_text_message("\n\n Plan generation complete.")
            )
        else:
            await event_queue.enqueue_event(
                new_agent_text_message("Plan generation failed.")
            )
planner_executor = PlannerExecutor()

        
