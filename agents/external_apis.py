import os
import requests
import wikipediaapi
from dotenv import load_dotenv

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
    
    def tavily_search(self, query):
        """Search using Tavily API"""
        if not self.tavily_api_key:
            return "Tavily API key not configured"
            
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
                return data.get("answer", "No answer found") or data.get("results", [])
            else:
                return f"Tavily API Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Tavily Search Error: {str(e)}"
    
    def get_news(self, category="technology"):
        """Get news using News API"""
        if not self.news_api_key:
            return "News API key not configured"
            
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
                return [{"title": a["title"], "description": a["description"]} for a in articles]
            else:
                return f"News API Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"News API Error: {str(e)}"
    
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