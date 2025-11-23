import os
import json
import requests
from typing import List
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
            # Using the same models as in the TypeScript code
            model_mapping = {
                "gemini-1.5-flash": "gemini-1.5-flash",
                "gemini-1.5-pro": "gemini-1.5-pro",
                "gemini-2.5-flash": "gemini-2.5-flash",
                "gemini-3-pro-preview": "gemini-3-pro-preview",
                "gemini": "gemini-2.5-flash"  # default
            }
            
            self.gemini_model_name = model_mapping.get(self.provider, "gemini-2.5-flash")

    def _call_gemini_api(self, prompt: str) -> str:
        """
        Calls Gemini REST API directly, matching the TypeScript implementation.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model_name}:generateContent?key={self.gemini_api_key}"
        
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
                    
                    # Try to extract JSON from the response
                    data = json.loads(response_text)
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
                return response_text

        except Exception as e:
            print(f"Error generating prompts ({self.provider}): {e}")
            return "{}"
