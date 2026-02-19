"""
LLM Orchestrator - Agent Framework Version
An orchestrator using LLM intelligence for sophisticated routing decisions

ORCHESTRATION STRATEGY:
- Uses dedicated LLM instance for routing decisions
- Analyzes user intent and context, not just keywords
- Provides detailed agent descriptions to LLM for informed routing
- Low temperature (0.1) for consistent, deterministic routing
- Fallback to keyword matching if LLM routing fails
- Separate routing call to avoid interference with agent conversations

LLM ROUTING PROCESS:
1. User query analyzed by routing LLM
2. LLM considers agent capabilities and user intent
3. Returns agent name or 'none' if uncertain
4. Fallback to keyword matching on LLM failure

PROS:
- Understands user intent and context
- Handles complex and ambiguous queries
- Natural language understanding
- Can reason about multi-domain requests
- Adapts to new query patterns without rule changes
- Most intelligent routing decisions

CONS:
- Slower than other methods (requires LLM call)
- Additional API costs for routing decisions
- Potential for inconsistent routing (mitigated by low temperature)
- Depends on LLM service availability
- Harder to debug routing decisions

BEST FOR:
- Complex, ambiguous user queries
- Natural language heavy environments
- Scenarios where routing accuracy is critical
- Applications with unpredictable query patterns
- User-facing systems requiring natural interaction

EXAMPLE ROUTING:
- "Help me understand why the login is failing" → GitHub (intent: troubleshoot code)
- "I need to review the authentication logic" → GitHub (intent: code review)
- "What's 25 plus 17?" → Math (intent: calculation)
"""

import os
import re
from typing import Optional, Dict
from azure.identity.aio import DefaultAzureCredential
from agent_framework.azure import AzureAIClient
from dotenv import load_dotenv

from agents.github_agent import create_github_agent
from agents.math_agent import create_math_agent

load_dotenv(override=True)


class LLMOrchestrator:
    """Orchestrator that uses LLM intelligence to make routing decisions"""
    
    def __init__(self):
        """Initialize the LLM-based orchestrator"""
        self.agents: Dict[str, any] = {}
        self.current_agent_name: Optional[str] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize all specialized agents and routing logic"""
        if self._initialized:
            return
        
        # Get configuration from environment
        project_endpoint = os.getenv('AZURE_PROJECT_ENDPOINT')
        model_deployment_name = os.getenv('MODEL_DEPLOYMENT_NAME', 'gpt-4.1')
        
        if not project_endpoint:
            raise ValueError("AZURE_PROJECT_ENDPOINT environment variable is not set")
        
        # Create separate Azure AI client for each agent to ensure isolation
        credential = DefaultAzureCredential()
        
        # Initialize GitHub Agent with its own client
        github_client = AzureAIClient(
            project_endpoint=project_endpoint,
            model_deployment_name=model_deployment_name,
            credential=credential
        )
        self.agents['github'] = create_github_agent(github_client)
        
        # Initialize Math Agent with its own client
        math_client = AzureAIClient(
            project_endpoint=project_endpoint,
            model_deployment_name=model_deployment_name,
            credential=credential
        )
        self.agents['math'] = create_math_agent(math_client)
        
        self._initialized = True
        print(f"Initialized {len(self.agents)} specialized agent(s) with LLM routing")
    
    def get_agent_keywords(self) -> Dict[str, list]:
        """Return keyword mappings for fallback routing"""
        return {
            'github': ['github', 'repository', 'repo', 'code', 'file', 'branch', 'commit', 'pull', 'issue', 'fork'],
            'math': ['calculate', 'math', 'add', 'subtract', 'multiply', 'divide', 'equation', 'expression', 'number', 'compute']
        }
    
    def get_routing_prompt(self, user_input: str) -> str:
        """Generate a prompt for the LLM to make routing decisions"""
        return f"""You are an intelligent agent router. Analyze the user's request and determine which specialist agent should handle it.

Available Agents:
1. **github**: Code repository management, file browsing, code analysis, repository operations
   - Use for: repository queries, file content, code structure, GitHub operations, code review, browsing files
   
2. **math**: Mathematical calculations and expression evaluation
   - Use for: arithmetic, algebra, calculations, math problems, numeric operations

User Request: "{user_input}"

Instructions:
- Analyze the user's intent and context
- Consider which agent's capabilities best match the request
- If it's about code/repositories/files, respond with: github
- If it's about math/calculations/numbers, respond with: math
- If unclear or neither, respond with: none

