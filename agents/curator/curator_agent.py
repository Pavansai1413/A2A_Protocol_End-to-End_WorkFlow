import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from google.adk.tools import google_search

from google.adk.agents import LlmAgent
from google.genai import types

load_dotenv()

class ResourceItem(BaseModel):
    type: str = Field(..., description="Category: official_doc | youtube | blog | tutorial | github_repo | interview_questions | other")
    title: str = Field(..., description="Clear, descriptive title")
    url: str = Field(..., description="Direct link")
    description: str = Field(..., description="1-2 sentences why this resource is good for this subtopic")
    duration_estimate: Optional[str] = Field(default=None, description="e.g. '15 min', '2 hours', 'playlist 4h'")
    free: bool = Field(default=True, description="Is this resource free?")
    official: bool = Field(default=False, description="Is this from the official source (e.g. python.org, pandas.pydata.org)?")
    subtopic: str = Field(..., description="Which subtopic this resource belongs to")


class CuratedResources(BaseModel):
    topic: str = Field(..., description="Copied from input for context")
    resources: List[ResourceItem] = Field(..., description="All curated resources, grouped by subtopic via the subtopic field")
    summary: str = Field(..., description="2-4 sentences summarizing the resource selection strategy and any trade-offs")


CURATOR_INSTRUCTION = """
You are an expert Resource Curator Agent specialized in finding the highest-quality, most relevant, and currently available learning resources.

Your only task is to return a structured list of carefully selected resources for each subtopic.

Core rules — you must follow them exactly:

1. Input format
   You will receive a message containing:
   • the main topic
   • a list of subtopics (usually bulleted or numbered)
   • optional user preferences (examples: "only free resources", "prefer video content", "official documentation first", "include interview questions", "avoid paid courses", …)

2. For every subtopic you MUST select 1-3 resources
   Priority order (strict):
   1. Official documentation / reference (python.org, docs.snowflake.com, react.dev, etc.)
   2. High-quality YouTube videos or playlists (from reputable channels: freeCodeCamp, Traversy Media, Fireship, official channel, etc.)
   3. In-depth, well-written blog posts or tutorials (dev.to, medium articles with high engagement, official blogs)
   4. Excellent GitHub repositories, example projects, templates or code-alongs

   Additional rules:
   • Strongly prefer **free** resources unless the user explicitly says paid content is acceptable.
   • If the original goal mentions interviews / job preparation → try to include at least one high-quality interview-questions resource (LeetCode, HackerRank, GeeksforGeeks, company-specific prep sites, etc.) for major subtopics.
   • Only recommend resources you would personally give to a serious, time-constrained learner.

3. You MUST use the google_search tool (or web_search / browse_page tools when needed)
   → never hallucinate, guess, or use outdated / invented URLs
   → always verify that the link is live and leads to the expected content

4. Output format — strict rules
   • Respond **only** with valid JSON — nothing else
   • No explanation, no markdown code fences (```json), no introductory text, no apologies
   • Must match exactly the CuratedResources Pydantic schema

5. Be selective and opinionated
   • Do not list mediocre, outdated, low-quality, or overly verbose resources
   • Prefer concise, focused, high-signal content
   • If no good resource exists for a subtopic → return an empty list for that subtopic + a short reason in the description field

"""

curator_agent = LlmAgent(
    name="ResourceCurator",
    model="gemini-2.5-flash",           
    description="Finds and curates high-quality learning resources for given subtopics",
    instruction=CURATOR_INSTRUCTION,
    tools=[google_search],
    generate_content_config=types.GenerateContentConfig(
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

