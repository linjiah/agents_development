"""
Web Search Tool for Agents

This module provides a web search tool that can be used by agents.
In production, integrate with actual search APIs like Google Search API, SerpAPI, etc.
"""

import requests
from typing import Dict, List, Optional

class WebSearchTool:
    """Tool for performing web searches."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the web search tool.
        
        Args:
            api_key: API key for search service (e.g., SerpAPI, Google Custom Search)
        """
        self.api_key = api_key
    
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Perform a web search.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results with title, url, and snippet
        """
        # Placeholder implementation
        # In production, integrate with actual search API
        
        if not self.api_key:
            return self._mock_search(query, num_results)
        
        # Example: SerpAPI integration
        # try:
        #     params = {
        #         "q": query,
        #         "api_key": self.api_key,
        #         "num": num_results
        #     }
        #     response = requests.get("https://serpapi.com/search", params=params)
        #     data = response.json()
        #     
        #     results = []
        #     for item in data.get("organic_results", [])[:num_results]:
        #         results.append({
        #             "title": item.get("title", ""),
        #             "url": item.get("link", ""),
        #             "snippet": item.get("snippet", "")
        #         })
        #     return results
        # except Exception as e:
        #     print(f"Search error: {e}")
        #     return self._mock_search(query, num_results)
        
        return self._mock_search(query, num_results)
    
    def _mock_search(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """Mock search results for testing."""
        return [
            {
                "title": f"Result 1 for: {query}",
                "url": "https://example.com/result1",
                "snippet": f"This is a mock search result for the query: {query}"
            },
            {
                "title": f"Result 2 for: {query}",
                "url": "https://example.com/result2",
                "snippet": f"Another mock result providing information about: {query}"
            }
        ][:num_results]
    
    def search_and_summarize(self, query: str) -> str:
        """
        Perform a search and return a summarized result.
        
        Args:
            query: Search query
            
        Returns:
            Summarized search results as a string
        """
        results = self.search(query)
        
        if not results:
            return f"No results found for: {query}"
        
        summary = f"Search results for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            summary += f"{i}. {result['title']}\n"
            summary += f"   URL: {result['url']}\n"
            summary += f"   {result['snippet']}\n\n"
        
        return summary

# Example usage
if __name__ == "__main__":
    tool = WebSearchTool()
    results = tool.search("machine learning interview questions")
    print(tool.search_and_summarize("machine learning interview questions"))