Respond with ONLY ONE WORD: github, math, or none"""
    
    async def get_agent_by_llm(self, user_input: str) -> Optional[str]:
        """
        Use LLM intelligence to determine which agent should handle the query
        
        Args:
            user_input: The user's query
            
        Returns:
            Agent name or None
        """
        try:
            # Create a routing prompt
            routing_prompt = self.get_routing_prompt(user_input)
            
            # Use the routing agent to make decision
            routing_thread = self.routing_agent.get_new_thread()
            
            # Get routing decision from LLM
            response_text = ""
            async for chunk in self.routing_agent.run_stream(routing_prompt, thread=routing_thread):
                if chunk.text:
                    response_text += chunk.text
            
            decision = response_text.strip().lower()
            print(f"🧠 LLM routing decision: {decision}")
            
            if decision in self.agents:
                return decision
            elif decision == "none":
                return None
            else:
                print(f"⚠️ Unexpected LLM response: {decision}, falling back to keyword matching")
                return self._fallback_keyword_routing(user_input)
            
        except Exception as e:
            print(f"⚠️ LLM routing failed: {e}, falling back to keyword matching")
            return self._fallback_keyword_routing(user_input)
    
    def _fallback_keyword_routing(self, user_input: str) -> Optional[str]:
        """Fallback to keyword matching if LLM routing fails"""
        user_lower = user_input.lower()
        keywords = self.get_agent_keywords()
        
        # Score each agent based on keyword matches
        scores = {}
        for agent_name, agent_keywords in keywords.items():
            score = sum(1 for keyword in agent_keywords if keyword in user_lower)
            scores[agent_name] = score
        
        # Boost math agent score if input contains numbers with operators
        math_pattern = r'\d+\s*[\+\-\*\/\^%]\s*\d+'
        if re.search(math_pattern, user_input):
            scores['math'] = scores.get('math', 0) + 5
        
        # Return agent with highest score (if any matches)
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            return max(scores, key=scores.get)
        
        return None
        return None
    
    async def route_query(self, user_input: str, stream: bool = False):
        """
        Route the user query using LLM intelligence
        
        Args:
            user_input: The user's message
            stream: Whether to return a streaming response (not currently supported)
            
        Returns:
            Tuple of (response_text, agent_switch_info)
        """
        # Ensure initialization
        if not self._initialized:
            await self.initialize()
        
        # Use LLM to determine the best agent
        selected_agent_name = await self.get_agent_by_llm(user_input)
        
        if not selected_agent_name:
            # LLM couldn't determine agent - return help info
            help_response = self.get_agent_selection_help()
            return help_response, None
        
        # Check if we switched agents
        agent_switch_info = None
        if self.current_agent_name != selected_agent_name:
            self.current_agent_name = selected_agent_name
            agent_switch_info = f"🤖 LLM routed to: {selected_agent_name.title()} Agent"
        
        # Get agent
        agent = self.agents[selected_agent_name]
        
        # Get response from agent
        response = await agent.run(user_input)
        
        # Convert AgentRunResponse to string
        response_text = str(response) if hasattr(response, '__str__') else response
        
        return response_text, agent_switch_info
    
    def get_agent_selection_help(self) -> str:
        """Provide help for selecting an agent"""
        keywords = self.get_agent_keywords()
        help_text = "I couldn't determine which specialist can help you best. Here are your options:\n\n"
        
        for agent_name, agent_keywords in keywords.items():
            help_text += f"**{agent_name.title()} Agent**\n"
            help_text += f"Keywords: {', '.join(agent_keywords[:5])}\n\n"
        
        help_text += "Example queries:\n"
        help_text += "- 'Show me the latest commits in my repository' → GitHub\n"
        help_text += "- 'Calculate 25 * 4 + 10' → Math\n\n"
        help_text += "Try being more specific about what you want to accomplish."
        
        return help_text
    
    def switch_agent(self, agent_identifier: str) -> tuple[bool, str]:
        """Manually switch to a specific agent"""
        agent_map = {
            'github': 'github', 'git': 'github', 'code': 'github',
            'math': 'math', 'calc': 'math', 'calculator': 'math'
        }
        
        agent_key = agent_map.get(agent_identifier.lower())
        if agent_key and agent_key in self.agents:
            self.current_agent_name = agent_key
            return True, f"✅ Switched to {agent_key.title()} Agent"
        else:
            available = ', '.join(agent_map.keys())
            return False, f"❌ Unknown agent: {agent_identifier}. Available: {available}"
    
    def list_agents(self) -> str:
        """List all available agents with their status"""
        agent_list = "Available Specialized Agents (LLM-Powered Routing):\n\n"
        for i, agent_name in enumerate(self.agents.keys(), 1):
            status = "🟢 ACTIVE" if self.current_agent_name == agent_name else "⚪ Available"
            agent_list += f"{i}. **{agent_name.title()} Agent** {status}\n"
        return agent_list
    
    def clear_all_history(self):
        """Clear all agent conversation histories"""
        for agent_name in self.agents:
            self.threads[agent_name] = self.agents[agent_name].get_new_thread()
        self.current_agent_name = None
    
    def get_current_agent_name(self) -> Optional[str]:
        """Get the name of the currently active agent"""
        return self.current_agent_name