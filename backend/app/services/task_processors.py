"""
Independent task processors for the 3-stage workflow.
Each task can run independently and handles errors gracefully.
"""

import traceback
from typing import Dict, Any, List
from datetime import datetime
from app.services.request_storage import RequestStorage
from app.services.llm_service import LLMService
from app.services.dataforseo_client import DataForSEOClient
from app.services.vector_store import VectorStore

class TaskProcessor:
    """Base class for task processors"""
    
    def __init__(self):
        self.storage = RequestStorage()
    
    def log(self, request_id: str, task_name: str, message: str):
        """Add a log message to the task"""
        self.storage.update_task_status(
            request_id=request_id,
            task_name=task_name,
            status="running",  # Keep current status
            log=message
        )
        print(f"[{request_id}][{task_name}] {message}")


class DataCollectionTask(TaskProcessor):
    """
    Task 1: Data Collection
    - Generate keywords using LLM
    - Call DataForSEO APIs for each keyword
    - Save ALL API responses (even on error)
    - Store to vector database
    """
    
    def execute(self, request_id: str) -> bool:
        """Execute data collection task"""
        task_name = "dataCollection"
        
        try:
            # Get request
            request = self.storage.get_request(request_id)
            if not request:
                print(f"Request {request_id} not found")
                return False
            
            config = request.config
            
            # Mark as running
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="running",
                progress=0,
                log="Starting data collection..."
            )
            
            # Initialize services
            llm = LLMService(provider=config.llm_provider)
            d4s = DataForSEOClient()
            vs = VectorStore()
            
            # Step 1: Generate keywords
            self.log(request_id, task_name, f"Generating keywords with {config.llm_provider}...")
            self.storage.update_task_status(request_id, task_name, "running", progress=10)
            
            generated_keywords = llm.generate_keywords(config.prompt, config.keywords)
            self.log(request_id, task_name, f"Generated {len(generated_keywords)} keywords")
            
            if not generated_keywords:
                self.log(request_id, task_name, "WARNING: No keywords generated")
            
            # Save generated keywords
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="running",
                data={"generatedKeywords": generated_keywords},
                progress=20
            )
            
            # Step 2: Fetch data from DataForSEO
            self.log(request_id, task_name, "Fetching data from DataForSEO...")
            
            # Map country/lang codes
            loc_code = 2840 if config.country == 'us' else 2410  # US/KR
            lang_code = "en" if config.language == 'en' else "ko"
            
            # Default to google_search if no APIs selected
            target_apis = config.apis if config.apis else ["google_search"]
            
            api_responses = []
            total = len(generated_keywords)
            
            for i, kw in enumerate(generated_keywords):
                for api in target_apis:
                    try:
                        # Fetch data
                        data = d4s.fetch_keyword_data(kw, loc_code, lang_code, api_type=api)
                        
                        # ALWAYS save the response, even if it's an error
                        api_responses.append({
                            "keyword": kw,
                            "api": api,
                            "response": data,
                            "error": None,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        # Save error response
                        error_msg = str(e)
                        api_responses.append({
                            "keyword": kw,
                            "api": api,
                            "response": {},
                            "error": error_msg,
                            "timestamp": datetime.now().isoformat()
                        })
                        self.log(request_id, task_name, f"Error fetching {kw} ({api}): {error_msg}")
                
                # Update progress
                progress = 20 + int((i / total) * 50)  # 20% to 70%
                self.storage.update_task_status(
                    request_id=request_id,
                    task_name=task_name,
                    status="running",
                    progress=progress
                )
                
                if i % 5 == 0:
                    self.log(request_id, task_name, f"Fetched {i}/{total} keywords")
            
            # Save API responses
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="running",
                data={"apiResponses": api_responses},
                progress=70
            )
            
            # Step 3: Build vector database
            self.log(request_id, task_name, "Building vector database...")
            
            # Prepare data items for vector store
            data_items = []
            for resp in api_responses:
                if resp.get("response"):  # Only add if we have data
                    data_items.append({
                        "keyword": resp["keyword"],
                        "api": resp["api"],
                        "data": resp["response"],
                        "request_id": request_id  # Tag with request ID
                    })
            
            if data_items:
                vs.add_data(data_items)
                self.log(request_id, task_name, f"Added {len(data_items)} items to vector store")
            else:
                self.log(request_id, task_name, "No data to add to vector store")
            
            # Mark as success
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="success",
                progress=100,
                log="Data collection completed successfully"
            )
            
            return True
            
        except Exception as e:
            error_msg = f"Error in data collection: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            
            # Mark as error but keep any data we collected
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="error",
                error=error_msg,
                log="Data collection failed with error"
            )
            
            return False


