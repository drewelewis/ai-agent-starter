"""
GitHub Agent - Microsoft Agent Framework Version
A specialized AI agent for GitHub repository management and code analysis
"""

import os
import asyncio
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from agent_framework.azure import AzureAIClient
from agent_framework import ChatAgent

# Import GitHub tools
from tools.github_tool import (
    get_repos_by_user,
    get_files_by_repo,
    get_file_content,
    create_github_issue
)

# Load environment variables
load_dotenv(override=True)


async def create_github_agent() -> ChatAgent:
    """
    Create and configure the GitHub Agent with tools.
    
    Returns:
        Configured ChatAgent instance
    """
    # Get configuration from environment
    project_endpoint = os.getenv('AZURE_PROJECT_ENDPOINT')
    model_deployment_name = os.getenv('MODEL_DEPLOYMENT_NAME', 'gpt-4.1')
    
    if not project_endpoint:
        raise ValueError("AZURE_PROJECT_ENDPOINT environment variable is not set")
    
    # Create credential
    credential = DefaultAzureCredential()
    
    # Create Azure AI client
    client = AzureAIClient(
        project_endpoint=project_endpoint,
        model_deployment_name=model_deployment_name,
        credential=credential
    )
    
    # Define agent instructions
    instructions = """You are a specialized GitHub Assistant Agent. You are an expert in:
- Repository management and navigation
- Code analysis and review
- File browsing and content retrieval
- GitHub best practices and workflows

**Your Capabilities:**
- List repositories for any GitHub user
- Browse repository structure and files
- Retrieve and analyze file contents
- Create GitHub issues
- Provide insights about code organization

**Default Configuration:**
- Default GitHub user: drewelewis
- Default repository: drewelewis/ContosoBankAPI
- Always verify with users if they want to use different repositories

**Your Expertise:**
- Code structure analysis
- Repository organization patterns
- File dependency mapping
- Code quality assessment
- Development workflow guidance

**Instructions:**
- Focus exclusively on GitHub-related tasks and questions
- Provide detailed insights about repository structure and code
- Help users understand codebases and find specific files or functions
- Offer suggestions for code organization and best practices
- Be thorough in your analysis and explanations
- If asked about non-GitHub topics, politely redirect to your GitHub expertise

Always think step by step when analyzing repositories and provide clear, actionable insights."""
    
    # Create agent with tools
    agent = client.create_agent(
        name="GitHubAgent",
        instructions=instructions,
        tools=[
            get_repos_by_user,
            get_files_by_repo,
            get_file_content,
            create_github_issue
        ]
    )
    
    return agent


async def main():
    """
    Main entry point for running the GitHub Agent in interactive mode.
    For HTTP server mode, use server.py instead.
    """
    print("\n" + "="*60)
    print("GitHub Assistant Agent - Microsoft Agent Framework")
    print("="*60 + "\n")
    
    # Create the agent
    async with (
        DefaultAzureCredential() as credential,
        await create_github_agent() as agent
    ):
        print("✅ GitHub Agent initialized successfully!")
        print("💬 Type your questions (or 'quit' to exit)\n")
        
        # Create a thread for multi-turn conversation
        thread = agent.get_new_thread()
        
        # Interactive chat loop
        while True:
            try:
                user_input = input("You: ")
                print()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not user_input.strip():
                    continue
                
                # Stream the response
                print("Agent: ", end="", flush=True)
                async for chunk in agent.run_stream(user_input, thread=thread):
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                print("\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
