import streamlit as st
import json
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.a2a_orchestrator import A2AOrchestrator

# Initialize the orchestrator
@st.cache_resource
def get_orchestrator():
    return A2AOrchestrator(user_id=st.session_state.get("user_id", "default_user"))

def format_agent_output(result_data):
    """Format agent output for better presentation"""
    if isinstance(result_data, dict):
        if "content" in result_data:
            content = result_data["content"]
            if isinstance(content, dict):
                return format_dict_content(content)
            else:
                return str(content)
        elif "response" in result_data:
            return str(result_data["response"])
        else:
            return json.dumps(result_data, indent=2)
    else:
        return str(result_data)

def format_dict_content(content_dict):
    """Format dictionary content for better presentation"""
    if isinstance(content_dict, dict):
        # Check for common response formats
        if "summary" in content_dict:
            return content_dict["summary"]
        elif "answer" in content_dict:
            return content_dict["answer"]
        elif "response" in content_dict:
            return content_dict["response"]
        elif "title" in content_dict and "summary" in content_dict:
            return f"**{content_dict['title']}**\n\n{content_dict['summary']}"
        else:
            # Format as key-value pairs for readability
            formatted = ""
            for key, value in content_dict.items():
                formatted += f"**{key.replace('_', ' ').title()}:** {value}\n\n"
            return formatted
    return str(content_dict)

def format_task_output(task_data):
    """Format task data for better presentation"""
    if isinstance(task_data, dict):
        formatted = ""
        for key, value in task_data.items():
            if key not in ["auto_api_selection"]:  # Skip internal parameters
                formatted += f"**{key.replace('_', ' ').title()}:** {value}\n\n"
        return formatted
    return str(task_data)

