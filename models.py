from typing import List, Literal, Optional

from pydantic import BaseModel, Field

AreaType = Literal["Work", "Health", "Finance", "Relationships", "Growth", "Home", "Admin"]
EnergyType = Literal["Low", "Medium", "High"]
CognitiveLoad = Literal["Deep Focus", "Active", "Passive", "Shallow"]
SensoryReq = Literal["Visual", "Auditory", "Physical", "Hands-Free", "Mixed"]


class CoreMeta(BaseModel):
    title: str = Field(..., description="A concise, actionable title.")
    life_area: AreaType = Field(..., description="The primary life domain.")
    expected_gain: Optional[str] = Field(None, description="The reason or expected benefit of completing this.")


class Goal(CoreMeta):
    type: Literal["goal"] = "goal"
    time_horizon: str = Field(..., description="e.g., '1 Month', '1 Year', '5 Years'")


class Project(CoreMeta):
    type: Literal["project"] = "project"
    status: Literal["Not Started", "In Progress", "On Hold"] = "Not Started"
    goal_title: Optional[str] = Field(None, description="The overarching goal this belongs to.")


class Task(CoreMeta):
    type: Literal["task"] = "task"
    related_project_title: Optional[str] = None
    status: Literal["To Do", "Done", "Blocked", "Someday"] = "To Do"
    priority_score: int = Field(..., ge=1, le=10)
    estimated_minutes: int = Field(30, ge=5, le=480)
    energy_required: EnergyType
    hard_deadline: Optional[str] = Field(None, description="YYYY-MM-DD format if a strict deadline exists.")
    cognitive_load: CognitiveLoad
    sensory_requirement: SensoryReq
    can_pair: bool


class Resource(BaseModel):
    type: Literal["resource"] = "resource"
    title: str
    url: str
    related_task_title: Optional[str] = None
    related_project_title: Optional[str] = None


class IntakeStructure(BaseModel):
    detected_goals: List[Goal] = Field(default_factory=list)
    detected_projects: List[Project] = Field(default_factory=list)
    detected_tasks: List[Task] = Field(default_factory=list)
    detected_resources: List[Resource] = Field(default_factory=list)
    reasoning_summary: str


class ChatMessage(BaseModel):
    message: str


class ChatAction(BaseModel):
    action_type: Literal["create_task", "none"] = Field(description="The action to take.")
    title: Optional[str] = None
    minutes: Optional[int] = 30


class AgentChatResponse(BaseModel):
    reply: str
    actions: List[ChatAction] = Field(default_factory=list)


class AdaptAction(BaseModel):
    action_type: Literal["add_task", "remove_task", "add_resource"]
    target_task_id: Optional[int] = None
    title: Optional[str] = None
    url: Optional[str] = None
    minutes: Optional[int] = 30


class ProjectAdaptation(BaseModel):
    summary: str
    actions: List[AdaptAction] = Field(default_factory=list)


class GlobalReflectionResponse(BaseModel):
    updated_max_minutes: int
    new_core_lessons: str
    reply: str
