"""
Keyword Orchestrator - Agent Framework Version
An intelligent routing system for specialized AI agents using keyword-based matching

ORCHESTRATION STRATEGY:
- Simple keyword matching against predefined agent domain keywords
- Scores each agent based on number of keyword matches in user input
- Routes to agent with highest score (if any matches found)
- Fast and predictable routing decisions
- Pattern detection for numeric expressions (math agent)

PROS:
- Very fast routing (no LLM calls required)
- Predictable and deterministic behavior
- Easy to debug and understand
- Low computational overhead
- No additional API costs

CONS:
- Limited context understanding
- May miss nuanced intent
- Relies on exact keyword presence
- Cannot handle complex multi-domain queries well

BEST FOR:
- Simple, clear-cut routing needs
- High-volume environments where speed matters
- Predictable user query patterns
- Cost-conscious deployments

EXAMPLE ROUTING:
- "show github repositories" → GitHub Agent (matches: github, repositories)
- "calculate 5 + 3" → Math Agent (matches: calculate, numeric pattern)
- "what is 25 * 4" → Math Agent (matches: numeric pattern)
"""

import re
from typing import Optional, Dict

from agents.github_agent import create_github_agent
from agents.math_agent import create_math_agent



class KeywordOrchestrator:
    """Orchestrator that manages multiple specialized agents with keyword-based routing"""
    
    def __init__(self):
        """Initialize the keyword-based orchestrator"""
        self.agents: Dict[str, any] = {}
        self.threads: Dict[str, any] = {}
        self.current_agent_name: Optional[str] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize all specialized agents"""
        if self._initialized:
            return
            
        # Initialize GitHub Agent
        self.agents['github'] = await create_github_agent()
        self.threads['github'] = self.agents['github'].get_new_thread()
        
        # Initialize Math Agent
        self.agents['math'] = await create_math_agent()
        self.threads['math'] = self.agents['math'].get_new_thread()
        
        self._initialized = True
        print(f"Initialized {len(self.agents)} specialized agent(s)")
    
    def get_agent_keywords(self) -> Dict[str, list]:
        """Return keyword mappings for agent routing"""
        return {
            'github': ['github', 'repository', 'repo', 'code', 'file', 'branch', 'commit', 'pull', 'issue', 'fork'],
            'math': ['calculate', 'math', 'add', 'subtract', 'multiply', 'divide', 'equation', 'expression', 'number', 'compute']
        }
        
    def get_agent_by_keywords(self, user_input: str) -> Optional[str]:
        """
        Determine which agent should handle the query based on keywords
        
        Args:
            user_input: The user's query
            
        Returns:
            Agent name or None
        """
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
        
        # Boost math agent for "what is" followed by numbers
        if re.search(r'what\s+is\s+\d+', user_lower):
            scores['math'] = scores.get('math', 0) + 3
        
        # Return agent with highest score (if any matches)
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores, key=scores.get)
        
        return None
    
    async def route_query(self, user_input: str, stream: bool = False):
        """
        Route the user query to the appropriate agent
        
        Args:
            user_input: The user's message
            stream: Whether to return a streaming response (async generator)
            
        Returns:
            If stream=False: Tuple of (response_text, agent_switch_info)
            If stream=True: Async generator yielding chunks and final (None, agent_switch_info)
        """
        # Ensure initialization
        if not self._initialized:
            await self.initialize()
        
        # Try to determine the best agent automatically
        selected_agent_name = self.get_agent_by_keywords(user_input)
        
        if not selected_agent_name:
            # No agent matched - return help info
            help_response = self.get_agent_selection_help()
            if stream:
                async def help_generator():
                    yield help_response
                    yield (None, None)
                return help_generator()
            else:
                return help_response, None
        
        # Check if we switched agents
        agent_switch_info = None
        if self.current_agent_name != selected_agent_name:
            self.current_agent_name = selected_agent_name
            agent_switch_info = f"🤖 Routed to: {selected_agent_name.title()} Agent"
        
        # Get agent and thread
        agent = self.agents[selected_agent_name]
        thread = self.threads[selected_agent_name]
        
        if stream:
            # Return streaming generator
            async def response_generator():
                tool_calls_made = []
                async for chunk in agent.run_stream(user_input, thread=thread):
                    # Track tool calls
                    if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                        for tool_call in chunk.tool_calls:
                            tool_name = tool_call.function.name if hasattr(tool_call.function, 'name') else str(tool_call)
                            if tool_name not in tool_calls_made:
                                tool_calls_made.append(tool_name)
                                yield f"\n🔧 Calling tool: {tool_name}\n"
                    
                    if chunk.text:
                        yield chunk.text
                        
                # Final yield with switch info and tool summary
                if tool_calls_made:
                    tool_summary = f"\n\n📋 Tools used: {', '.join(tool_calls_made)}"
                    yield tool_summary
                yield (None, agent_switch_info)
            return response_generator()
        else:
            # Collect full response and track tools
            response_text = ""
            tool_calls_made = []
            async for chunk in agent.run_stream(user_input, thread=thread):
                # Track tool calls
                if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                    for tool_call in chunk.tool_calls:
                        tool_name = tool_call.function.name if hasattr(tool_call.function, 'name') else str(tool_call)
                        if tool_name not in tool_calls_made:
                            tool_calls_made.append(tool_name)
                            print(f"\n🔧 Calling tool: {tool_name}", flush=True)
                
                if chunk.text:
                    response_text += chunk.text
            
            # Add tool summary to response
            if tool_calls_made:
                response_text += f"\n\n📋 Tools used: {', '.join(tool_calls_made)}"
                
            return response_text, agent_switch_info
    
    def get_agent_selection_help(self) -> str:
        """Provide help for selecting an agent"""
        keywords = self.get_agent_keywords()
        help_text = "I'm not sure which specialist can help you best. Here are your options:\n\n"
        
        for agent_name, agent_keywords in keywords.items():
            help_text += f"**{agent_name.title()} Agent**\n"
            help_text += f"Keywords: {', '.join(agent_keywords[:5])}\n"
            if agent_name == 'math':
                help_text += "Also detects: numeric expressions (e.g., 5 + 3, 12 * 4)\n"
            help_text += "\n"
        
        help_text += "Try using specific keywords in your question to help me route you correctly."
        
        return help_text
    
    def switch_agent(self, agent_identifier: str) -> tuple[bool, str]:
        """
        Manually switch to a specific agent
        
        Args:
            agent_identifier: Agent name or alias
            
        Returns:
            Tuple of (success, message)
        """
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
        agent_list = "Available Specialized Agents:\n\n"
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