def main():
    st.set_page_config(page_title="Multi-Agent System", page_icon="🤖", layout="wide")
    
    st.title("🤖 Multi-Agent System with A2A Protocol")
    st.markdown("""
    This system demonstrates the coordination of three AI agents using actual frameworks:
    - **Research Agent** (CrewAI Framework) - Specialized in research and information gathering
    - **Analysis Agent** (LangGraph Framework) - Specialized in data analysis and pattern recognition
    - **Expert Agent** (Google ADK Framework) - Specialized in domain expertise and strategic recommendations
    
    Tasks are orchestrated using a simplified A2A protocol with collaborative agent communication.
    """)
    
    # Add information about the frameworks
    with st.expander("ℹ️ About the Agent Frameworks", expanded=False):
        st.markdown("""
        This system uses actual industry-standard frameworks for each agent:
        
        - **CrewAI Framework**: A framework for orchestrating role-playing AI agents. 
          Agents are given roles, goals, and backstories to fulfill their tasks.
          
        - **LangGraph Framework**: A library for building stateful, multi-step AI applications. 
          It provides precise control over agent workflows and state management.
          
        - **Google ADK Framework**: Google's Agent Development Kit for building sophisticated AI agents. 
          It provides tools for creating agents with specialized expertise and capabilities.
        """)
    
    # Initialize session state
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = get_orchestrator()
    
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = "default_user"
    
    # User ID input
    st.sidebar.header("User Configuration")
    user_id = st.sidebar.text_input("User ID", st.session_state.user_id)
    st.session_state.user_id = user_id
    st.session_state.orchestrator.user_id = user_id
    
    # Sidebar for agent selection
    st.sidebar.header("Agent Configuration")
    agent_type = st.sidebar.selectbox(
        "Select Agent Type",
        ["Auto-route", "Research Agent", "Analysis Agent", "Expert Agent", "Collaborative Execution"]
    )
    
    # API Selection Mode (only for individual agents)
    auto_selection = True
    if agent_type != "Collaborative Execution":
        st.sidebar.subheader("API Selection Mode")
        auto_api_selection = st.sidebar.radio(
            "API Selection Method",
            ["Automatic (Smart Detection)", "Manual (User Control)"],
            index=0  # Default to automatic
        )
        
        auto_selection = (auto_api_selection == "Automatic (Smart Detection)")
    
    # External API options for Research Agent (only shown in manual mode)
    use_web_search = False
    use_news = False
    use_weather = False
    use_geolocation = False
    use_stock_data = False
    use_wikipedia = False
    city = None
    ip_address = None
    stock_symbol = None
    wikipedia_query = None
    
    if agent_type == "Research Agent" and not auto_selection:
        st.sidebar.subheader("External API Options")
        use_web_search = st.sidebar.checkbox("Use Tavily Search")
        use_news = st.sidebar.checkbox("Get Latest News")
        use_weather = st.sidebar.checkbox("Get Weather Data")
        use_geolocation = st.sidebar.checkbox("Get Geolocation")
        use_stock_data = st.sidebar.checkbox("Get Stock Data")
        use_wikipedia = st.sidebar.checkbox("Search Wikipedia")
        
        if use_weather:
            city = st.sidebar.text_input("City for Weather", "New York")
            
        if use_geolocation:
            ip_address = st.sidebar.text_input("IP Address for Geolocation", "")
            
        if use_stock_data:
            stock_symbol = st.sidebar.text_input("Stock Symbol", "AAPL")
            
        if use_wikipedia:
            wikipedia_query = st.sidebar.text_input("Wikipedia Search Query", "Artificial Intelligence")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Task Input")
        
        # Task input
        task_input = st.text_area(
            "Enter your task:",
            height=150,
            placeholder="Example: What's the weather like in New York today? Or, Research the latest advancements in AI..."
        )
        
        # Additional parameters based on agent type
        task_params = {}
        if agent_type == "Analysis Agent":
            st.subheader("Analysis Data")
            data_input = st.text_area(
                "Enter data for analysis (comma-separated):",
                placeholder="Example: 10, 20, 30, 40, 50"
            )
            if data_input:
                try:
                    task_params["data"] = [float(x.strip()) for x in data_input.split(",")]
                except:
                    st.warning("Could not parse data. Please enter comma-separated numbers.")
        
        elif agent_type == "Expert Agent":
            st.subheader("Additional Context")
            context_input = st.text_area(
                "Provide additional context:",
                placeholder="Any background information for the expert..."
            )
            if context_input:
                task_params["context"] = context_input
        
        # Submit button
        if st.button("Submit Task", type="primary"):
            if task_input:
                if agent_type == "Collaborative Execution":
                    # Execute collaborative task
                    with st.spinner("Agents working together..."):
                        result = st.session_state.orchestrator.collaborative_task_execution(
                            task_input, 
                            st.session_state.conversation_history
                        )
                        
                        # Update conversation history
                        st.session_state.conversation_history = result["conversation_history"]
                        
                        # Show final output
                        st.success("Collaborative task completed!")
                        st.subheader("Final Expert Recommendation")
                        st.markdown(format_agent_output(result["final_output"]))
                        
                        # Add to conversation history
                        st.session_state.conversation_history.append({
                            "task": {"type": "collaborative", "content": task_input},
                            "result": {"final_output": result["final_output"]}
                        })
                else:
                    # Prepare task based on agent type
                    task = {"content": task_input}
                    
                    if agent_type == "Research Agent":
                        task["type"] = "research"
                        # Add API selection mode
                        task["auto_api_selection"] = auto_selection
                        if not auto_selection:
                            # Add external API parameters for manual mode
                            task["use_web_search"] = use_web_search
                            task["use_news"] = use_news
                            task["use_weather"] = use_weather
                            task["city"] = city
                            task["use_geolocation"] = use_geolocation
                            task["ip_address"] = ip_address
                            task["use_stock_data"] = use_stock_data
                            task["stock_symbol"] = stock_symbol
                            task["use_wikipedia"] = use_wikipedia
                            task["wikipedia_query"] = wikipedia_query
                    elif agent_type == "Analysis Agent":
                        task["type"] = "analysis"
                        task.update(task_params)
                    elif agent_type == "Expert Agent":
                        task["type"] = "expert_query"
                        task.update(task_params)
                    else:
                        task["type"] = "general"
                    
                    # Execute task
                    with st.spinner("Processing your task..."):
                        result = st.session_state.orchestrator.route_task(task)
                    
                    # Add to conversation history
                    st.session_state.conversation_history.append({
                        "task": task,
                        "result": result
                    })
                    
                    st.success("Task completed!")
            else:
                st.warning("Please enter a task.")
    
    with col2:
        st.header("Agent Status")
        
        # Display agent statuses with framework information
        st.subheader("Active Agents")
        agent_frameworks = {
            "researcher": "CrewAI Framework",
            "analyzer": "LangGraph Framework",
            "expert": "Google ADK Framework"
        }
        
        for agent_name in st.session_state.orchestrator.agents.keys():
            framework = agent_frameworks.get(agent_name, "Framework")
            st.markdown(f"- **{agent_name.capitalize()}** ✅ Active ({framework})")
        
        # Display conversation history
        st.subheader("Conversation History")
        if st.session_state.conversation_history:
            for i, entry in enumerate(reversed(st.session_state.conversation_history[-5:])):
                with st.expander(f"Task {len(st.session_state.conversation_history)-i}", expanded=False):
                    st.markdown("**Task:**")
                    st.markdown(format_task_output(entry["task"]))
                    
                    st.markdown("**Result:**")
                    if isinstance(entry["result"], dict) and "result" in entry["result"]:
                        result_data = entry["result"]["result"]
                        st.markdown(format_agent_output(result_data))
                    else:
                        st.markdown(format_agent_output(entry["result"]))
                    
                    # Display APIs used if available
                    if isinstance(entry["result"], dict) and "result" in entry["result"]:
                        result_data = entry["result"]["result"]
                        if isinstance(result_data, dict) and "apis_used" in result_data:
                            apis_used = result_data["apis_used"]
                            if apis_used:
                                st.markdown("**APIs Used:**")
                                st.markdown(", ".join(apis_used))
                    
                    # Display token usage if available
                    if isinstance(entry["result"], dict) and "result" in entry["result"]:
                        result_data = entry["result"]["result"]
                        if isinstance(result_data, dict) and "token_usage" in result_data:
                            token_usage = result_data["token_usage"]
                            if token_usage:
                                st.markdown("**Token Usage:**")
                                st.json(token_usage)

        else:
            st.info("No tasks executed yet.")
    
    # Run coordinated tasks section
    st.divider()
    st.header("Run Coordinated Tasks")
    st.markdown("Execute a sequence of tasks coordinated by the A2A protocol:")
    
    if st.button("Run Sample Coordinated Tasks"):
        with st.spinner("Running coordinated tasks..."):
            # Define sample tasks
            tasks = [
                {
                    "type": "research",
                    "content": "Research the benefits of multi-agent systems in AI"
                },
                {
                    "type": "analysis",
                    "content": "Analyze key advantages of using specialized agents",
                    "data": ["Specialization", "Scalability", "Fault Tolerance", "Efficiency"]
                },
                {
                    "type": "expert_query",
                    "content": "Based on the research and analysis, provide recommendations for implementing a multi-agent system",
                    "context": "We're building a system with CrewAI, LangGraph, and Google ADK agents."
                }
            ]
            
            # Execute coordinated tasks
            results = st.session_state.orchestrator.coordinate_agents(tasks)
            
            # Display results
            st.subheader("Coordinated Task Results")
            for i, result in enumerate(results):
                st.markdown(f"**Task {i+1} ({result['agent'].capitalize()}):**")
                
                if isinstance(result["result"], dict) and "content" in result["result"]:
                    st.markdown(format_agent_output(result["result"]))
                else:
                    st.markdown(format_agent_output(result["result"]))
                
                # Display APIs used if available
                if isinstance(result["result"], dict) and "apis_used" in result["result"]:
                    apis_used = result["result"]["apis_used"]
                    if apis_used:
                        st.markdown("**APIs Used:**")
                        st.markdown(", ".join(apis_used))
                
                # Display token usage if available
                if isinstance(result["result"], dict) and "token_usage" in result["result"]:
                    token_usage = result["result"]["token_usage"]
                    if token_usage:
                        st.markdown("**Token Usage:**")
                        tokens_used = token_usage.get("total_tokens", 0)
                        st.markdown(f"Total Tokens: {tokens_used}")
                
                st.divider()
            
            # Add to conversation history
            for i, (task, result) in enumerate(zip(tasks, results)):
                st.session_state.conversation_history.append({
                    "task": task,
                    "result": result
                })
            
            st.success("Coordinated tasks completed!")

if __name__ == "__main__":
    main()