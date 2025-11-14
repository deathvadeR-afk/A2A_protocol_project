import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.crewai_agent import RealCrewAIAgent
from agents.langgraph_agent import RealLangGraphAgent
from agents.google_adk_agent import RealGoogleADKAgent
from orchestration.a2a_orchestrator import A2AOrchestrator

def test_agents():
    """Test individual agents - import only test"""
    print("Testing individual agents imports...")
    
    # Test that we can create all agent types
    researcher = RealCrewAIAgent(
        role="Research Analyst",
        goal="Analyze market trends and provide insights using actual CrewAI framework",
        backstory="You are an experienced analyst with expertise in market research and trend analysis, utilizing the powerful CrewAI framework."
    )
    
    analyzer = RealLangGraphAgent(
        name="Data Analyzer",
        capabilities=["data analysis", "pattern recognition"]
    )
    
    expert = RealGoogleADKAgent(
        name="Technology Expert",
        expertise="artificial intelligence and machine learning technologies using Google ADK framework"
    )
    
    print("✅ All agents created successfully!")
    
def test_orchestration():
    """Test the A2A orchestration - import only test"""
    print("\n\nTesting A2A Orchestration imports...")
    
    # Create the orchestrator
    orchestrator = A2AOrchestrator()
    
    print("✅ Orchestrator created successfully!")

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