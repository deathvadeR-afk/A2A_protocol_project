import os
import requests
import wikipediaapi
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv()

class ExternalAPIs:
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY")
        self.ip_geolocation_api_key = os.getenv("IP_GEOLOCATION_API_KEY")
        self.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        
        # Initialize Wikipedia API with proper user agent
        self.wiki_wiki = wikipediaapi.Wikipedia(
            user_agent='MultiAgentSystem/1.0 (https://github.com/your-username/multi-agent-system)',
            language='en'
        )
        
        # Initialize Langfuse for observability
        try:
            from langfuse import Langfuse
            self.langfuse = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            )
        except ImportError:
            self.langfuse = None
        except Exception as e:
            print(f"Warning: Langfuse initialization failed: {e}")
            self.langfuse = None
    
    def tavily_search(self, query):
        """Search using Tavily API"""
        if not self.tavily_api_key:
            return "Tavily API key not configured"
            
        # Add Langfuse span for tracing if available
        span = None
        if self.langfuse:
            try:
                trace = self.langfuse.trace(name="external-api-call", user_id="default_user")
                span = trace.span(
                    name="tavily-search",
                    input={"query": query}
                )
            except Exception as e:
                print(f"Warning: Failed to create Langfuse span: {e}")
        
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "include_images": False,
            "include_raw_content": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                result = data.get("answer", "No answer found") or data.get("results", [])
                
                # Update Langfuse span with output if available
                if span:
                    try:
                        span.update(
                            output=result,
                            metadata={"status": "success"}
                        )
                    except Exception as e:
                        print(f"Warning: Failed to update Langfuse span: {e}")
                
                return result
            else:
                error_msg = f"Tavily API Error: {response.status_code} - {response.text}"
                
                # Update Langfuse span with error if available
                if span:
                    try:
                        span.update(
                            output=error_msg,
                            metadata={"status": "error", "error_code": response.status_code}
                        )
                    except Exception as e:
                        print(f"Warning: Failed to update Langfuse span: {e}")
                
                return error_msg
        except Exception as e:
            error_msg = f"Tavily Search Error: {str(e)}"
            
            # Update Langfuse span with error if available
            if span:
                try:
                    span.update(
                        output=error_msg,
                        metadata={"status": "exception", "error_type": type(e).__name__}
                    )
                except Exception as e:
                    print(f"Warning: Failed to update Langfuse span: {e}")
            
            return error_msg
    
    def get_news(self, category="technology"):
        """Get news using News API"""
        if not self.news_api_key:
            return "News API key not configured"
            
        # Add Langfuse span for tracing if available
        span = None
        if self.langfuse:
            try:
                trace = self.langfuse.trace(name="external-api-call", user_id="default_user")
                span = trace.span(
                    name="news-api-call",
                    input={"category": category}
                )
            except Exception as e:
                print(f"Warning: Failed to create Langfuse span: {e}")
        
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "category": category,
            "apiKey": self.news_api_key,
            "pageSize": 5
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                result = [{"title": a["title"], "description": a["description"]} for a in articles]
                
                # Update Langfuse span with output if available
                if span:
                    try:
                        span.update(
                            output=result,
                            metadata={"status": "success", "article_count": len(articles)}
                        )
                    except Exception as e:
                        print(f"Warning: Failed to update Langfuse span: {e}")
                
                return result
            else:
                error_msg = f"News API Error: {response.status_code} - {response.text}"
                
                # Update Langfuse span with error if available
                if span:
                    try:
                        span.update(
                            output=error_msg,
                            metadata={"status": "error", "error_code": response.status_code}
                        )
                    except Exception as e:
                        print(f"Warning: Failed to update Langfuse span: {e}")
                
                return error_msg
        except Exception as e:
            error_msg = f"News API Error: {str(e)}"
            
            # Update Langfuse span with error if available
            if span:
                try:
                    span.update(
                        output=error_msg,
                        metadata={"status": "exception", "error_type": type(e).__name__}
                    )
                except Exception as e:
                    print(f"Warning: Failed to update Langfuse span: {e}")
            
            return error_msg
    
    def get_weather(self, city):
        """Get weather using OpenWeather API"""
        if not self.openweather_api_key:
            return "OpenWeather API key not configured"
            
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": self.openweather_api_key,
            "units": "metric"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return {
                    "city": city,
                    "temperature": data["main"]["temp"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"]
                }
            else:
                return f"Weather API Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Weather API Error: {str(e)}"
    
    def get_geolocation(self, ip_address=""):
        """Get geolocation using IP Geolocation API"""
        if not self.ip_geolocation_api_key:
            return "IP Geolocation API key not configured"
            
        if ip_address:
            url = f"https://api.ipgeolocation.io/ipgeo?apiKey={self.ip_geolocation_api_key}&ip={ip_address}"
        else:
            url = f"https://api.ipgeolocation.io/ipgeo?apiKey={self.ip_geolocation_api_key}"
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return {
                    "country": data.get("country_name", ""),
                    "state": data.get("state_prov", ""),
                    "city": data.get("city", ""),
                    "latitude": data.get("latitude", ""),
                    "longitude": data.get("longitude", "")
                }
            else:
                return f"Geolocation API Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Geolocation API Error: {str(e)}"
    
    def get_stock_data(self, symbol):
        """Get stock data using Alpha Vantage API"""
        if not self.alpha_vantage_api_key:
            return "Alpha Vantage API key not configured"
            
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.alpha_vantage_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                quote = data.get("Global Quote", {})
                if quote:
                    return {
                        "symbol": quote.get("01. symbol", ""),
                        "price": quote.get("05. price", ""),
                        "change": quote.get("09. change", ""),
                        "change_percent": quote.get("10. change percent", "")
                    }
                else:
                    return "No stock data found"
            else:
                return f"Alpha Vantage API Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Alpha Vantage API Error: {str(e)}"
    
    def search_wikipedia(self, query):
        """Search Wikipedia"""
        try:
            page = self.wiki_wiki.page(query)
            if page.exists():
                return {
                    "title": page.title,
                    "summary": page.summary[:500] + "..." if len(page.summary) > 500 else page.summary
                }
            else:
                return "No Wikipedia page found for this query"
        except Exception as e:
            return f"Wikipedia Search Error: {str(e)}"
    
    def gemini_fallback(self, prompt):
        """Fallback to Gemini 2.0 Flash if OpenRouter fails"""
        if not self.google_api_key:
            return "Google API key not configured"
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.google_api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return f"Gemini API Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Gemini Fallback Error: {str(e)}"