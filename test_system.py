import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.crewai_agent import SimpleCrewAIAgent
from agents.langgraph_agent import SimpleLangGraphAgent
from agents.google_adk_agent import SimpleGoogleADKAgent
from orchestration.a2a_orchestrator import A2AOrchestrator

def test_agents():
    """Test individual agents"""
    print("Testing individual agents...")
    
    # Test CrewAI agent
    print("\n1. Testing CrewAI Agent:")
    researcher = SimpleCrewAIAgent(
        role="Research Analyst",
        goal="Analyze market trends and provide insights",
        backstory="You are an experienced analyst with expertise in market research and trend analysis."
    )
    
    result = researcher.execute_task("What are the current trends in AI development?")
    print(f"Research Result: {result[:200]}...")
    
    # Test LangGraph agent
    print("\n2. Testing LangGraph Agent:")
    analyzer = SimpleLangGraphAgent(
        name="Data Analyzer",
        capabilities=["data analysis", "pattern recognition"]
    )
    
    input_data = {
        "task": "Analyze sales data",
        "data": [100, 150, 200, 175, 300, 250]
    }
    
    result = analyzer.process_input(input_data)
    print(f"Analysis Result: {result}")
    
    # Test Google ADK agent
    print("\n3. Testing Google ADK Agent:")
    expert = SimpleGoogleADKAgent(
        name="Technology Expert",
        expertise="artificial intelligence and machine learning technologies"
    )
    
    result = expert.respond_to_query("What are the latest advancements in natural language processing?")
    if "response" in result:
        print(f"Expert Response: {result['response'][:200]}...")
    else:
        print(f"Expert Response Error: {result}")

def test_orchestration():
    """Test the A2A orchestration"""
    print("\n\nTesting A2A Orchestration...")
    
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
        print(f"\nTask {i+1} handled by {result['agent']}:")
        if isinstance(result['result'], dict):
            print(f"Result: {result['result']}")
        else:
            print(f"Result: {result['result'][:200]}...")

def test_streamlit_app():
    """Test that the Streamlit app can be imported"""
    print("\n\nTesting Streamlit App Import...")
    try:
        # This is just to verify the file can be imported without syntax errors
        import frontend.streamlit_app
        print("Streamlit app imported successfully!")
    except Exception as e:
        print(f"Error importing Streamlit app: {e}")

if __name__ == "__main__":
    print("Running system tests...")
    
    try:
        test_agents()
        test_orchestration()
        test_streamlit_app()
        
        print("\n\n✅ All tests completed successfully!")
        print("\nTo run the Streamlit UI, use the following command:")
        print("streamlit run frontend/streamlit_app.py")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()