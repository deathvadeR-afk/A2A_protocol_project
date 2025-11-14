import os
import json
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional, TypedDict
from agents.external_apis import ExternalAPIs

# Try to import LangGraph components
try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import HumanMessage, AIMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    StateGraph = None
    END = None
    HumanMessage = None
    AIMessage = None
    LANGGRAPH_AVAILABLE = False

# Try to import ChatOpenAI, but provide fallback if not available
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    ChatOpenAI = None
    OPENAI_AVAILABLE = False

# Load environment variables
load_dotenv()

# Define the state structure
class AgentState(TypedDict):
    input_data: Dict[str, Any]
    analysis: str
    patterns: List[str]
    insights: List[str]
    recommendations: List[str]
    user_id: str

class RealLangGraphAgent:
    def __init__(self, name: str, capabilities: List[str]):
        self.name = name
        self.capabilities = capabilities
        self.state = {}
        self.external_apis = ExternalAPIs()
        
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
        
        # Initialize Mem0 memory client
        mem0_api_key = os.getenv("M0_API_KEY")
        try:
            from mem0 import MemoryClient
            if mem0_api_key:
                self.memory_client = MemoryClient(api_key=mem0_api_key)
            else:
                self.memory_client = None
        except ImportError:
            self.memory_client = None
        
        # Initialize the model if available
        if OPENAI_AVAILABLE and ChatOpenAI:
            try:
                self.model = ChatOpenAI(
                    model="meta-llama/llama-4-maverick:free",
                    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                    openai_api_base="https://openrouter.ai/api/v1"
                )
            except Exception:
                self.model = None
        else:
            self.model = None
        
        # Initialize the graph if LangGraph is available
        if LANGGRAPH_AVAILABLE and StateGraph and END:
            try:
                # Initialize the graph
                self.graph = StateGraph(AgentState)
                
                # Add nodes to the graph
                self.graph.add_node("analyze", self._analyze_node)
                self.graph.add_node("generate_response", self._generate_response_node)
                
                # Add edges
                self.graph.add_edge("analyze", "generate_response")
                self.graph.set_entry_point("analyze")
                self.graph.add_edge("generate_response", END)
                
                # Compile the graph
                self.app = self.graph.compile()
            except Exception:
                self.app = None
        else:
            self.app = None
        
    def update_state(self, key: str, value: Any):
        """Update the agent's state"""
        self.state[key] = value

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the agent"""
        return self.state.copy()
        
    def add_memory(self, user_id: str, message: str):
        """Add a memory using Mem0"""
        if self.memory_client:
            try:
                result = self.memory_client.add(message, user_id=user_id)
                return result
            except Exception as e:
                return f"Memory Error: {str(e)}"
        return "Memory client not configured"
        
    def search_memory(self, user_id: str, query: str):
        """Search memory using Mem0"""
        if self.memory_client:
            try:
                results = self.memory_client.search(query, user_id=user_id)
                return results
            except Exception as e:
                return f"Memory Search Error: {str(e)}"
        return "Memory client not configured"
        
    def _analyze_node(self, state: AgentState) -> Dict[str, Any]:
        """Analyze the input data"""
        input_data = state["input_data"]
        
        # Perform analysis using external APIs if needed
        analysis = f"Analysis of {input_data.get('task', 'data')}"
        patterns = ["Pattern 1", "Pattern 2"]
        insights = ["Insight 1", "Insight 2"]
        
        # If we have a model, use it for analysis
        if self.model:
            try:
                prompt = f"Analyze the following data and identify key patterns and insights: {input_data}"
                if HumanMessage:
                    response = self.model.invoke([HumanMessage(content=prompt)])
                    analysis = response.content
            except Exception as e:
                analysis = f"Analysis failed: {str(e)}"
        
        return {
            "analysis": analysis,
            "patterns": patterns,
            "insights": insights
        }
    
    def _generate_response_node(self, state: AgentState) -> Dict[str, Any]:
        """Generate the final response"""
        recommendations = ["Recommendation 1", "Recommendation 2"]
        
        # If we have a model, use it for generating recommendations
        if self.model:
            try:
                prompt = f"Based on this analysis: {state.get('analysis', '')}, generate actionable recommendations."
                if HumanMessage:
                    response = self.model.invoke([HumanMessage(content=prompt)])
                    recommendations = [response.content]
            except Exception as e:
                recommendations = [f"Recommendation generation failed: {str(e)}"]
        
        response = {
            "analysis": state.get("analysis", ""),
            "patterns": state.get("patterns", []),
            "insights": state.get("insights", []),
            "recommendations": recommendations
        }
        
        return {"content": response}
    
    def process_input(self, input_data: Dict[str, Any], user_id: str = "default_user") -> Dict[str, Any]:
        """Process input using the LangGraph framework"""
        # Start Langfuse trace if available
        trace = None
        if self.langfuse:
            try:
                trace = self.langfuse.trace(
                    name="langgraph-agent-processing",
                    user_id=user_id,
                    metadata={
                        "agent_name": self.name,
                        "capabilities": self.capabilities,
                        "input_type": input_data.get("type", "unknown")
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to create Langfuse trace: {e}")
        
        # If LangGraph is available, use it
        if self.app:
            try:
                # Initialize the state
                initial_state = {
                    "input_data": input_data,
                    "user_id": user_id
                }
                
                # Add Langfuse span for graph execution if available
                span = None
                if trace:
                    try:
                        span = trace.span(
                            name="langgraph-execution",
                            input=initial_state
                        )
                    except Exception as e:
                        print(f"Warning: Failed to create Langfuse span: {e}")
                
                # Run the graph
                result = self.app.invoke(initial_state)
                
                # Update Langfuse span with output if available
                if span:
                    try:
                        span.update(
                            output=result.get("content", {}),
                            metadata={
                                "execution_success": True,
                                "agent_name": self.name
                            }
                        )
                    except Exception as e:
                        print(f"Warning: Failed to update Langfuse span: {e}")
                
                # Add to memory
                if self.memory_client:
                    self.add_memory(user_id, f"Agent {self.name} processed: {input_data} and responded: {result.get('content', {})}")
                
                return {
                    "content": result.get("content", {}),
                    "agent": self.name,
                    "capabilities": self.capabilities
                }
            except Exception as e:
                # Handle content moderation errors specifically
                error_str = str(e).lower()
                if "403" in error_str and ("moderation" in error_str or "flagged" in error_str):
                    # Try with a simpler prompt in the fallback implementation
                    try:
                        # Use the fallback implementation with a simpler approach
                        analysis = f"Analysis of {input_data.get('task', 'data')}"
                        patterns = ["Pattern 1", "Pattern 2"]
                        insights = ["Insight 1", "Insight 2"]
                        recommendations = ["Recommendation 1", "Recommendation 2"]
                        
                        # If we have a model, use it with a simpler prompt
                        if self.model:
                            try:
                                # Simple analysis with minimal prompt
                                prompt = f"Analyze: {input_data.get('task', 'data')}"
                                if HumanMessage:
                                    response = self.model.invoke([HumanMessage(content=prompt)])
                                    analysis = response.content
                                
                                # Simple recommendations
                                prompt = f"Recommendations based on: {analysis}"
                                if HumanMessage:
                                    response = self.model.invoke([HumanMessage(content=prompt)])
                                    recommendations = [response.content]
                            except Exception as model_e:
                                analysis = f"Analysis with simplified prompt failed: {str(model_e)}"
                                recommendations = [f"Recommendation generation failed: {str(model_e)}"]
                        
                        response = {
                            "analysis": analysis,
                            "patterns": patterns,
                            "insights": insights,
                            "recommendations": recommendations
                        }
                        
                        # Add to memory
                        if self.memory_client:
                            self.add_memory(user_id, f"Agent {self.name} processed: {input_data} with fallback and responded: {response}")
                        
                        return {
                            "content": response,
                            "agent": self.name,
                            "capabilities": self.capabilities,
                            "fallback_used": True
                        }
                    except Exception as fallback_e:
                        return {
                            "error": f"Error processing input (fallback also failed): {str(e)} | Fallback error: {str(fallback_e)}",
                            "agent": self.name,
                            "capabilities": self.capabilities
                        }
                else:
                    return {
                        "error": f"Error processing input: {str(e)}",
                        "agent": self.name,
                        "capabilities": self.capabilities
                    }
        else:
            # Fallback implementation
            try:
                # Simple implementation without LangGraph
                analysis = f"Analysis of {input_data.get('task', 'data')}"
                patterns = ["Pattern 1", "Pattern 2"]
                insights = ["Insight 1", "Insight 2"]
                recommendations = ["Recommendation 1", "Recommendation 2"]
                
                # If we have a model, use it
                if self.model:
                    try:
                        # Analysis with a simpler prompt to avoid moderation issues
                        prompt = f"Analyze: {input_data.get('task', 'data')}"
                        if HumanMessage:
                            response = self.model.invoke([HumanMessage(content=prompt)])
                            analysis = response.content
                        
                        # Recommendations with a simpler prompt
                        prompt = f"Recommendations based on: {analysis}"
                        if HumanMessage:
                            response = self.model.invoke([HumanMessage(content=prompt)])
                            recommendations = [response.content]
                    except Exception as e:
                        analysis = f"Analysis failed: {str(e)}"
                        recommendations = [f"Recommendation generation failed: {str(e)}"]
                
                response = {
                    "analysis": analysis,
                    "patterns": patterns,
                    "insights": insights,
                    "recommendations": recommendations
                }
                
                # Add to memory
                if self.memory_client:
                    self.add_memory(user_id, f"Agent {self.name} processed: {input_data} and responded: {response}")
                
                return {
                    "content": response,
                    "agent": self.name,
                    "capabilities": self.capabilities
                }
            except Exception as e:
                return {
                    "error": f"Error processing input: {str(e)}",
                    "agent": self.name,
                    "capabilities": self.capabilities
                }
