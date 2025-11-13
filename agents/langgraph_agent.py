import os
import json
import requests
from dotenv import load_dotenv
from typing import Dict, Any
from agents.external_apis import ExternalAPIs
from mem0 import MemoryClient

# Load environment variables
load_dotenv()

class SimpleLangGraphAgent:
    def __init__(self, name, capabilities):
        self.name = name
        self.capabilities = capabilities
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.state = {}
        self.external_apis = ExternalAPIs()
        # Initialize Mem0 memory client
        mem0_api_key = os.getenv("M0_API_KEY")
        if mem0_api_key:
            self.memory_client = MemoryClient(api_key=mem0_api_key)
        else:
            self.memory_client = None
        
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
        
    def process_input(self, input_data: Dict[str, Any], user_id: str = "default_user") -> Dict[str, Any]:
        """Process input and return output based on agent capabilities"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Add memory if available
        memory_context = ""
        if self.memory_client:
            memory_results = self.search_memory(user_id, str(input_data))
            if isinstance(memory_results, list) and len(memory_results) > 0:
                memory_context = f"Relevant memories: {memory_results[:3]}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build the prompt based on capabilities and input
        prompt = f"You are {self.name}, an AI agent with the following capabilities: {', '.join(self.capabilities)}. "
        prompt += f"Current state: {json.dumps(self.state)}. "
        if memory_context:
            prompt += f"{memory_context}. "
        prompt += f"Input to process: {json.dumps(input_data)}. "
        prompt += "Respond with a JSON object containing your analysis and any updates to your state."
        
        payload = {
            "model": "openai/gpt-3.5-turbo",  # Using a standard model
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Add to memory
                if self.memory_client:
                    self.add_memory(user_id, f"Agent {self.name} processed: {input_data} and responded: {content}")
                
                # Try to parse the response as JSON
                try:
                    return {
                        "content": json.loads(content),
                        "token_usage": result.get('usage', {})
                    }
                except json.JSONDecodeError:
                    # If not valid JSON, return as text
                    return {
                        "content": {"response": content},
                        "token_usage": result.get('usage', {})
                    }
            else:
                return {
                    "error": f"API Error: {response.status_code} - {response.text}",
                    "token_usage": {}
                }
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Network Error: {str(e)}",
                "token_usage": {}
            }
        except Exception as e:
            return {
                "error": f"Unexpected Error: {str(e)}",
                "token_usage": {}
            }

# Example usage
if __name__ == "__main__":
    # Create a simple analyzer agent
    analyzer = SimpleLangGraphAgent(
        name="Data Analyzer",
        capabilities=["data analysis", "pattern recognition", "statistical modeling"]
    )
    
    # Process a sample input
    input_data = {
        "task": "Analyze sales data",
        "data": [100, 150, 200, 175, 300, 250]
    }
    
    result = analyzer.process_input(input_data)
    print(f"Analysis Result: {result}")