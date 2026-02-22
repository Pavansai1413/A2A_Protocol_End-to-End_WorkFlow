import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from google.adk.tools import google_search

from google.adk.agents import LlmAgent
from google.genai import types

load_dotenv()

class Subtopic(BaseModel):
    name: str = Field(..., description="Clear, concise name of the subtopic")
    description: str = Field(..., description="1-2 sentence explanation what will be learned")
    estimated_days: int = Field(..., description="Number of days required to master this subtopic")
    prerequisites: List[str] = Field(default_factory=list, description="Names of previous subtopics that must be completed before this one")


class WeeklySchedule(BaseModel):
    period: str = Field(..., description="day1, day2, etc.")
    subtopics: List[str] = Field(..., description="List of subtopics to be covered in this period")
    activities: str = Field(..., description="Activities to be done in this period")
    deliverables: Optional[str] = Field(default=None, description="mini goals to be achieved in this period")

    
class ProjectBlueprint(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    phases: List[str] = Field(default_factory=list)
    final_deliverable: Optional[str] = None


class StudyPlan(BaseModel):
    topic: str
    level: str
    total_duration_days: int
    subtopics: List[Subtopic] = Field(..., description="Ordered list — prerequisites respected")
    schedule: List[WeeklySchedule]
    project: Optional[ProjectBlueprint] = None
    advice: str = Field(..., description="1-3 sentences of general learning tips for this plan")



Planner_instruction = """
You are a expert Study Planner Agent.
You create realistic, prerequisite-aware, goal-oriented study plans for users.

Rules you MUST follow:
1. Respect the total time budget - spread content realistically.
   very shot budgets (1-3 days) -> focus on high-impact essentials only)
2. Order subtopics so prerequisites come before dependent topics.
3. If the goal mentions "project", "build", "portfolio" → include a realistic project blueprint.
4. Include hands on practice whenever it makes sense.
5. Output **ONLY** valid JSON that matches the StudyPlan schema - no extra text.
6. Use very clear, concise, professional English in all names and descriptions.


User will give you input like:
Topic:...
Level:beginner/intermediate/advanced
Time budget: 1 day/ 2 days
Goal: prepare for job interview / build a small project / understand fundamentals /...

Parse the input carefully and create a best possible plan for the user based on the upto date information available.
"""


planner_agent = LlmAgent(
    name="StudyPlanner",
    model = "gemini-2.5-flash",
    description = "StudyPlanner is the one that Creates structured, prerequisite-aware study plans for any topic and goal",
    instruction = Planner_instruction,
    tools = [google_search],
    generate_content_config = types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=5000,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            )
        ]

    )
)


