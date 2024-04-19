import openai
from .pdf_extractor import extract_text_from_pdf
from django.conf import settings

class CourseCreatorAgent:
    def __init__(self, openai_api_key):
        # Use the OpenAI library by setting the API key directly
        openai.api_key = openai_api_key

    def generate_course_content(self, report, pdf_files):
        # Process PDF files and summarize contents
        pdf_texts = [self.summarize_text(extract_text_from_pdf(pdf)) for pdf in pdf_files if pdf]
        combined_context = "\n\n".join([report] + [text for text in pdf_texts if text])

        # Generate course content based on the combined context
        return self._request_openai_for_course_content(combined_context)

    def summarize_text(self, text, max_tokens=300):
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"Summarize this text: {text}",
                max_tokens=max_tokens,
                temperature=0.7  # Adjust creativity of the summary
            )
            return response.choices[0].text.strip()
        except Exception as e:
            print(f"Error during summarization: {str(e)}")
            return "Unable to summarize text due to an error."

    def _request_openai_for_course_content(self, context):
        try:
            response = openai.Completion.create(
                engine="gpt-3.5-turbo",
                prompt=f"Generate a course outline based on the following information:\n\n{context}",
                max_tokens=1000,
                stop=["\n\n"]
            )
            return self._structure_course_content(response.choices[0].text.strip())
        except Exception as e:
            print(f"Error accessing OpenAI: {e}")
            return "There was an error processing your request."

    def _structure_course_content(self, content):
        topics = content.split("\n\n")
        structured_content = {"topics": []}
        for topic in topics:
            if '\n' in topic:
                title, description = topic.split('\n', 1)
                structured_content['topics'].append({'title': title, 'description': description})
        return structured_content
