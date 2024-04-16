from textwrap import dedent
from crewai import Agent
# Assuming there are specific toolsets for each agent's needs
from .tools import CourseToolset, PDFToolset, QuizToolset, TutorToolset, UserProfileToolset
import markdown

class LearningAgents():
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key
    
    def course_agent(self):
        course_tools = [tool for tool in CourseToolset.tools()]
        pdf_tools = [tool for tool in PDFToolset.tools()]
        tools = course_tools + pdf_tools  # This now creates a single list of tools
        print("Tools before Agent creation:", tools)
        agent = Agent(
            openai_api_key=self.openai_api_key, 
            role="Course Agent",
            goal=dedent("""\
                Manage and deliver comprehensive course content tailored to the user's learning path.
            """),
            tools=tools,  # Pass the flattened list
            backstory=dedent("""\
                The Course Agent is designed to curate and manage educational content, ensuring users have access to up-to-date and relevant learning materials.
            """),
            verbose=True
        )

        def create_and_process_course(teacher, name, description, pdf_paths):
                    course = CourseToolset.create_course(teacher, name, description, pdf_paths)
                    course_materials = agent.process_pdfs_for_course(pdf_paths)
                    return course, course_materials

        def enroll_and_adapt_course(student, course):
            CourseToolset.enroll_student(student, course)
            CourseToolset.adapt_course_level(student, course)
            return course

        # Attach the methods to the agent instance
        agent.create_and_process_course = create_and_process_course
        agent.enroll_and_adapt_course = enroll_and_adapt_course

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

    def tutor_agent(self, tutor):
        tools = TutorToolset.tools() + PDFToolset.tools()
        print("Debug - Tools List:", tools)  # This will show what's being passed as tools
        if not all(callable(tool) for tool in tools):
            raise ValueError("All tools must be callable")
        
        agent = Agent(
            role="Tutor (Chatbot) Agent",
            goal=f"Provide tutoring based on the materials and expertise of {tutor.name}.",
            tools=tools,
            backstory=f"The Tutor Agent uses resources from {tutor.name} to tailor the tutoring experience.",
            verbose=True
        )
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
        