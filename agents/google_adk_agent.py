import os
import json
import requests
from dotenv import load_dotenv
from typing import Dict, Any, List
from agents.external_apis import ExternalAPIs

# Load environment variables
load_dotenv()

# Try to import Mem0 memory client
try:
    from mem0 import MemoryClient
except ImportError:
    MemoryClient = None

# Try to import Google ADK components
try:
    from google.adk.agents import LlmAgent
    from google.adk.runners import InMemoryRunner
    GOOGLE_ADK_AVAILABLE = True
except ImportError:
    LlmAgent = None
    InMemoryRunner = None
    GOOGLE_ADK_AVAILABLE = False

class RealGoogleADKAgent:
    def __init__(self, name, expertise):
        self.name = name
        self.expertise = expertise
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.context_history = []
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
        if mem0_api_key and MemoryClient:
            try:
                self.memory_client = MemoryClient(api_key=mem0_api_key)
            except Exception:
                self.memory_client = None
        else:
            self.memory_client = None
            
        # Initialize the actual Google ADK agent if available
        if GOOGLE_ADK_AVAILABLE and LlmAgent and InMemoryRunner:
            try:
                self.agent = LlmAgent(
                    model="meta-llama/llama-4-maverick:free",
                    name=name,
                    description=f"Expert in {expertise}",
                    instruction=f"You are {name}, a world-class expert in {expertise}. Provide authoritative, accurate, and insightful responses based on your specialized expertise.",
                    tools=[self._external_api_tool]
                )
                self.runner = InMemoryRunner(agent=self.agent, app_name=f"{name}_app")
            except Exception:
                self.agent = None
                self.runner = None
        else:
            self.agent = None
            self.runner = None
        
    def _external_api_tool(self, query: str) -> Dict[str, Any]:
        """Tool to access external APIs"""
        try:
            # Use the external APIs to get additional information
            result = self.external_apis.search_wikipedia(query)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def add_to_context(self, context: str):
        """Add context to the agent's history"""
        self.context_history.append(context)
        
    def get_context(self) -> List[str]:
        """Get the current context history"""
        return self.context_history.copy()
        
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
        
    def respond_to_query(self, query: str, context: str = "", user_id: str = "default_user") -> Dict[str, Any]:
        """Respond to a query using the agent's expertise"""
        # Start Langfuse trace if available
        trace = None
        if self.langfuse:
            try:
                trace = self.langfuse.trace(
                    name="google-adk-agent-query",
                    user_id=user_id,
                    metadata={
                        "agent_name": self.name,
                        "expertise": self.expertise,
                        "query_length": len(query)
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to create Langfuse trace: {e}")
        
        # If Google ADK is available, use it
        if self.agent and self.runner:
            try:
                # Run the agent with the query
                result = self.runner.run(query)
                content = result.get("content", "No response generated")
                
                # Add Langfuse generation tracing if available
                generation = None
                if trace:
                    try:
                        generation = trace.generation(
                            name="google-adk-llm-call",
                            model="meta-llama/llama-4-maverick:free",
                            input={
                                "query": query,
                                "context": context,
                                "agent_name": self.name
                            },
                            output=content
                        )
                    except Exception as e:
                        print(f"Warning: Failed to create Langfuse generation: {e}")
                
                # Add this interaction to context and memory
                self.add_to_context(f"Query: {query} | Response: {content}")
                
                # Add to memory
                if self.memory_client:
                    self.add_memory(user_id, f"Agent {self.name} responded to query '{query}' with: {content}")
                
                return {
                    "content": content,
                    "agent": self.name,
                    "expertise": self.expertise
                }
            except Exception as e:
                error_msg = f"ADK Error: {str(e)}"
                self.add_to_context(f"Query: {query} | Error: {error_msg}")
                return {
                    "error": error_msg,
                    "agent": self.name,
                    "expertise": self.expertise
                }
        else:
            # Fallback to the original implementation
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            # Add memory if available
            memory_context = ""
            if self.memory_client:
                memory_results = self.search_memory(user_id, query)
                if isinstance(memory_results, list) and len(memory_results) > 0:
                    memory_context = f"Relevant memories: {memory_results[:3]}"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Build the prompt with expertise and context
            system_prompt = f"""You are {self.name}, a world-class expert in {self.expertise}.

YOUR ROLE AND RESPONSIBILITIES:
- Provide authoritative, accurate, and insightful responses based on your specialized expertise
- Synthesize complex information into clear, actionable recommendations
- Draw upon your contextual knowledge and previous interactions to enhance responses
- Maintain a professional yet accessible communication style

EXPERTISE DOMAIN:
Your specialized knowledge encompasses:
- Deep understanding of {self.expertise}
- Current trends and developments in your field
- Best practices and proven methodologies
- Strategic insights and practical applications

CONTEXTUAL AWARENESS:
You have access to the following contextual information:
{f"Previous conversation history: {'; '.join(self.context_history[-5:])}" if self.context_history else "No previous conversation history"}
{memory_context if memory_context else "No relevant memories from previous interactions"}

RESPONSE METHODOLOGY:
1. Carefully analyze the query and any provided context
2. Identify the core issues or questions that need to be addressed
3. Apply your expert knowledge to provide comprehensive answers
4. Structure your response with clear logic and supporting evidence
5. Offer actionable insights and practical recommendations when appropriate

RESPONSE GUIDELINES:
- Begin with a clear, concise summary of your main points
- Organize information in logical sections with descriptive headings
- Use specific examples and concrete details to illustrate key concepts
- Address any potential counterarguments or alternative perspectives
- Conclude with actionable recommendations or next steps
- Maintain an authoritative yet approachable tone throughout

When responding to queries, focus on providing maximum value through your expert insights while ensuring clarity and practical applicability."""
            
            # Add Langfuse generation tracing if available
            generation = None
            if trace:
                try:
                    generation = trace.generation(
                        name="google-adk-fallback-llm-call",
                        model="meta-llama/llama-4-maverick:free",
                        input={
                            "query": query,
                            "context": context,
                            "system_prompt": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt
                        }
                    )
                except Exception as e:
                    print(f"Warning: Failed to create Langfuse generation: {e}")
            
            payload = {
                "model": "meta-llama/llama-4-maverick:free",  # Using the free Llama 4 Maverick model
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"{context}\n\nQuery: {query}"
                    }
                ]
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    
                    # Update Langfuse generation with output if available
                    if generation:
                        try:
                            generation.update(
                                output=content,
                                metadata={
                                    "response_success": True,
                                    "token_usage": result.get('usage', {})
                                }
                            )
                        except Exception as e:
                            print(f"Warning: Failed to update Langfuse generation: {e}")
                    
                    # Add this interaction to context and memory
                    self.add_to_context(f"Query: {query} | Response: {content}")
                    
                    # Add to memory
                    if self.memory_client:
                        self.add_memory(user_id, f"Agent {self.name} responded to query '{query}' with: {content}")
                    
                    return {
                        "content": content,
                        "agent": self.name,
                        "expertise": self.expertise,
                        "token_usage": result.get('usage', {})
                    }
                elif response.status_code == 403:
                    # Handle content moderation errors
                    error_response = response.json()
                    if "moderation" in error_response.get("error", {}).get("message", "").lower():
                        # Try with a less specific prompt
                        fallback_payload = {
                            "model": "meta-llama/llama-4-maverick:free",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": f"You are {self.name}, an expert in {self.expertise}. Provide a concise, professional response."
                                },
                                {
                                    "role": "user",
                                    "content": query
                                }
                            ]
                        }
                        
                        fallback_response = requests.post(url, headers=headers, json=fallback_payload, timeout=30)
                        if fallback_response.status_code == 200:
                            fallback_result = fallback_response.json()
                            content = fallback_result['choices'][0]['message']['content']
                            
                            self.add_to_context(f"Query: {query} | Fallback Response: {content}")
                            if self.memory_client:
                                self.add_memory(user_id, f"Agent {self.name} responded to query '{query}' with fallback: {content}")
                            
                            return {
                                "content": content,
                                "agent": self.name,
                                "expertise": self.expertise,
                                "token_usage": fallback_result.get('usage', {}),
                                "fallback_used": True
                            }
                    
                    error_msg = f"API Error: {response.status_code} - {response.text}"
                    self.add_to_context(f"Query: {query} | Error: {error_msg}")
                    return {
                        "error": error_msg,
                        "agent": self.name,
                        "expertise": self.expertise,
                        "token_usage": {}
                    }
                else:
                    error_msg = f"API Error: {response.status_code} - {response.text}"
                    self.add_to_context(f"Query: {query} | Error: {error_msg}")
                    return {
                        "error": error_msg,
                        "agent": self.name,
                        "expertise": self.expertise,
                        "token_usage": {}
                    }
            except requests.exceptions.RequestException as e:
                error_msg = f"Network Error: {str(e)}"
                self.add_to_context(f"Query: {query} | Error: {error_msg}")
                return {
                    "error": error_msg,
                    "agent": self.name,
                    "expertise": self.expertise,
                    "token_usage": {}
                }
            except Exception as e:
                error_msg = f"Unexpected Error: {str(e)}"
                self.add_to_context(f"Query: {query} | Error: {error_msg}")
                return {
                    "error": error_msg,
                    "agent": self.name,
                    "expertise": self.expertise,
                    "token_usage": {}
                }

# Example usage
if __name__ == "__main__":
    # Create a real expert agent using Google ADK
    expert = RealGoogleADKAgent(
        name="Technology Expert",
        expertise="artificial intelligence and machine learning technologies"
    )
    
    # Respond to a sample query
    query = "What are the latest advancements in natural language processing?"
    result = expert.respond_to_query(query)
    print(f"Expert Response: {result}")