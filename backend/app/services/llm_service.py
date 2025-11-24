import os
import json
import requests
import re
from typing import List, Dict, Optional, Callable
from openai import OpenAI

class LLMService:
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.openai_client = None
        self.gemini_api_key = None
        self.gemini_model_name = None

        if self.provider.startswith("gpt"):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider.startswith("gemini"):
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
            # Map frontend model names to official Google AI Studio model names
            # Using v1 API which has better model support
            model_mapping = {
                "gemini-1.5-flash": "gemini-1.5-flash-latest",
                "gemini-1.5-pro": "gemini-1.5-pro-latest",
                "gemini-2.5-flash": "gemini-2.0-flash-exp",  # 2.5 doesn't exist, use 2.0
                "gemini-3-pro-preview": "gemini-exp-1206",  # Latest experimental model
                "gemini-3.0-preview": "gemini-exp-1206",
                "gemini": "gemini-1.5-flash-latest"  # default to stable model
            }
            
            self.gemini_model_name = model_mapping.get(self.provider, "gemini-1.5-flash-latest")

    def _call_gemini_api(self, prompt: str) -> str:
        """
        Calls Gemini REST API directly, matching the TypeScript implementation.
        Using v1 API for better model compatibility.
        """
        url = f"https://generativelanguage.googleapis.com/v1/models/{self.gemini_model_name}:generateContent?key={self.gemini_api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if not response.ok:
            raise Exception(f"Gemini API error: {response.status_code} {response.text}")
        
        json_response = response.json()
        return json_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

    def _clean_json_response(self, response_text: str) -> str:
        """
        Cleans the response text to extract JSON content, removing markdown code blocks.
        """
        # Remove markdown code blocks (```json ... ``` or ``` ... ```)
        cleaned_text = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", response_text, flags=re.DOTALL).strip()
        return cleaned_text

    def generate_keywords(self, prompt: str, base_keywords: str, count: int = 50) -> List[str]:
        """
        Generates related keywords based on the user prompt.
        """
        system_prompt = (
            "You are a keyword research expert. Generate a list of related search keywords "
            "based on the user's topic. Return ONLY a JSON array of strings. "
            f"Limit to {count} keywords."
        )
        
        user_content = f"Topic: {prompt}\nReference: {base_keywords}"

        try:
            if self.provider.startswith("gpt"):
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
                data = json.loads(content)
                return data.get("keywords", [])
            
            elif self.provider.startswith("gemini"):
                full_prompt = f"{system_prompt}\n\n{user_content}\n\nReturn JSON only."
                try:
                    response_text = self._call_gemini_api(full_prompt)
                    print(f"Gemini Response: {response_text}") # Debug log
                    
                    # Clean and parse JSON
                    cleaned_text = self._clean_json_response(response_text)
                    data = json.loads(cleaned_text)
                    
                    if isinstance(data, list):
                        return data
                    return data.get("keywords", [])
                except json.JSONDecodeError as e:
                    print(f"Gemini JSON parsing error: {e}")
                    print(f"Response text: {response_text}")
                    return []
                except Exception as e:
                    print(f"Gemini Error: {e}")
                    return []

        except Exception as e:
            print(f"Error generating keywords ({self.provider}): {e}")
            return []

    def generate_hierarchy_and_prompts(self, topic: str, context: str) -> str:
        """
        Generates a hierarchy and prompts based on the RAG context.
        Returns a JSON string with the structure.
        """
        system_prompt = (
            "You are an expert prompt engineer. Use the provided search data context to "
            "create a structured hierarchy of subtopics and generate high-quality, "
            "real-world prompts for each. "
            "Return a JSON object with 'hierarchy' (nested objects) and 'prompts' (list of objects)."
        )

        user_content = f"Topic: {topic}\n\nContext Data:\n{context}"

        try:
            if self.provider.startswith("gpt"):
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            
            elif self.provider.startswith("gemini"):
                full_prompt = f"{system_prompt}\n\n{user_content}\n\nReturn JSON only."
                response_text = self._call_gemini_api(full_prompt)
                return self._clean_json_response(response_text)

        except Exception as e:
            print(f"Error generating prompts ({self.provider}): {e}")
            return "{}"

    def evaluate_hierarchies(self, hierarchies: List[dict], has_korean: bool = False, on_log: Optional[Callable[[str], None]] = None) -> List[dict]:
        """
        Evaluates the generated hierarchies using 8 expert personas.
        Returns the hierarchies with an added 'evaluation' field.
        """
        if on_log: on_log(f"Starting 8-Expert Evaluation for {len(hierarchies)} hierarchies...")
        print(f"Evaluating {len(hierarchies)} hierarchies with 8 expert agents...")
        
        eval_prompt = ""
        if has_korean:
            eval_prompt = f"""당신은 8명의 전문가 에이전트로 구성된 평가 팀입니다. 다음 {len(hierarchies)}개의 키워드 계층 구조를 다양한 관점에서 평가하세요.

**8명의 평가 전문가:**
1. **SEO 전문가**: 검색 엔진 최적화 관점에서 키워드의 효과성 평가
2. **마케팅 전략가**: 마케팅 캠페인 및 ROI 관점에서 평가
3. **데이터 분석가**: 검색량, 경쟁도, 트렌드 데이터의 신뢰성 평가
4. **브랜드 전문가**: 브랜드 포지셔닝 및 인지도 관점에서 평가
5. **소비자 인사이트 연구원**: 소비자 행동 및 의도 반영도 평가
6. **콘텐츠 전략가**: 콘텐츠 구조 및 정보 아키텍처 평가
7. **AI 검색 최적화 전문가**: AI 검색 엔진(ChatGPT, Perplexity 등) 최적화 관점
8. **비즈니스 컨설턴트**: 비즈니스 가치 및 수익화 가능성 평가

평가 기준 (각 10점 만점):
1. 논리적 구조와 깊이 (Logical Structure)
2. 키워드 관련성과 포괄성 (Keyword Relevance)
3. 검색량 추정의 현실성 (Search Volume Realism)
4. 비즈니스 가치 (Business Value)

계층 구조들:
"""
            for i, h in enumerate(hierarchies):
                eval_prompt += f"\n[옵션 {i + 1}] - {h.get('agentName', 'Unknown')}\n관점: {h.get('perspective', 'Unknown')}\n설명: {h.get('description', 'Unknown')}\n"
            
            eval_prompt += """
각 계층 구조에 대해 **8명의 전문가 관점을 종합한 상세 평가**를 제공하세요.

다음 JSON 형식으로만 응답하세요:
{
  "evaluations": [
    {
      "optionNumber": 1,
      "scores": {
        "logicalStructure": 8,
        "keywordRelevance": 9,
        "searchVolumeRealism": 7,
        "businessValue": 8
      },
      "totalScore": 32,
      "reasoning": "8명의 전문가 관점에서 본 평가 근거...",
      "strengths": ["강점1", "강점2", "강점3"],
      "weaknesses": ["약점1", "약점2"],
      "hierarchyAnalysis": "계층 구조 분석..."
    }
  ]
}"""
        else:
            eval_prompt = f"""You are an evaluation team of 8 expert agents. Evaluate the following {len(hierarchies)} keyword hierarchies from diverse perspectives.

**8 Evaluation Experts:**
1. **SEO Specialist**: Evaluates keyword effectiveness from search engine optimization perspective
2. **Marketing Strategist**: Assesses from marketing campaign and ROI perspective
3. **Data Analyst**: Evaluates reliability of search volume, competition, and trend data
4. **Brand Expert**: Assesses from brand positioning and awareness perspective
5. **Consumer Insights Researcher**: Evaluates reflection of consumer behavior and intent
6. **Content Strategist**: Assesses content structure and information architecture
7. **AI Search Optimization Expert**: Evaluates optimization for AI search engines
8. **Business Consultant**: Assesses business value and monetization potential

Evaluation criteria (10 points each):
1. Logical structure and depth
2. Keyword relevance and coverage
3. Realistic search volume estimates
4. Business value

Hierarchies:
"""
            for i, h in enumerate(hierarchies):
                eval_prompt += f"\n[Option {i + 1}] - {h.get('agentName', 'Unknown')}\nPerspective: {h.get('perspective', 'Unknown')}\nDescription: {h.get('description', 'Unknown')}\n"

            eval_prompt += """
Provide detailed evaluation synthesizing 8 expert perspectives for each hierarchy.

Respond with ONLY this JSON format:
{
  "evaluations": [
    {
      "optionNumber": 1,
      "scores": {
        "logicalStructure": 8,
        "keywordRelevance": 9,
        "searchVolumeRealism": 7,
        "businessValue": 8
      },
      "totalScore": 32,
      "reasoning": "Evaluation reasoning from 8 experts...",
      "strengths": ["Strength 1", "Strength 2", "Strength 3"],
      "weaknesses": ["Weakness 1", "Weakness 2"],
      "hierarchyAnalysis": "Hierarchy analysis..."
    }
  ]
}"""

        try:
            if self.provider.startswith("gpt"):
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an expert evaluation system. Return JSON only."},
                        {"role": "user", "content": eval_prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
                eval_data = json.loads(content)
            
            elif self.provider.startswith("gemini"):
                response_text = self._call_gemini_api(eval_prompt)
                # Clean up markdown code blocks if present
                cleaned_text = self._clean_json_response(response_text)
                eval_data = json.loads(cleaned_text)
            
            # Merge evaluations back into hierarchies
            evaluations = eval_data.get("evaluations", [])
            evaluated_hierarchies = []
            
            for i, h in enumerate(hierarchies):
                evaluation = next((e for e in evaluations if e.get("optionNumber") == i + 1), {})
                h["evaluation"] = {
                    "scores": evaluation.get("scores", {}),
                    "totalScore": evaluation.get("totalScore", 0),
                    "reasoning": evaluation.get("reasoning", ""),
                    "strengths": evaluation.get("strengths", []),
                    "weaknesses": evaluation.get("weaknesses", []),
                    "hierarchyAnalysis": evaluation.get("hierarchyAnalysis", "")
                }
                evaluated_hierarchies.append(h)
                
            return evaluated_hierarchies

        except Exception as e:
            print(f"Error evaluating hierarchies ({self.provider}): {e}")
            # Return original hierarchies without evaluation if failed
            return hierarchies

    def generate_prompts_from_csv(self, csv_content: str) -> str:
        """
        Generates prompts based on the provided CSV hierarchy.
        Returns a JSON string with 'prompts' list.
        """
        system_prompt = (
            "You are an expert prompt engineer. You will be provided with a CSV representing a keyword hierarchy "
            "(Depth1, Depth2, Depth3). "
            "Your task is to generate high-quality, real-world prompts for each unique leaf node or key topic in the CSV. "
            "Return a JSON object with a 'prompts' key containing a list of objects, each with 'topic', 'type', and 'content' (the prompt text)."
        )

        user_content = f"CSV Hierarchy:\n{csv_content}"

        try:
            if self.provider.startswith("gpt"):
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            
            elif self.provider.startswith("gemini"):
                full_prompt = f"{system_prompt}\n\n{user_content}\n\nReturn JSON only."
                response_text = self._call_gemini_api(full_prompt)
                return self._clean_json_response(response_text)

        except Exception as e:
            print(f"Error generating prompts from CSV ({self.provider}): {e}")
            return '{"prompts": []}'