class HierarchyGenerationTask(TaskProcessor):
    """
    Task 2: Hierarchy Generation
    - Load data from completed DataCollection task
    - Query vector store for context
    - Generate hierarchy using LLM
    - Optionally run 8-expert evaluation
    """
    
    def execute(self, request_id: str) -> bool:
        """Execute hierarchy generation task"""
        task_name = "hierarchyGeneration"
        
        try:
            # Get request
            request = self.storage.get_request(request_id)
            if not request:
                print(f"Request {request_id} not found")
                return False
            
            config = request.config
            
            # Check if data collection is complete
            if request.tasks.dataCollection.status != "success":
                error_msg = "Data collection must be completed before hierarchy generation"
                self.storage.update_task_status(
                    request_id=request_id,
                    task_name=task_name,
                    status="error",
                    error=error_msg
                )
                return False
            
            # Mark as running
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="running",
                progress=0,
                log="Starting hierarchy generation..."
            )
            
            # Initialize services
            llm = LLMService(provider=config.llm_provider)
            vs = VectorStore()
            
            # Step 1: Query vector store for context
            self.log(request_id, task_name, "Querying vector store for context...")
            self.storage.update_task_status(request_id, task_name, "running", progress=20)
            
            context_docs = vs.query(config.prompt, n_results=20)
            context_str = "\n\n".join(context_docs)
            
            self.log(request_id, task_name, f"Retrieved {len(context_docs)} context documents")
            
            # Step 2: Generate hierarchy
            self.log(request_id, task_name, "Generating hierarchy and prompts...")
            self.storage.update_task_status(request_id, task_name, "running", progress=40)
            
            result_json_str = llm.generate_hierarchy_and_prompts(config.prompt, context_str)
            
            # Parse result
            import json
            try:
                result_data = json.loads(result_json_str)
            except json.JSONDecodeError:
                self.log(request_id, task_name, "Failed to parse hierarchy JSON, using raw string")
                result_data = {"raw": result_json_str}
            
            # Save hierarchy
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="running",
                data={"hierarchy": result_data},
                progress=60
            )
            
            # Step 3: Optional evaluation
            evaluation_data = None
            if config.include_evaluation and isinstance(result_data, dict) and "hierarchy" in result_data:
                self.log(request_id, task_name, "Running 8-expert evaluation...")
                self.storage.update_task_status(request_id, task_name, "running", progress=70)
                
                hierarchy_option = {
                    "agentName": "RAG Generator",
                    "perspective": "Data-Driven RAG",
                    "description": "Generated based on search data and RAG context.",
                    "hierarchy": result_data["hierarchy"]
                }
                
                def eval_log(msg):
                    self.log(request_id, task_name, f"[Eval] {msg}")
                
                has_korean = "ko" in config.language or any(ord(c) > 127 for c in config.prompt)
                evaluated_options = llm.evaluate_hierarchies(
                    [hierarchy_option],
                    has_korean=has_korean,
                    on_log=eval_log
                )
                
                evaluation_data = evaluated_options[0].get("evaluation", {})
                
                # Save evaluation
                self.storage.update_task_status(
                    request_id=request_id,
                    task_name=task_name,
                    status="running",
                    data={"evaluation": evaluation_data},
                    progress=90
                )
            
            # Mark as success
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="success",
                progress=100,
                log="Hierarchy generation completed successfully"
            )
            
            return True
            
        except Exception as e:
            error_msg = f"Error in hierarchy generation: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="error",
                error=error_msg,
                log="Hierarchy generation failed with error"
            )
            
            return False


class PromptGenerationTask(TaskProcessor):
    """
    Task 3: Prompt Generation
    - Load hierarchy from completed HierarchyGeneration task
    - Generate prompts based on hierarchy
    """
    
    def execute(self, request_id: str) -> bool:
        """Execute prompt generation task"""
        task_name = "promptGeneration"
        
        try:
            # Get request
            request = self.storage.get_request(request_id)
            if not request:
                print(f"Request {request_id} not found")
                return False
            
            config = request.config
            
            # Check if hierarchy generation is complete
            if request.tasks.hierarchyGeneration.status != "success":
                error_msg = "Hierarchy generation must be completed before prompt generation"
                self.storage.update_task_status(
                    request_id=request_id,
                    task_name=task_name,
                    status="error",
                    error=error_msg
                )
                return False
            
            # Mark as running
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="running",
                progress=0,
                log="Starting prompt generation..."
            )
            
            # Initialize services
            llm = LLMService(provider=config.llm_provider)
            
            # Get hierarchy data
            hierarchy_data = request.tasks.hierarchyGeneration.data.get("hierarchy")
            
            if not hierarchy_data:
                error_msg = "No hierarchy data found"
                self.storage.update_task_status(
                    request_id=request_id,
                    task_name=task_name,
                    status="error",
                    error=error_msg
                )
                return False
            
            self.log(request_id, task_name, "Generating prompts from hierarchy...")
            self.storage.update_task_status(request_id, task_name, "running", progress=30)
            
            # Convert hierarchy to CSV format for prompt generation
            # This is a simplified version - you may want to enhance this
            import json
            hierarchy_str = json.dumps(hierarchy_data, indent=2)
            
            # Generate prompts
            result_json_str = llm.generate_prompts_from_csv(hierarchy_str)
            
            # Parse result
            try:
                result_data = json.loads(result_json_str)
                prompts = result_data.get("prompts", [])
            except json.JSONDecodeError:
                self.log(request_id, task_name, "Failed to parse prompts JSON")
                prompts = []
            
            # Save prompts
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="running",
                data={"prompts": prompts},
                progress=80
            )
            
            self.log(request_id, task_name, f"Generated {len(prompts)} prompts")
            
            # Mark as success
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="success",
                progress=100,
                log="Prompt generation completed successfully"
            )
            
            return True
            
        except Exception as e:
            error_msg = f"Error in prompt generation: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            
            self.storage.update_task_status(
                request_id=request_id,
                task_name=task_name,
                status="error",
                error=error_msg,
                log="Prompt generation failed with error"
            )
            
            return False
