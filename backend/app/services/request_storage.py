import os
import json
import glob
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from app.models.request_model import Request, RequestConfig, TaskStatus

class RequestStorage:
    """
    Persistent storage for request data using JSON files.
    Each request is stored as a separate JSON file in the requests_db directory.
    """
    
    def __init__(self, storage_dir: str = "./requests_db"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def _get_request_path(self, request_id: str) -> Path:
        """Get the file path for a request"""
        return self.storage_dir / f"{request_id}.json"
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID"""
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        
        # Find existing requests for today
        pattern = f"REQ-{date_str}-*.json"
        existing = glob.glob(str(self.storage_dir / pattern))
        
        # Get the next sequence number
        if existing:
            sequences = []
            for path in existing:
                try:
                    seq = int(Path(path).stem.split('-')[-1])
                    sequences.append(seq)
                except (ValueError, IndexError):
                    continue
            next_seq = max(sequences) + 1 if sequences else 1
        else:
            next_seq = 1
        
        return f"REQ-{date_str}-{next_seq:03d}"
    
    def create_request(self, config: RequestConfig) -> Request:
        """Create a new request with generated ID"""
        request_id = self._generate_request_id()
        now = datetime.now().isoformat()
        
        request = Request(
            requestId=request_id,
            createdAt=now,
            updatedAt=now,
            config=config
        )
        
        self.save_request(request)
        return request
    
    def save_request(self, request: Request) -> None:
        """Save or update a request"""
        request.updatedAt = datetime.now().isoformat()
        
        path = self._get_request_path(request.requestId)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(request.model_dump(), f, indent=2, ensure_ascii=False)
    
    def get_request(self, request_id: str) -> Optional[Request]:
        """Retrieve a request by ID"""
        path = self._get_request_path(request_id)
        
        if not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Request(**data)
        except Exception as e:
            print(f"Error loading request {request_id}: {e}")
            return None
    
    def list_requests(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List all requests with pagination"""
        all_files = sorted(
            glob.glob(str(self.storage_dir / "REQ-*.json")),
            key=os.path.getmtime,
            reverse=True  # Most recent first
        )
        
        total = len(all_files)
        files = all_files[offset:offset + limit]
        
        requests = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                requests.append(Request(**data))
            except Exception as e:
                print(f"Error loading request from {file_path}: {e}")
                continue
        
        return {
            "requests": [r.model_dump() for r in requests],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def update_task_status(
        self,
        request_id: str,
        task_name: str,
        status: TaskStatus,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        progress: Optional[int] = None,
        log: Optional[str] = None
    ) -> bool:
        """Update the status of a specific task"""
        request = self.get_request(request_id)
        if not request:
            return False
        
        # Get the task
        task = getattr(request.tasks, task_name, None)
        if not task:
            return False
        
        # Update status
        task.status = status
        
        # Update timestamps
        now = datetime.now().isoformat()
        if status == "running" and not task.startedAt:
            task.startedAt = now
        elif status in ["success", "error"]:
            task.completedAt = now
        
        # Update data
        if data is not None:
            task.data.update(data)
        
        # Update error
        if error is not None:
            task.error = error
        
        # Update progress
        if progress is not None:
            task.progress = progress
        
        # Add log
        if log is not None:
            task.logs.append(f"[{now}] {log}")
        
        # Save the request
        self.save_request(request)
        return True
    
    def delete_request(self, request_id: str) -> bool:
        """Delete a request"""
        path = self._get_request_path(request_id)
        
        if not path.exists():
            return False
        
        try:
            path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting request {request_id}: {e}")
            return False
    
    def get_task_data(self, request_id: str, task_name: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific task"""
        request = self.get_request(request_id)
        if not request:
            return None
        
        task = getattr(request.tasks, task_name, None)
        if not task:
            return None
        
        return task.data
