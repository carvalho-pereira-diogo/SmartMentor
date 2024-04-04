from textwrap import dedent
from crewai import Task

# Create different tasks for the AI agent
class MeetingPrepTasks():
    def research_task(self, agent, meeting_participants, meeting_context):
        return Task(
            name="Research",
            description=dedent(
                f"""
                Research the following topics:
                - {meeting_participants}
                - {meeting_context}
                """
            ),
            agent=agent,
            expected_output=dedent(
                f"""
                Research the following topics:
                - {meeting_participants}
                - {meeting_context}
                """
            ),
            async_execution=True
        )
        
    def another_task(self, agent, meeting_participants, meeting_context):  # Renamed method
        return Task(
            name="Another Task",  # Changed task name
            description=dedent(
                f"""
                Research the following topics:
                - {meeting_participants}
                - {meeting_context}
                """
            ),
            agent=agent,
            expected_output=dedent(
                f"""
                Research the following topics:
                - {meeting_participants}
                - {meeting_context}
                """
            ),
            async_execution=True
        )