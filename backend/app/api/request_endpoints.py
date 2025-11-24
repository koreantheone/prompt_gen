"""
New API endpoints for request-based workflow.
Provides endpoints for creating, managing, and executing tasks.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Literal
from app.models.request_model import RequestConfig, Request
from app.services.request_storage import RequestStorage
from app.services.task_processors import (
    DataCollectionTask,
    HierarchyGenerationTask,
    PromptGenerationTask
)

router = APIRouter()
storage = RequestStorage()

# Task name type
TaskName = Literal["dataCollection", "hierarchyGeneration", "promptGeneration"]


class CreateRequestRequest(BaseModel):
    """Request body for creating a new request"""
    prompt: str
    keywords: str = ""
    country: str
    language: str
    mode: str
    apis: List[str]
    llm_provider: str = "openai"
    include_evaluation: bool = False


class CreateRequestResponse(BaseModel):
    """Response for creating a new request"""
    requestId: str
    message: str = "Request created successfully"


class ExecuteTaskResponse(BaseModel):
    """Response for executing a task"""
    status: str
    message: str


@router.post("/requests/create", response_model=CreateRequestResponse)
async def create_request(
    request: CreateRequestRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new request and automatically start Task 1 (Data Collection).
    Returns the request ID immediately.
    """
    # Create request config
    config = RequestConfig(**request.model_dump())
    
    # Create request
    new_request = storage.create_request(config)
    
    # Start Task 1 (Data Collection) in background
    def run_data_collection():
        task = DataCollectionTask()
        task.execute(new_request.requestId)
    
    background_tasks.add_task(run_data_collection)
    
    return CreateRequestResponse(
        requestId=new_request.requestId,
        message="Request created and data collection started"
    )


@router.get("/requests", response_model=Dict)
async def list_requests(limit: int = 50, offset: int = 0):
    """
    List all requests with pagination.
    Returns a list of requests with their current status.
    """
    result = storage.list_requests(limit=limit, offset=offset)
    return result


@router.get("/requests/{request_id}", response_model=Request)
async def get_request(request_id: str):
    """
    Get detailed information about a specific request.
    Includes all task statuses and data.
    """
    request = storage.get_request(request_id)
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return request


@router.post("/requests/{request_id}/tasks/{task_name}/execute", response_model=ExecuteTaskResponse)
async def execute_task(
    request_id: str,
    task_name: TaskName,
    background_tasks: BackgroundTasks
):
    """
    Execute or retry a specific task.
    The task will run in the background.
    """
    # Verify request exists
    request = storage.get_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Get the appropriate task processor
    task_processors = {
        "dataCollection": DataCollectionTask,
        "hierarchyGeneration": HierarchyGenerationTask,
        "promptGeneration": PromptGenerationTask
    }
    
    TaskClass = task_processors.get(task_name)
    if not TaskClass:
        raise HTTPException(status_code=400, detail="Invalid task name")
    
    # Reset task status to pending before execution
    storage.update_task_status(
        request_id=request_id,
        task_name=task_name,
        status="pending",
        error=None,
        progress=0,
        log=f"Task {task_name} queued for execution"
    )
    
    # Execute task in background
    def run_task():
        task = TaskClass()
        task.execute(request_id)
    
    background_tasks.add_task(run_task)
    
    return ExecuteTaskResponse(
        status="started",
        message=f"Task {task_name} started"
    )


@router.get("/requests/{request_id}/tasks/{task_name}/status")
async def get_task_status(request_id: str, task_name: TaskName):
    """
    Get the status of a specific task.
    """
    request = storage.get_request(request_id)
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    task = getattr(request.tasks, task_name, None)
    if not task:
        raise HTTPException(status_code=400, detail="Invalid task name")
    
    return task.model_dump()


@router.delete("/requests/{request_id}")
async def delete_request(request_id: str):
    """
    Delete a request and all its data.
    """
    success = storage.delete_request(request_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return {"message": "Request deleted successfully"}


# Backward compatibility endpoint
@router.post("/search")
async def search_legacy(
    request: CreateRequestRequest,
    background_tasks: BackgroundTasks
):
    """
    Legacy /search endpoint for backward compatibility.
    Redirects to the new request-based workflow.
    """
    # Create request using new workflow
    config = RequestConfig(**request.model_dump())
    new_request = storage.create_request(config)
    
    # Start Task 1 in background
    def run_data_collection():
        task = DataCollectionTask()
        task.execute(new_request.requestId)
    
    background_tasks.add_task(run_data_collection)
    
    # Return in old format for compatibility
    return {
        "id": new_request.requestId,
        "status": "Queued",
        "progress": 0,
        "logs": ["Request created and data collection started"],
        "result": None,
        "requestId": new_request.requestId  # Add new field
    }


@router.get("/status/{job_id}")
async def get_status_legacy(job_id: str):
    """
    Legacy /status endpoint for backward compatibility.
    Maps to the new request system.
    """
    request = storage.get_request(job_id)
    
    if not request:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Determine overall status
    dc_task = request.tasks.dataCollection
    hg_task = request.tasks.hierarchyGeneration
    pg_task = request.tasks.promptGeneration
    
    # Calculate overall progress
    progress = 0
    if dc_task.status == "success":
        progress += 33
    elif dc_task.status == "running":
        progress += dc_task.progress // 3
    
    if hg_task.status == "success":
        progress += 33
    elif hg_task.status == "running":
        progress += hg_task.progress // 3
    
    if pg_task.status == "success":
        progress += 34
    elif pg_task.status == "running":
        progress += pg_task.progress // 3
    
    # Determine status
    if pg_task.status == "success":
        status = "Complete"
        result = pg_task.data.get("prompts", [])
    elif any(t.status == "error" for t in [dc_task, hg_task, pg_task]):
        status = "Failed"
        result = None
    elif any(t.status == "running" for t in [dc_task, hg_task, pg_task]):
        status = "Running"
        result = None
    else:
        status = "Queued"
        result = None
    
    # Collect all logs
    all_logs = []
    all_logs.extend(dc_task.logs)
    all_logs.extend(hg_task.logs)
    all_logs.extend(pg_task.logs)
    
    return {
        "id": job_id,
        "status": status,
        "progress": progress,
        "logs": all_logs,
        "result": result,
        "requestId": job_id  # Add new field
    }
