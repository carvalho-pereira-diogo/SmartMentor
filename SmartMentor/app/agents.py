from textwrap import dedent
from crewai import Agent
# Assuming there are specific toolsets for each agent's needs
from .tools import CourseToolset, PDFToolset, QuizToolset, TutorToolset, UserProfileToolset

class LearningAgents():
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key
    
    def course_agent(self):
        agent = Agent(
            openai_api_key=self.openai_api_key, 
            role="Course Agent",
            goal=dedent("""\
                Manage and deliver comprehensive course content tailored to the user's learning path.
            """),
            tools=CourseToolset.tools() + PDFToolset.tools(),
            backstory=dedent("""\
                The Course Agent is designed to curate and manage educational content, ensuring users have access to up-to-date and relevant learning materials.
            """),
            
            verbose=True
        )

        def process_pdfs_for_course(pdf_paths: list):
            course_materials = []
            for pdf_path in pdf_paths:
                text_content = PDFToolset.extract_text(pdf_path)
                course_material = CourseToolset.create_course_material(topic=text_content, level="Extracted Level")
                course_materials.append(course_material)
            return course_materials

        # Attach the method to the agent instance
        agent.process_pdfs_for_course = process_pdfs_for_course

        return agent

    def quiz_agent(self):
        agent = Agent(
            role="Quiz Agent",
            goal=dedent("""\
                Design, administer, and grade quizzes to assess and reinforce user learning effectively.
            """),
            tools=QuizToolset.tools() + PDFToolset.tools(),
            backstory=dedent("""\
                The Quiz Agent creates engaging and informative quizzes that test the user's knowledge and help solidify their understanding of course content.
            """),
            verbose=True
        )

        def process_pdfs_for_quiz(pdf_paths: list):
            quizzes = []
            for pdf_path in pdf_paths:
                text_content = PDFToolset.extract_text(pdf_path)
                quiz = QuizToolset.generate_quiz(topic=text_content, difficulty="Extracted Difficulty")
                quizzes.append(quiz)
            return quizzes

        # Attach the method to the agent instance
        agent.process_pdfs_for_quiz = process_pdfs_for_quiz

        return agent

    def tutor_agent(self):
        agent = Agent(
            role="Tutor (Chatbot) Agent",
            goal=dedent("""\
                Provide real-time tutoring and assistance, answering queries and offering guidance through the learning material.
            """),
            tools=TutorToolset.tools() + PDFToolset.tools(),
            backstory=dedent("""\
                The Tutor Agent leverages advanced NLP techniques to understand and respond to user queries, offering a personalized tutoring experience.
            """),
            verbose=True
        )

        def process_pdfs_for_tutoring(pdf_paths: list):
            resources = []
            for pdf_path in pdf_paths:
                text_content = PDFToolset.extract_text(pdf_path)
                # Assuming a method exists to create tutoring content from text
                resource = TutorToolset.create_tutoring_resource(content=text_content)
                resources.append(resource)
            return resources

        # Attach the method to the agent instance
        agent.process_pdfs_for_tutoring = process_pdfs_for_tutoring

        return agent

    def user_profile_agent(self):
        return Agent(
            role="User Profile Agent",
            goal=dedent("""\
                Analyze user interactions and performance across the platform to create and refine personalized learning paths.
            """),
            tools=UserProfileToolset.tools(),
            backstory=dedent("""\
                The User Profile Agent synthesizes data from various interactions to tailor the learning experience directly to the user's needs and preferences.
            """),
            verbose=True
        )
        