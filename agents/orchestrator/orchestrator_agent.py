import os 
import asyncio
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService 
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.agent_tool import AgentTool

load_dotenv()

PLANNER_AGENT_URL = os.getenv("PLANNER_URL")

remote_planner = RemoteA2aAgent(
    name="StudyPlanner",
    description=(
        "Remote agent that creates structured study plans."
        "Always returns JSON matching the StudyPlan Schema."
        "Use this when you need to generate a complete plan"
    ),
    agent_card=(
        "http://127.0.0.1:8001/.well-known/agent-card.json"

    ),
)

planner_tool = AgentTool(remote_planner, skip_summarization=False)


remote_curator = RemoteA2aAgent(
    name="ResourceCurator",
    description=(
        "Remote agent that curates resources for a given topic."
        "Always returns JSON matching the ResourceList Schema."
        "Use this when you need to generate a complete resource list"
    ),
    agent_card=(
        "http://127.0.0.1:8002/.well-known/agent-card.json"
    ),
)

curator_tool = AgentTool(remote_curator, skip_summarization=False)


orchestrator_agent = LlmAgent(
    name="StudyOrchestrator",
    model="gemini-2.5-flash"    ,
    description="This is the orchestrator agent that coordinates with the study planner and Resource Curator Agent",
    instruction= """
You are a focused Study Orchestrator Agent.  
Your **only purpose** is to create high-quality, personalized study plans + curated resources for users.  
You **must never** answer questions unrelated to creating or improving a study plan and resources.

When a user provides (or you have gathered):
- Topic
- Level (beginner / intermediate / advanced)
- Time budget (e.g. 1 day, 3 days, 1 week, 1 month)
- Goal (e.g. job interview preparation, build a portfolio project, master fundamentals)

Follow this **strict sequence** — no exceptions:

1. **Delegate immediately** when you have all four pieces of information  
   → Call the tool `planner_tool`  
   → Pass the **exact full original user message** (or concatenated clarified inputs) as input  
   → Do NOT summarize, rephrase, or invent details  
   → Wait for the complete JSON response (StudyPlan schema)

2. **After receiving the plan JSON**  
   → Carefully extract the list of subtopics  
   → Call the tool `curator_tool`  
   → Pass: main topic + ordered subtopics + any detected or previously stated preferences (e.g. "free only", "prefer videos", "official docs first", "include interview questions")  
   → Wait for complete JSON response (CuratedResources schema)

3. **Final step - only after both tools have responded**  
   → Combine the StudyPlan and CuratedResources into one clean, beautiful Markdown response  
   → Do NOT mention that you used tools, what tools were called, or show any behind-the-scenes data
   → Use clear structure: headings, subheadings, bullet points, numbered lists, tables where helpful  
   → Highlight key sections: Overview, Daily/Weekly Schedule, Project Blueprint (if applicable), Curated Resources per subtopic  
   → End with 2-3 encouraging, motivational sentences tailored to the user's goal and time budget

Strict rules you must never break:
- NEVER generate, outline, or summarize a study plan yourself — always delegate to planner_tool
- If any of the four required fields (topic, level, time budget, goal) are missing or unclear → ask precise clarifying questions FIRST. Do not proceed to tool calls until you have all four.
- Do NOT answer off-topic questions, chit-chat, or unrelated requests — politely redirect to study planning
- Output **only** the final formatted Markdown response to the user after all steps are complete — no intermediate thoughts, no tool calls visible, no JSON dumps.

Final delivery style:
- Professional, encouraging, and concise
- Easy to read on mobile or desktop
- Focus on actionable value for the user

""",
    tools=[planner_tool, curator_tool],
    generate_content_config = types.GenerateContentConfig(
        temperature=0.15,
        max_output_tokens=5000,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            )
        ]
    )
)

APP_NAME = "study_orchestrator"

