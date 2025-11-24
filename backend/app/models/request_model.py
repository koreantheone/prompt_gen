from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# Task status types
TaskStatus = Literal["pending", "running", "success", "error"]

class TaskData(BaseModel):
    """Base model for task data"""
    status: TaskStatus = "pending"
    startedAt: Optional[str] = None
    completedAt: Optional[str] = None
    error: Optional[str] = None
    progress: int = 0
    logs: List[str] = Field(default_factory=list)

class DataCollectionTaskData(TaskData):
    """Data collection task specific data"""
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "generatedKeywords": [],
        "apiResponses": []
    })

class HierarchyGenerationTaskData(TaskData):
    """Hierarchy generation task specific data"""
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "hierarchy": None,
        "evaluation": None
    })

class PromptGenerationTaskData(TaskData):
    """Prompt generation task specific data"""
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "prompts": []
    })

class RequestConfig(BaseModel):
    """Configuration for a request"""
    prompt: str
    keywords: str = ""
    country: str
    language: str
    mode: str
    apis: List[str]
    llm_provider: str = "openai"
    include_evaluation: bool = False

class RequestTasks(BaseModel):
    """All tasks for a request"""
    dataCollection: DataCollectionTaskData = Field(default_factory=DataCollectionTaskData)
    hierarchyGeneration: HierarchyGenerationTaskData = Field(default_factory=HierarchyGenerationTaskData)
    promptGeneration: PromptGenerationTaskData = Field(default_factory=PromptGenerationTaskData)

class Request(BaseModel):
    """Main request model"""
    requestId: str
    createdAt: str
    updatedAt: str
    config: RequestConfig
    tasks: RequestTasks = Field(default_factory=RequestTasks)
    
    class Config:
        json_schema_extra = {
            "example": {
                "requestId": "REQ-20251124-001",
                "createdAt": "2025-11-24T14:37:09+09:00",
                "updatedAt": "2025-11-24T14:37:09+09:00",
                "config": {
                    "prompt": "AI tools for developers",
                    "keywords": "",
                    "country": "us",
                    "language": "en",
                    "mode": "comprehensive",
                    "apis": ["google_search"],
                    "llm_provider": "gemini-2.5-flash",
                    "include_evaluation": False
                },
                "tasks": {
                    "dataCollection": {
                        "status": "pending",
                        "startedAt": None,
                        "completedAt": None,
                        "error": None,
                        "progress": 0,
                        "logs": [],
                        "data": {
                            "generatedKeywords": [],
                            "apiResponses": []
                        }
                    },
                    "hierarchyGeneration": {
                        "status": "pending",
                        "startedAt": None,
                        "completedAt": None,
                        "error": None,
                        "progress": 0,
                        "logs": [],
                        "data": {
                            "hierarchy": None,
                            "evaluation": None
                        }
                    },
                    "promptGeneration": {
                        "status": "pending",
                        "startedAt": None,
                        "completedAt": None,
                        "error": None,
                        "progress": 0,
                        "logs": [],
                        "data": {
                            "prompts": []
                        }
                    }
                }
            }
        }
