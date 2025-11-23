import os
import time
import requests
import base64
from typing import List, Dict, Any

class DataForSEOClient:
    def __init__(self):
        self.login = os.getenv("DATAFORSEO_API_LOGIN")
        self.password = os.getenv("DATAFORSEO_API_PASSWORD")
        self.base_url = "https://api.dataforseo.com/v3"
        self.rate_limit_per_minute = 2000
        self.tokens = self.rate_limit_per_minute
        self.last_refill = time.time()

    def _get_auth_header(self):
        creds = f"{self.login}:{self.password}"
        return {
            "Authorization": f"Basic {base64.b64encode(creds.encode()).decode()}",
            "Content-Type": "application/json"
        }

    def _wait_for_token(self):
        """Simple token bucket rate limiter"""
        now = time.time()
        time_passed = now - self.last_refill
        
        # Refill tokens based on time passed
        # 2000 tokens per 60 seconds
        refill_amount = time_passed * (self.rate_limit_per_minute / 60.0)
        self.tokens = min(self.rate_limit_per_minute, self.tokens + refill_amount)
        self.last_refill = now

        if self.tokens < 1:
            sleep_time = (1 - self.tokens) / (self.rate_limit_per_minute / 60.0)
            time.sleep(sleep_time)
            self.tokens = 0
            self.last_refill = time.time()
        
        self.tokens -= 1

    def fetch_keyword_data(self, keyword: str, location_code: int, language_code: str, api_type: str = "google_search") -> Dict[str, Any]:
        """
        Fetches data for a single keyword based on the requested API type.
        """
        self._wait_for_token()
        
        endpoint = ""
        payload = []

        # Common payload structure
        base_payload = {
            "keyword": base64.b64encode(keyword.encode()).decode(),
            "location_code": location_code,
            "language_code": language_code,
        }

        if api_type == "google_search":
            endpoint = "/serp/google/organic/live/advanced"
            payload = [{**base_payload, "depth": 10}]
        
        elif api_type == "bing_search":
            endpoint = "/serp/bing/organic/live/advanced"
            payload = [{**base_payload, "depth": 10}]
            
        elif api_type == "naver_search":
            # Naver only supports Korean/Korea usually, but we pass params anyway
            endpoint = "/serp/naver/organic/live/advanced"
            payload = [{**base_payload, "depth": 10}]

        elif api_type == "google_ads":
            endpoint = "/keywords_data/google_ads/search_volume/live"
            payload = [{"keywords": [keyword], "location_code": location_code, "language_code": language_code}]

        elif api_type == "bing_ads":
            endpoint = "/keywords_data/bing/search_volume/live"
            payload = [{"keywords": [keyword], "location_code": location_code, "language_code": language_code}]

        elif api_type == "google_trends":
            endpoint = "/keywords_data/google/trends/explore/live"
            payload = [{"keywords": [keyword], "location_code": location_code, "language_code": language_code}]

        elif api_type == "facebook":
            # Social APIs often work differently, using app_data_google as a proxy or specific social endpoints if available.
            # DataforSEO doesn't have a direct "Facebook Search" API in the same way. 
            # We will use Google SERP with site:facebook.com as a robust workaround for "Social Media API" context
            endpoint = "/serp/google/organic/live/advanced"
            kw_encoded = base64.b64encode(f"site:facebook.com {keyword}".encode()).decode()
            payload = [{"keyword": kw_encoded, "location_code": location_code, "language_code": language_code, "depth": 10}]

        elif api_type == "reddit":
            endpoint = "/serp/google/organic/live/advanced"
            kw_encoded = base64.b64encode(f"site:reddit.com {keyword}".encode()).decode()
            payload = [{"keyword": kw_encoded, "location_code": location_code, "language_code": language_code, "depth": 10}]

        elif api_type == "google_reviews":
             # Using Google Maps Reviews API proxy
            endpoint = "/serp/google/maps/reviews/live/advanced"
            # This requires a data_id or specialized call. For simplicity in this RAG context, 
            # we'll search for the keyword on Maps to find a place, then get reviews.
            # But to keep it simple and stateless: we use Google Organic with "reviews" appended.
            kw_encoded = base64.b64encode(f"{keyword} reviews".encode()).decode()
            endpoint = "/serp/google/organic/live/advanced"
            payload = [{"keyword": kw_encoded, "location_code": location_code, "language_code": language_code, "depth": 10}]

        elif api_type == "amazon_reviews":
            endpoint = "/serp/amazon/organic/live/advanced"
            payload = [{**base_payload, "depth": 10}]

        else:
            # Default to Google Search
            endpoint = "/serp/google/organic/live/advanced"
            payload = [{**base_payload, "depth": 10}]

        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_auth_header(),
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching data for {keyword} ({api_type}): {e}")
            return {}

    def fetch_batch(self, keywords: List[str], location_code: int, language_code: str, apis: List[str]) -> List[Dict[str, Any]]:
        """
        Fetches data for a list of keywords across multiple APIs.
        """
        results = []
        for kw in keywords:
            # For each keyword, we pick ONE API from the list to diversify, 
            # or we could call ALL APIs for ALL keywords (expensive).
            # Requirement: "Call desired keyword... from DataforSEO".
            # Let's iterate through requested APIs for each keyword.
            for api in apis:
                data = self.fetch_keyword_data(kw, location_code, language_code, api)
                results.append({"keyword": kw, "api": api, "data": data})
        return results
