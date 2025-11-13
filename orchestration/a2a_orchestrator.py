import json
import time
import uuid
from typing import Dict, Any, List, Optional
from agents.crewai_agent import SimpleCrewAIAgent
from agents.langgraph_agent import SimpleLangGraphAgent
from agents.google_adk_agent import SimpleGoogleADKAgent

# Task state enumeration
class TaskState:
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    UNKNOWN = "unknown"

class TaskStatus:
    def __init__(self, state: str, message: str = "", timestamp: Optional[str] = None):
        self.state = state
        self.message = message
        self.timestamp = timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

class Task:
    def __init__(self, task_id: str, session_id: Optional[str] = None, message: str = ""):
        self.id = task_id
        self.session_id = session_id or str(uuid.uuid4())
        self.status = TaskStatus(TaskState.SUBMITTED, "Task created")
        self.history: List[Dict] = []
        self.artifacts: List[Dict] = []
        self.metadata: Dict[str, Any] = {}
        self.message = message

class A2AOrchestrator:
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        # Initialize all agents
        self.researcher = SimpleCrewAIAgent(
            role="Research Analyst",
            goal="Analyze topics and provide comprehensive insights",
            backstory="You are an experienced analyst with expertise in research and analysis across multiple domains."
        )
        
        self.analyzer = SimpleLangGraphAgent(
            name="Data Analyzer",
            capabilities=["data analysis", "pattern recognition", "insight generation", "statistical modeling"]
        )
        
        self.expert = SimpleGoogleADKAgent(
            name="Domain Expert",
            expertise="technology trends, business strategy, and implementation best practices"
        )
        
        self.agents = {
            "researcher": self.researcher,
            "analyzer": self.analyzer,
            "expert": self.expert
        }
        
        # Task management
        self.tasks: Dict[str, Task] = {}
        
    def create_task(self, message: str, session_id: Optional[str] = None) -> Task:
        """Create a new task with proper A2A task structure"""
        task_id = str(uuid.uuid4())
        task = Task(task_id, session_id, message)
        self.tasks[task_id] = task
        return task
    
    def update_task_status(self, task_id: str, state: str, message: str = ""):
        """Update the status of a task"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus(state, message)
    
    def add_task_history(self, task_id: str, entry: Dict):
        """Add an entry to the task history"""
        if task_id in self.tasks:
            self.tasks[task_id].history.append(entry)
    
    def add_task_artifact(self, task_id: str, artifact: Dict):
        """Add an artifact to the task"""
        if task_id in self.tasks:
            artifact["index"] = len(self.tasks[task_id].artifacts)
            self.tasks[task_id].artifacts.append(artifact)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    def route_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a task to the appropriate agent based on task type
        """
        task_type = task.get("type", "general")
        content = task.get("content", "")
        
        if task_type == "research":
            # Route to researcher agent
            auto_api_selection = task.get("auto_api_selection", True)
            
            if auto_api_selection:
                # Let the agent automatically decide which APIs to use
                result = self.researcher.execute_task(content, auto_api_selection=True)
            else:
                # Use manual API selection
                use_web_search = task.get("use_web_search", False)
                use_news = task.get("use_news", False)
                use_weather = task.get("use_weather", False)
                use_geolocation = task.get("use_geolocation", False)
                use_stock_data = task.get("use_stock_data", False)
                use_wikipedia = task.get("use_wikipedia", False)
                city = task.get("city")
                ip_address = task.get("ip_address")
                stock_symbol = task.get("stock_symbol")
                wikipedia_query = task.get("wikipedia_query")
                
                result = self.researcher.execute_task(
                    content, 
                    auto_api_selection=False,
                    use_web_search=use_web_search,
                    use_news=use_news,
                    use_weather=use_weather,
                    use_geolocation=use_geolocation,
                    use_stock_data=use_stock_data,
                    use_wikipedia=use_wikipedia,
                    city=city,
                    ip_address=ip_address,
                    stock_symbol=stock_symbol,
                    wikipedia_query=wikipedia_query
                )
            return {
                "agent": "researcher",
                "result": result
            }
            
        elif task_type == "analysis":
            # Route to analyzer agent
            input_data = {
                "task": content,
                "data": task.get("data", [])
            }
            result = self.analyzer.process_input(input_data, user_id=self.user_id)
            return {
                "agent": "analyzer",
                "result": result
            }
            
        elif task_type == "expert_query":
            # Route to expert agent
            context = task.get("context", "")
            result = self.expert.respond_to_query(content, context, user_id=self.user_id)
            return {
                "agent": "expert",
                "result": result
            }
            
        else:
            # Default routing - send to expert for general queries
            result = self.expert.respond_to_query(content, user_id=self.user_id)
            return {
                "agent": "expert",
                "result": result
            }
    
    def collaborative_task_execution(self, task_description: str, conversation_history: Optional[List] = None) -> Dict[str, Any]:
        """
        Execute a task collaboratively where all agents work together
        """
        if conversation_history is None:
            conversation_history = []
        
        # Create A2A task
        task = self.create_task(task_description)
        task_id = task.id
        
        # Update task status
        self.update_task_status(task_id, TaskState.WORKING, "Starting collaborative task execution")
        
        # Step 1: Research Agent gathers information
        self.update_task_status(task_id, TaskState.WORKING, "Research agent gathering information")
        research_task = {
            "type": "research",
            "content": f"Research this topic comprehensively: {task_description}",
            "auto_api_selection": True
        }
        research_result = self.route_task(research_task)
        
        # Add to conversation history
        conversation_history.append({
            "task": research_task,
            "result": research_result
        })
        
        # Add to task history and artifacts
        self.add_task_history(task_id, {
            "role": "agent",
            "content": f"Research completed by {research_result['agent']}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        
        research_content = research_result["result"]["content"] if isinstance(research_result["result"], dict) else research_result["result"]
        self.add_task_artifact(task_id, {
            "name": "Research Findings",
            "description": "Comprehensive research findings from the research agent",
            "content": research_content,
            "type": "text/plain"
        })
        
        # Step 2: Analyzer processes the research findings
        self.update_task_status(task_id, TaskState.WORKING, "Analysis agent processing research findings")
        analysis_task = {
            "type": "analysis",
            "content": f"Analyze the research findings and identify key patterns and insights",
            "data": {
                "research_findings": research_content
            }
        }
        analysis_result = self.route_task(analysis_task)
        
        # Add to conversation history
        conversation_history.append({
            "task": analysis_task,
            "result": analysis_result
        })
        
        # Add to task history and artifacts
        self.add_task_history(task_id, {
            "role": "agent",
            "content": f"Analysis completed by {analysis_result['agent']}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        
        analysis_content = analysis_result["result"]["content"] if isinstance(analysis_result["result"], dict) else str(analysis_result["result"])
        self.add_task_artifact(task_id, {
            "name": "Analysis Results",
            "description": "Data analysis and pattern recognition results",
            "content": analysis_content,
            "type": "text/plain"
        })
        
        # Step 3: Expert provides recommendations based on research and analysis
        self.update_task_status(task_id, TaskState.WORKING, "Expert agent providing recommendations")
        expert_task = {
            "type": "expert_query",
            "content": f"Based on the research and analysis, provide expert recommendations and strategic insights for: {task_description}",
            "context": f"Research findings: {research_content}\n\nAnalysis results: {analysis_content}"
        }
        expert_result = self.route_task(expert_task)
        
        # Add to conversation history
        conversation_history.append({
            "task": expert_task,
            "result": expert_result
        })
        
        # Add to task history and artifacts
        self.add_task_history(task_id, {
            "role": "agent",
            "content": f"Expert recommendations provided by {expert_result['agent']}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        
        expert_content = expert_result["result"]["content"] if isinstance(expert_result["result"], dict) else expert_result["result"]
        self.add_task_artifact(task_id, {
            "name": "Expert Recommendations",
            "description": "Strategic recommendations and expert insights",
            "content": expert_content,
            "type": "text/plain"
        })
        
        # Mark task as completed
        self.update_task_status(task_id, TaskState.COMPLETED, "Collaborative task execution completed")
        
        return {
            "research": research_result,
            "analysis": analysis_result,
            "expert": expert_result,
            "final_output": expert_content,
            "conversation_history": conversation_history,
            "task_id": task_id
        }
    
    def coordinate_agents(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Coordinate multiple agents to handle a sequence of tasks
        """
        results = []
        
        for task in tasks:
            result = self.route_task(task)
            results.append(result)
            
            # Share context between agents where appropriate
            if result["agent"] == "researcher":
                # Share research findings with the analyzer
                research_content = result["result"]["content"] if isinstance(result["result"], dict) else result["result"]
                self.analyzer.update_state("recent_research", research_content)
                
            elif result["agent"] == "analyzer":
                # Share analysis with the expert
                if isinstance(result["result"], dict):
                    if "content" in result["result"]:
                        analysis_content = result["result"]["content"]
                    elif "error" in result["result"]:
                        analysis_content = f"Error occurred: {result['result']['error']}"
                    else:
                        analysis_content = str(result["result"])
                else:
                    analysis_content = str(result["result"])
                analysis_summary = analysis_content[:200] + "..." if len(analysis_content) > 200 else analysis_content
                self.expert.add_to_context(f"Analysis result: {analysis_summary}")
                
        return results

# Example usage
if __name__ == "__main__":
    # Create the orchestrator
    orchestrator = A2AOrchestrator()
    
    # Define a sequence of tasks
    tasks = [
        {
            "type": "research",
            "content": "Research the current state of AI agents and multi-agent systems"
        },
        {
            "type": "analysis",
            "content": "Analyze the benefits of using multiple specialized agents",
            "data": ["Specialization", "Collaboration", "Efficiency", "Scalability"]
        },
        {
            "type": "expert_query",
            "content": "Based on the research and analysis, what are your recommendations for implementing a multi-agent system?",
            "context": "We're building a system with CrewAI, LangGraph, and Google ADK agents."
        }
    ]
    
    # Coordinate the agents to handle the tasks
    results = orchestrator.coordinate_agents(tasks)
    
    # Print results
    for i, result in enumerate(results):
        print(f"Task {i+1} handled by {result['agent']}:")
        print(json.dumps(result['result'], indent=2))
        print("-" * 50)