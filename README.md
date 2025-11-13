# Multi-Agent System with A2A Protocol

A coordinated system of three specialized AI agents (Research, Analysis, Expert) implementing the Agent-to-Agent (A2A) protocol for seamless collaboration.

## 🏗️ Architecture Overview

This system implements the A2A protocol with three specialized agents:

1. **Research Analyst Agent** - Specialized for comprehensive research and information gathering
2. **Data Analyzer Agent** - Specialized for data analysis, pattern recognition, and statistical modeling
3. **Domain Expert Agent** - Specialized for providing expert knowledge, strategic recommendations, and business insights

## 📋 A2A Protocol Compliance

### ✅ AgentCard Publishing
- **Location**: `/.well-known/` directory
- **Files**: 
  - `agent.json` - Main system AgentCard
  - `researcher-agent.json` - Research Analyst AgentCard
  - `analyzer-agent.json` - Data Analyzer AgentCard
  - `expert-agent.json` - Domain Expert AgentCard

### ✅ Task State Management
- **States**: submitted, working, input-required, completed, canceled, failed, unknown
- **Lifecycle**: Full task state tracking with history and artifacts
- **Session Support**: Optional session association for related interactions

### ✅ Standardized Communication
- **Protocol**: Direct Python method calls (in-process communication)
- **Components**: Standardized components for agent discovery, task management, and messaging
- **Documentation**: Built-in documentation through code structure and comments

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Installation
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration
Create a `.env` file with your API keys:
```env
OPENROUTER_API_KEY=your_openrouter_api_key
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
NEWS_API_KEY=your_news_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
IP_GEOLOCATION_API_KEY=your_ip_geolocation_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
M0_API_KEY=your_mem0_api_key
```

### Running the System
```bash
# Start the Streamlit frontend (this includes the orchestrator)
streamlit run frontend/streamlit_app.py
```

## 🛠️ System Components

### Agent Discovery
AgentCards are available in the `.well-known/` directory:
- `agent.json` - Main system AgentCard
- `researcher-agent.json` - Research Analyst AgentCard
- `analyzer-agent.json` - Data Analyzer AgentCard
- `expert-agent.json` - Domain Expert AgentCard

## 🔧 Testing

The system uses direct Python method calls for communication between components rather than HTTP APIs. All agent interactions happen within the same Python process through the A2AOrchestrator.

## 📚 Documentation

### AgentCards
Each AgentCard follows the A2A specification with:
- Name and description
- URL and provider information
- Version and documentation URL
- Capabilities (streaming, push notifications, state transition history)
- Authentication requirements
- Input/output modes
- Skills with detailed descriptions

### Task Management
Tasks follow the A2A task lifecycle with:
- Formal state management (submitted, working, completed, etc.)
- Session association for related tasks
- History tracking of all task events
- Artifact storage for task outputs

## 🤝 Collaboration Workflow

The system implements a three-stage collaborative workflow:
1. **Research** - Research Analyst gathers comprehensive information
2. **Analysis** - Data Analyzer processes findings and identifies patterns
3. **Expertise** - Domain Expert provides strategic recommendations

## 📈 External API Integration

The system integrates with multiple external APIs:
- **Tavily Search** - Web research
- **NewsAPI** - Current news analysis
- **OpenWeather** - Weather data
- **IP Geolocation** - Location-based information
- **Alpha Vantage** - Stock market data
- **Wikipedia** - General knowledge base

## 💾 Memory Management

Persistent memory is implemented using Mem0:
- Long-term storage of agent interactions
- Context retention across sessions
- Learning from previous interactions

## 🎯 Features

- **Multi-Agent Collaboration** - Three specialized agents working together
- **A2A Protocol Compliance** - Full implementation of Agent-to-Agent protocol
- **External API Integration** - Access to multiple data sources
- **Memory Management** - Persistent storage with Mem0
- **Security** - API key based authentication
- **Fallback Support** - Gemini 2.0 Flash fallback for OpenRouter limits
- **Automatic API Selection** - Intelligent API usage based on task content

## 📖 License

This project is licensed under the MIT License - see the LICENSE file for details.