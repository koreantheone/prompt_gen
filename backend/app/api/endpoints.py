from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from app.services.llm_service import LLMService
from app.services.dataforseo_client import DataForSEOClient
from app.services.vector_store import VectorStore

router = APIRouter()

# In-memory storage for job status (replace with Redis/DB in production)
jobs = {}

class SearchRequest(BaseModel):
    prompt: str
    keywords: Optional[str] = ""
    country: str
    language: str
    mode: str
    apis: List[str]
    llm_provider: str = "openai"

class JobStatus(BaseModel):
    id: str
    status: str
    progress: int
    logs: List[str]
    result: Optional[str] = None

def process_job(job_id: str, request: SearchRequest):
    llm = LLMService(provider=request.llm_provider)
    d4s = DataForSEOClient()
    vs = VectorStore()
    
    def log(msg):
        jobs[job_id]["logs"].append(msg)
        jobs[job_id]["status"] = msg

    try:
        # 1. Generate Keywords
        log(f"Generating keywords with {request.llm_provider.upper()}...")
        jobs[job_id]["progress"] = 10
        generated_keywords = llm.generate_keywords(request.prompt, request.keywords)
        log(f"Generated {len(generated_keywords)} keywords.")

        # 2. Fetch Data
        log("Fetching data from DataforSEO...")
        jobs[job_id]["progress"] = 20
        # Map country/lang codes to DataforSEO integers (simplified mapping)
        loc_code = 2840 if request.country == 'us' else 2410 # Default US/KR
        lang_code = "en" if request.language == 'en' else "ko"
        
        data_items = []
        total = len(generated_keywords)
        
        # If no APIs selected, default to google_search
        target_apis = request.apis if request.apis else ["google_search"]

        for i, kw in enumerate(generated_keywords):
            # Distribute APIs across keywords or call all for each?
            # Requirement: "Call desired keyword... from DataforSEO"
            # To avoid explosion of calls (50 keywords * N APIs), let's pick one API per keyword round-robin or just call all.
            # Given the "MAX 2,000/min" and "50 keywords", calling all APIs for all keywords might be heavy but feasible if N is small.
            # Let's call ALL requested APIs for EACH keyword to be robust.
            
            for api in target_apis:
                data = d4s.fetch_keyword_data(kw, loc_code, lang_code, api_type=api)
                data_items.append({"keyword": kw, "api": api, "data": data})
            
            progress = 20 + int((i / total) * 40) # 20% to 60%
            jobs[job_id]["progress"] = progress
            if i % 5 == 0:
                log(f"Fetched {i}/{total}: {kw}")

        # 3. Vector DB
        log("Building Vector Database...")
        jobs[job_id]["progress"] = 70
        vs.add_data(data_items)

        # 4. RAG & Prompt Gen
        log("Generating Hierarchy & Prompts...")
        jobs[job_id]["progress"] = 85
        
        # Retrieve context for the main prompt
        context_docs = vs.query(request.prompt, n_results=20)
        context_str = "\n\n".join(context_docs)
        
        result_json = llm.generate_hierarchy_and_prompts(request.prompt, context_str)
        
        jobs[job_id]["result"] = result_json
        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "Complete"
        log("Job finished successfully.")

    except Exception as e:
        log(f"Error: {str(e)}")
        jobs[job_id]["status"] = "Failed"

@router.post("/search", response_model=JobStatus)
async def start_search(request: SearchRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "id": job_id,
        "status": "Queued",
        "progress": 0,
        "logs": [],
        "result": None
    }
    background_tasks.add_task(process_job, job_id, request)
    return jobs[job_id]

@router.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]
