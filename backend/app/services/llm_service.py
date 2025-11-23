import os
import json
from typing import List
from openai import OpenAI
import google.generativeai as genai

class LLMService:
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.openai_client = None
        self.gemini_model = None

        if self.provider.startswith("gpt"):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider.startswith("gemini"):
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            # Map frontend model names to official Google AI Studio model names
            # Note: gemini-1.5-x models are deprecated, use 2.5 or 3.0 models
            model_mapping = {
                "gemini-1.5-flash": "gemini-2.5-flash",  # Redirect to 2.5
                "gemini-1.5-pro": "gemini-2.5-flash",    # Redirect to 2.5
                "gemini-2.5-flash": "gemini-2.5-flash",
                "gemini-3-pro-preview": "gemini-3-pro-preview",
                "gemini": "gemini-2.5-flash"  # default to 2.5
            }
            
            model_name = model_mapping.get(self.provider, "gemini-2.5-flash")
            self.gemini_model = genai.GenerativeModel(model_name)

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
                    response = self.gemini_model.generate_content(full_prompt, generation_config={"response_mime_type": "application/json"})
                    print(f"Gemini Response: {response.text}") # Debug log
                    data = json.loads(response.text)
                    if isinstance(data, list):
                        return data
                    return data.get("keywords", [])
                except Exception as e:
                    print(f"Gemini Error: {e}")
                    if hasattr(e, 'response'):
                        print(f"Gemini Feedback: {e.response.prompt_feedback}")
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
                response = self.gemini_model.generate_content(full_prompt, generation_config={"response_mime_type": "application/json"})
                return response.text

        except Exception as e:
            print(f"Error generating prompts ({self.provider}): {e}")
            return "{}"
