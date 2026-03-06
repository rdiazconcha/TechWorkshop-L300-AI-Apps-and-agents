# Azure imports
from azure.identity import DefaultAzureCredential
from azure.ai.evaluation.red_team import RedTeam, RiskCategory, AttackStrategy
from pyrit.prompt_target import OpenAIChatTarget
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

# Azure AI Project Information
azure_ai_project = os.getenv("FOUNDRY_ENDPOINT")

# Instantiate your AI Red Teaming Agent
red_team_agent = RedTeam(
    azure_ai_project=azure_ai_project,
    credential=DefaultAzureCredential(),
    risk_categories=[
        RiskCategory.Violence,
        RiskCategory.HateUnfairness,
        RiskCategory.Sexual,
        RiskCategory.SelfHarm
    ],
    num_objectives=5,
)

# Configuration for Azure OpenAI model
azure_openai_config = { 
    "azure_endpoint": f"{os.environ.get('gpt_endpoint')}/openai/deployments/{os.environ.get('gpt_deployment')}/chat/completions",
    "api_key": os.environ.get("FOUNDRY_KEY"),
    "azure_deployment": os.environ.get("gpt_deployment")
}



async def main():
    red_team_result = await red_team_agent.scan(target=azure_openai_config)


asyncio.run(main())
