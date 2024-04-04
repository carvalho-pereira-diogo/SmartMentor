from textwrap import dedent
from crewai import Agent
from tools import ExaSearchToolset

# Create different agents for the AI agent
class MeetingPrepAgents():
    def research_agent(self):
        return Agent(
            role = "Research Agent",
            goal = dedent(
                """\
                Conduct thorough research in python programming language.
                """
            ),
            tools = ExaSearchToolset.tools(),
            backstory = dedent(
                """\
                The research agent is a highly skilled AI agent that has been trained to conduct research in python programming language.
                """
            ),
            verbose = True
        ),
        
        
#set everything in view.py