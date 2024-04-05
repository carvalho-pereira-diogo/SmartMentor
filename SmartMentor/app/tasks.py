from textwrap import dedent
from crewai import Task

class LearningTasks():
    def create_course_content_task(self, agent, course_topic, user_level):
        return Task(
            name="Create Course Content",
            description=dedent(
                f"""
                Develop comprehensive course content on the following topic:
                - Topic: {course_topic}
                - User Level: {user_level}
                The content should be engaging, informative, and tailored to the specified user level.
                """
            ),
            agent=agent,
            expected_output=dedent(
                """
                A complete set of course materials, including lectures, readings, and multimedia resources, tailored to the user's level and interests.
                """
            ),
            async_execution=True
        )

    def generate_quiz_task(self, agent, course_topic, difficulty_level):
        return Task(
            name="Generate Quiz",
            description=dedent(
                f"""
                Create a quiz related to the following course topic:
                - Topic: {course_topic}
                - Difficulty Level: {difficulty_level}
                The quiz should effectively assess the user's understanding of the topic and adapt to the specified difficulty level.
                """
            ),
            agent=agent,
            expected_output=dedent(
                """
                A set of quiz questions with varying formats (multiple choice, true/false, short answer) that accurately measures understanding and provides feedback.
                """
            ),
            async_execution=True
        )

    def tutor_assistance_task(self, agent, user_query, subject_area):
        return Task(
            name="Tutor Assistance",
            description=dedent(
                f"""
                Provide real-time assistance for the following user query:
                - Query: {user_query}
                - Subject Area: {subject_area}
                Utilize the knowledge base to offer clear, concise, and helpful guidance.
                """
            ),
            agent=agent,
            expected_output=dedent(
                """
                A detailed response to the user's query, offering explanations, examples, and further reading resources where appropriate.
                """
            ),
            async_execution=True
        )

    def create_learning_path_task(self, agent, user_profile, learning_goals):
        return Task(
            name="Create Learning Path",
            description=dedent(
                f"""
                Analyze the user's profile and learning goals to develop a personalized learning path:
                - User Profile: {user_profile}
                - Learning Goals: {learning_goals}
                The learning path should incorporate recommended courses, quizzes, and tutoring sessions that align with the user's objectives.
                """
            ),
            agent=agent,
            expected_output=dedent(
                """
                A customized learning path that outlines a sequence of courses, quizzes, and key topics for tutoring, tailored to the user's goals and progress.
                """
            ),
            async_execution=True
        )
