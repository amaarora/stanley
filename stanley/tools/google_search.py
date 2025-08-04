import json
import os
from typing import Annotated

import requests

from stanley.base_tool import Tool


class GoogleSearchTool(Tool):
    name = "google_search"
    description = "Use this tool to search google about an input query."

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        super().__init__()

    def execute(
        self,
        query: Annotated[str, "The query to be searched"],
        num_results: Annotated[int, "The number of results to retrieve"] = 5,
    ) -> dict:
        """Use Google search engine to search information for the given query."""
        if not self.api_key:
            raise ValueError("SERPER_API_KEY environment variable is required")

        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": num_results})
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        return response.json()
