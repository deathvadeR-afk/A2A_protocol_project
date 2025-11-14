import os
from dotenv import load_dotenv
from typing import Optional, Any, Dict
from crewai import Agent, Task, Crew, LLM
from crewai.process import Process
from textwrap import dedent
from agents.external_apis import ExternalAPIs

# Load environment variables
load_dotenv()

class RealCrewAIAgent:
    def __init__(self, role, goal, backstory):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.external_apis = ExternalAPIs()
        
        # Initialize MCP client if available
        try:
            from mcp.client import MCPClient
            mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
            self.mcp_client = MCPClient(mcp_server_url)
        except ImportError:
            self.mcp_client = None
            
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
        
        # Create the LLM with OpenRouter configuration
        if self.api_key:
            self.llm = LLM(
                model="openrouter/meta-llama/llama-4-maverick:free",
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            # Fallback to default configuration
            self.llm = LLM(model="openrouter/meta-llama/llama-4-maverick:free")
        
        # Create the actual CrewAI agent with the LLM
        self.agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
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
        if any(keyword in task_lower for keyword in ["news", "latest", "recent", "current", "today", "trend"]):
            apis_to_use["use_news"] = True

        # Weather for location-based queries
        if any(keyword in task_lower for keyword in ["weather", "temperature", "climate"]):
            apis_to_use["use_weather"] = True
            # Try to extract city name
            words = task_lower.split()
            for i, word in enumerate(words):
                if word in ["in", "at", "for"] and i + 1 < len(words):
                    apis_to_use["city"] = words[i + 1].capitalize()

        # Geolocation for IP-based queries
        if any(keyword in task_lower for keyword in ["location", "geolocation", "ip", "where am i"]):
            apis_to_use["use_geolocation"] = True

        # Stock data for financial queries
        if any(keyword in task_lower for keyword in ["stock", "share price", "market value"]):
            apis_to_use["use_stock_data"] = True
            # Try to extract stock symbol (simple pattern matching)
            if "$" in task_lower:
                parts = task_lower.split("$")
                if len(parts) > 1:
                    apis_to_use["stock_symbol"] = parts[1].split()[0].upper()

        # Wikipedia for definitions and encyclopedic information
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

    def execute_task(self, task_description: str, auto_api_selection=True, **kwargs) -> Dict[str, Any]:
        """
        Execute a task using the actual CrewAI framework with external API integration
        """
        # Start Langfuse trace if available
        trace = None
        if self.langfuse:
            try:
                trace = self.langfuse.trace(
                    name="crewai-agent-task",
                    user_id="default_user",
                    metadata={
                        "agent_role": self.role,
                        "task_type": "research" if auto_api_selection else "manual",
                        "auto_api_selection": auto_api_selection
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to create Langfuse trace: {e}")
        
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

        # Create a task for the agent with enhanced context
        task = Task(
            description=dedent(f"""
                {enhanced_task}
                
                Consider using external data sources when relevant to enhance your research.
                Focus on accuracy and relevance to the task.
            """),
            agent=self.agent,
            expected_output="A comprehensive response to the task with relevant information and insights."
        )
        
        # Add Langfuse generation tracing if available
        generation = None
        if trace:
            try:
                generation = trace.generation(
                    name="crewai-task-execution",
                    model="meta-llama/llama-4-maverick:free",
                    input={
                        "task_description": task_description,
                        "enhanced_task": enhanced_task,
                        "auto_api_selection": auto_api_selection
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to create Langfuse generation: {e}")
        
        # Create a crew with just this agent
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        try:
            # Execute the task
            result = crew.kickoff()
            
            # Update Langfuse generation with output if available
            if generation:
                try:
                    generation.update(
                        output=str(result),
                        metadata={
                            "apis_used": [k for k, v in api_selection.items() if v and k.startswith("use_")],
                            "task_completed": True
                        }
                    )
                except Exception as e:
                    print(f"Warning: Failed to update Langfuse generation: {e}")
            
            return {
                "content": str(result),
                "agent": self.role,
                "task": task_description,
                "apis_used": [k for k, v in api_selection.items() if v and k.startswith("use_")]
            }
        except Exception as e:
            # Handle content moderation errors specifically
            error_str = str(e).lower()
            if "403" in error_str and ("moderation" in error_str or "flagged" in error_str):
                # Try with a simpler task description
                try:
                    simple_task = Task(
                        description=task_description,  # Use the original task without enhancements
                        agent=self.agent,
                        expected_output="A concise, professional response to the task."
                    )
                    
                    simple_crew = Crew(
                        agents=[self.agent],
                        tasks=[simple_task],
                        process=Process.sequential,
                        verbose=True
                    )
                    
                    simple_result = simple_crew.kickoff()
                    return {
                        "content": str(simple_result),
                        "agent": self.role,
                        "task": task_description,
                        "apis_used": [k for k, v in api_selection.items() if v and k.startswith("use_")],
                        "fallback_used": True
                    }
                except Exception as fallback_e:
                    return {
                        "error": f"Error executing task (fallback also failed): {str(e)} | Fallback error: {str(fallback_e)}",
                        "agent": self.role,
                        "task": task_description,
                        "apis_used": [k for k, v in api_selection.items() if v and k.startswith("use_")]
                    }
            else:
                return {
                    "error": f"Error executing task: {str(e)}",
                    "agent": self.role,
                    "task": task_description,
                    "apis_used": [k for k, v in api_selection.items() if v and k.startswith("use_")]
                }
