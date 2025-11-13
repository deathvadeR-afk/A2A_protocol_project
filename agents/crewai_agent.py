import os
import json
import requests
from dotenv import load_dotenv
from agents.external_apis import ExternalAPIs
from typing import Optional

# Load environment variables
load_dotenv()

class SimpleCrewAIAgent:
    def __init__(self, role, goal, backstory):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.external_apis = ExternalAPIs()
        
    def auto_select_apis(self, task_description):
        """Automatically determine which APIs to use based on task content"""
        task_lower = task_description.lower()
        apis_to_use = {
            "use_web_search": False,
            "use_news": False,
            "use_weather": False,
            "use_geolocation": False,
            "use_stock_data": False,
            "use_wikipedia": False,
            "city": None,
            "stock_symbol": None,
            "wikipedia_query": None
        }
        
        # Web search for general research queries
        if any(keyword in task_lower for keyword in ["research", "find", "search", "information", "about", "what is", "how to", "explain"]):
            apis_to_use["use_web_search"] = True
            
        # News for current events
        if any(keyword in task_lower for keyword in ["news", "latest", "recent", "current", "today", "update"]):
            apis_to_use["use_news"] = True
            
        # Weather for weather-related queries
        if any(keyword in task_lower for keyword in ["weather", "temperature", "forecast", "rain", "sunny", "cold", "hot"]):
            apis_to_use["use_weather"] = True
            # Try to extract city name
            cities = ["new york", "london", "tokyo", "paris", "berlin", "sydney", "los angeles", "chicago", "houston", "phoenix"]
            for city in cities:
                if city in task_lower:
                    apis_to_use["city"] = city.title()
                    break
            if not apis_to_use["city"]:
                apis_to_use["city"] = "New York"  # Default city
                
        # Geolocation for location-based queries
        if any(keyword in task_lower for keyword in ["location", "where", "country", "city", "state", "ip", "address"]):
            apis_to_use["use_geolocation"] = True
            
        # Stock data for financial queries
        if any(keyword in task_lower for keyword in ["stock", "price", "market", "share", "finance", "investment", "trading"]):
            apis_to_use["use_stock_data"] = True
            # Try to extract stock symbol
            stock_symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", "AMD", "INTC"]
            for symbol in stock_symbols:
                if symbol.lower() in task_lower:
                    apis_to_use["stock_symbol"] = symbol
                    break
            if not apis_to_use["stock_symbol"]:
                apis_to_use["stock_symbol"] = "AAPL"  # Default stock
                
        # Wikipedia for knowledge-based queries
        if any(keyword in task_lower for keyword in ["define", "meaning", "history", "biography", "scientist", "inventor", "theory"]):
            apis_to_use["use_wikipedia"] = True
            # Try to extract search term
            if "who is" in task_lower:
                parts = task_lower.split("who is")
                if len(parts) > 1:
                    apis_to_use["wikipedia_query"] = parts[1].strip()
            elif "what is" in task_lower:
                parts = task_lower.split("what is")
                if len(parts) > 1:
                    apis_to_use["wikipedia_query"] = parts[1].strip()
            else:
                # Use the entire task as query if no specific pattern
                apis_to_use["wikipedia_query"] = task_description[:50]  # Limit length
                
        return apis_to_use
        
    def execute_task(self, task_description, auto_api_selection=True, **kwargs):
        """Execute a task using the OpenRouter API with a free model and Gemini fallback"""
        # Automatically select APIs if enabled
        if auto_api_selection:
            api_selection = self.auto_select_apis(task_description)
            # Override with any manually provided kwargs
            api_selection.update(kwargs)
        else:
            # Use manually provided kwargs or defaults
            api_selection = {
                "use_web_search": kwargs.get("use_web_search", False),
                "use_news": kwargs.get("use_news", False),
                "use_weather": kwargs.get("use_weather", False),
                "use_geolocation": kwargs.get("use_geolocation", False),
                "use_stock_data": kwargs.get("use_stock_data", False),
                "use_wikipedia": kwargs.get("use_wikipedia", False),
                "city": kwargs.get("city"),
                "ip_address": kwargs.get("ip_address"),
                "stock_symbol": kwargs.get("stock_symbol"),
                "wikipedia_query": kwargs.get("wikipedia_query")
            }
        
        # Extract API parameters
        use_web_search = api_selection["use_web_search"]
        use_news = api_selection["use_news"]
        use_weather = api_selection["use_weather"]
        use_geolocation = api_selection["use_geolocation"]
        use_stock_data = api_selection["use_stock_data"]
        use_wikipedia = api_selection["use_wikipedia"]
        city = api_selection["city"]
        ip_address = api_selection.get("ip_address")
        stock_symbol = api_selection["stock_symbol"]
        wikipedia_query = api_selection["wikipedia_query"]
        
        # Enhance task with external data if requested
        enhanced_task = task_description
        
        if use_web_search:
            search_results = self.external_apis.tavily_search(task_description)
            enhanced_task = f"Task: {task_description}\n\nRelevant web search results: {search_results}"
            
        if use_news:
            news_results = self.external_apis.get_news()
            enhanced_task = f"Task: {task_description}\n\nLatest tech news: {news_results}"
            
        if use_weather and city:
            weather_results = self.external_apis.get_weather(city)
            enhanced_task = f"Task: {task_description}\n\nWeather in {city}: {weather_results}"
            
        if use_geolocation:
            geo_results = self.external_apis.get_geolocation(ip_address or "")
            enhanced_task = f"Task: {task_description}\n\nGeolocation info: {geo_results}"
            
        if use_stock_data and stock_symbol:
            stock_results = self.external_apis.get_stock_data(stock_symbol)
            enhanced_task = f"Task: {task_description}\n\nStock data for {stock_symbol}: {stock_results}"
            
        if use_wikipedia and wikipedia_query:
            wiki_results = self.external_apis.search_wikipedia(wikipedia_query)
            enhanced_task = f"Task: {task_description}\n\nWikipedia info: {wiki_results}"
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "meta-llama/llama-4-maverick:free",  # Using the free Llama 4 Maverick model
            "messages": [
                {
                    "role": "system",
                    "content": f"You are {self.role}. {self.backstory}. Your goal is to {self.goal}."
                },
                {
                    "role": "user",
                    "content": enhanced_task
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return {
                    "content": result['choices'][0]['message']['content'],
                    "token_usage": result.get('usage', {}),
                    "apis_used": [k for k, v in api_selection.items() if v and k.startswith("use_")]
                }
            else:
                # Fallback to Gemini if OpenRouter fails
                fallback_result = self.external_apis.gemini_fallback(enhanced_task)
                return {
                    "content": fallback_result,
                    "token_usage": {},
                    "fallback_used": True,
                    "apis_used": [k for k, v in api_selection.items() if v and k.startswith("use_")]
                }
        except requests.exceptions.RequestException as e:
            # Fallback to Gemini if OpenRouter fails
            fallback_result = self.external_apis.gemini_fallback(enhanced_task)
            return {
                "content": fallback_result,
                "token_usage": {},
                "fallback_used": True,
                "error": str(e),
                "apis_used": [k for k, v in api_selection.items() if v and k.startswith("use_")]
            }
        except Exception as e:
            # Fallback to Gemini if OpenRouter fails
            fallback_result = self.external_apis.gemini_fallback(enhanced_task)
            return {
                "content": fallback_result,
                "token_usage": {},
                "fallback_used": True,
                "error": str(e),
                "apis_used": [k for k, v in api_selection.items() if v and k.startswith("use_")]
            }

# Example usage
if __name__ == "__main__":
    # Create a simple researcher agent
    researcher = SimpleCrewAIAgent(
        role="Research Analyst",
        goal="Analyze market trends and provide insights",
        backstory="You are an experienced analyst with expertise in market research and trend analysis."
    )
    
    # Execute a sample task
    task = "Analyze the current trends in AI development and provide a brief summary."
    result = researcher.execute_task(task)
    print(f"Research Result: {result}")