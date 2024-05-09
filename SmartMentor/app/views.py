import logging
import os
import PyPDF2
import fitz 
import json
import openai
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.http import FileResponse, Http404, HttpResponse, HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.views.generic import ListView, DetailView
from django.views import generic
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse, reverse_lazy
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.management.base import BaseCommand
from django.views.decorators.http import require_POST
from .models import *
from .forms import *


def home(request):
    return render(request, 'app/home.html')

class UserLoginView(LoginView):
    template_name = 'app/login.html'  # Replace with your login template
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')

class LogoutOnGetView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
# profile register
def signup(request):
    if request.method == "POST":
        # Extract information from the POST request
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        role = request.POST['role']  # Either 'Student' or 'Teacher'
        level = request.POST.get('level', None)  # Only for students, with a default of None

        # Basic validations
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please try another username.")
            return redirect('signup')  # Assuming 'signup' is the name of your signup page URL

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists. Please try another email.")
            return redirect('signup')

        if len(username) > 10:
            messages.error(request, "Username must be under 10 characters.")
            return redirect('signup')

        if pass1 != pass2:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')

        if not username.isalnum():
            messages.error(request, "Username should only contain letters and numbers.")
            return redirect('signup')

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, first_name=fname, last_name=lname, email=email, password=pass1)
                profile = Profile(user=user, username=username, fname=fname, lname=lname, email=email, role=role)
                profile.save()

                if role.lower() == 'student':
                    student = Student(user=user, profile=profile, level=level)
                    student.save()
                elif role.lower() == 'teacher':
                    teacher = Teacher(user=user, profile=profile)
                    teacher.save()

                messages.success(request, "Your account has been created successfully!")
                return redirect('login')
        except IntegrityError as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('signup')
    else:
        return render(request, 'app/signup.html')

def signin(request):
    if request.method == "POST":
        username = request.POST['username']
        pass1 = request.POST['pass1']
        
        user = authenticate(request, username=username, password=pass1)
        
        if user is not None:
            login(request, user)
            # Redirect to a home/dashboard page upon successful login
            return redirect("home")  # Ensure "home" is the name of the URL pattern for your home page.
        else:
            # If authentication fails, show an error message and stay on the sign-in page.
            messages.error(request, "Invalid credentials, please try again.")
            return redirect("login")  # Ensure "signin" is the name of the URL pattern for your sign-in page.
        
    else:
        # For a GET request, just display the sign-in form.
        return render(request, 'app/login.html')
    
def signout(request):
    logout(request)
    return redirect('home')

class TeacherProfileView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = 'app/teacher_profile.html'
    
    def get_object(self):
        if hasattr(self.request.user, 'teacher'):
            return self.request.user.teacher
        else:
            return redirect('teacher_profile')
        
# Create a QuizView for student and teacher
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Quiz, Course
from .forms import SimpleQuizForm  # This form will potentially have fewer fields

class TeacherQuizView(LoginRequiredMixin, ListView):
    model = Quiz
    template_name = 'app/teacher_quiz.html'
    form_class = SimpleQuizForm  # Assume this is a simplified form
    success_url = reverse_lazy('teacher_quiz')

    def get_queryset(self):
        if hasattr(self.request.user, 'teacher'):
            return Quiz.objects.filter(teacher=self.request.user.teacher)
        else:
            return Quiz.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz_form'] = self.form_class()  # No need to pass user here if the form is simplified
        context['courses'] = Course.objects.filter(teacher=self.request.user.teacher)  # List courses for other UI elements maybe
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.teacher = request.user.teacher
            quiz.course = form.cleaned_data['course']  # Assuming 'course' is a field in your form
            quiz.save()

            # Associate the same PDFs as in the course to the quiz
            quiz.pdfs.set(quiz.course.pdfs.all())
            # add quiz to teacher's quiz list
            request.user.teacher.quiz_list.add(quiz)
            quiz.save()

            # Add the quiz to the course's quiz set
            quiz.course.quiz_set.add(quiz)  # Change to quizzes if related_name='quizzes' is used

            messages.success(request, "Quiz created successfully!")
            return redirect(self.success_url)
        else:
            return render(request, self.template_name, {'form': form, 'object_list': self.get_queryset(), 'errors': form.errors})



class TeacherPDFView(LoginRequiredMixin, ListView):
    model = PDF
    form_class = PDFUploadForm
    template_name = 'app/teacher_pdf_upload.html'

    def get_queryset(self):
        if hasattr(self.request.user, 'teacher'):
            return PDF.objects.filter(uploaded_by=self.request.user.teacher)
        else:
            return PDF.objects.none()

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            pdf = form.save(commit=False)
            if hasattr(request.user, 'teacher'):
                pdf.uploaded_by = request.user.teacher
                pdf.save()
                request.user.teacher.pdfs.add(pdf)
            return redirect('teacher_pdfs')
        else:
            pdfs = self.get_queryset()
            return render(request, self.template_name, {'form': form, 'object_list': pdfs})

@login_required
def delete_pdf(request, pdf_id):
    pdf = get_object_or_404(PDF, id=pdf_id)
    if request.user.is_authenticated and hasattr(request.user, 'teacher') and pdf.uploaded_by == request.user.teacher:
        pdf.delete()
        request.user.teacher.pdfs.remove(pdf)
    return redirect('teacher_pdfs')

import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ''
    for page in doc:
        text += page.get_text()
    doc.close()
    print("Extracted Text:", text)  # Debug output
    return text

# Adjust this example as necessary based on your actual implementation.


class TeacherCourseView(LoginRequiredMixin, ListView):
    model = Course
    form_class = CourseForm
    template_name = 'app/teacher_course.html'

    def get_queryset(self):
        if hasattr(self.request.user, 'teacher'):
            return Course.objects.filter(teacher=self.request.user.teacher)
        else:
            return Course.objects.none()

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            if hasattr(request.user, 'teacher'):
                course.teacher = request.user.teacher
                course.save()
                request.user.teacher.courses_list.add(course)

                # Get the selected PDFs from the form
                selected_pdfs = request.POST.getlist('pdfs')

                # Add each selected PDF to the course
                for pdf_id in selected_pdfs:
                    pdf = get_object_or_404(PDF, id=pdf_id)
                    course.pdfs.add(pdf)

                # Create a quiz for the course
                quiz = Quiz(course=course, name="Quiz for " + course.name, teacher=request.user.teacher)
                quiz.save()

                # Add the quiz to the teacher's quizzes list
                request.user.teacher.quizzes.add(quiz)

            return redirect('teacher_courses')
        else:
            courses = self.get_queryset()
            return render(request, self.template_name, {'form': form, 'object_list': courses})

@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user.is_authenticated:
        if hasattr(request.user, 'teacher'):
            if course.teacher == request.user.teacher:
                Quiz.objects.filter(course=course).delete()
                course.delete()
                print(f"Course {course_id} deleted.")
                # delete quizzes associated with the course
                
            else:
                print(f"The course's teacher is not the same as the user's teacher. Course teacher: {course.teacher}, User's teacher: {request.user.teacher}")
        else:
            print("The user does not have a teacher attribute.")
    else:
        print("The user is not authenticated.")
    return redirect('teacher_courses')
    
@login_required
def course_list(request):
    if hasattr(request.user, 'teacher'):
        teacher_courses = Course.objects.filter(teacher=request.user.teacher)
        other_courses = Course.objects.exclude(teacher=request.user.teacher)
    else:
        teacher_courses = Course.objects.none()
        other_courses = Course.objects.all()
    return render(request, 'stu_course.html', {'teacher_courses': teacher_courses, 'other_courses': other_courses})

@login_required
def teacher_courses(request):
    if hasattr(request.user, 'teacher'):
        courses = Course.objects.filter(teacher=request.user.teacher)
    else:
        courses = Course.objects.none()
    return render(request, 'te_courses.html', {'courses': courses})

class StudentProfileView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = 'app/student_profile.html'
    
    #Get the courses of the teacher
    def get_object(self):
        if hasattr(self.request.user, 'student'):
            return self.request.user.student
        else:
            return redirect('student_profile')
        
        
# Change the JSONresponse to a redirection to somewhere in the webapp
        

@login_required
def quiz(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    student = request.user.profile.student  # Adjust this based on how your Student model is linked to User

    if course in student.courses.all():
        student.courses.remove(course)
        messages.success(request, "You have successfully unenrolled from the course.")
    else:
        messages.error(request, "You are not enrolled in this course.")

    return redirect('student_courses')  # Redirect to the page where courses are listed or another appropriate page.

@login_required
def unenroll_quiz(request, quiz_id):  # Add the quiz_id parameter here
    # Assuming Student model has a 'quizzes' many-to-many field with Quiz
    student_profile = request.user.profile.student
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if quiz in student_profile.quizzes.all():
        student_profile.quizzes.remove(quiz)

    return redirect('student_quiz')  # Redirect to an appropriate view after unenrollment

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Quiz, Student

@login_required
def unenroll_course(request, course_id):  # Change 'quiz_id' to 'course_id'
    student_profile = request.user.profile.student
    course = get_object_or_404(Course, id=course_id)  # Change 'Quiz' to 'Course'

    if course in student_profile.courses.all():
        student_profile.courses.remove(course)
        
        quiz = get_object_or_404(Quiz, course=course)
        if quiz in student_profile.quizzes.all():
            student_profile.quizzes.remove(quiz)

    return redirect('student_courses')  # Redirect to an appropriate view after unenrollment Redirect to an appropriate view after unenrollment


@login_required
@require_POST
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    student = get_object_or_404(Student, profile__user=request.user)
    score = int(request.POST.get('score'))  # Convert the score to an integer

    # Save the quiz score
    quiz_score = QuizScore(student=student, quiz=quiz, score=score)
    quiz_score.save()

    # Update the LearningPath based on the score
    learning_path = get_object_or_404(LearningPath, student=student, course=quiz.course)
    if 0 <= score <= 74:
        learning_path.level = 'Beginner'
    elif 75 <= score <= 89:
        learning_path.level = 'Intermediate'
    elif 90 <= score <= 100:
        learning_path.level = 'Advanced'
    learning_path.save()

    return render(request, 'app/quiz_result.html', {'learning_path': learning_path})

        
class StudentQuizView(LoginRequiredMixin, ListView):
    model = Quiz
    template_name = 'app/student_quiz.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
            student_profile = self.request.user.profile.student
            enrolled_quizzes = student_profile.quizzes.all()
            all_quizzes = Quiz.objects.exclude(id__in=enrolled_quizzes.values_list('id', flat=True))
        else:
            all_quizzes = Quiz.objects.none()  # Show no quizzes if user is not authenticated or has no profile
        context['all_quizzes'] = all_quizzes
        context['enrolled_quizzes'] = enrolled_quizzes
        context['form'] = QuizEnrollmentForm(user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        selected_quiz_id = request.POST.get('quiz')
        print(f"Selected quiz ID: {selected_quiz_id}")  # Debug print
        if selected_quiz_id:
            quiz = get_object_or_404(Quiz, id=selected_quiz_id)
            print(f"Quiz: {quiz}")  # Debug print
            student_profile = request.user.profile.student
            if quiz not in student_profile.quizzes.all():
                student_profile.quizzes.add(quiz)  # Add the quiz to the student's list of enrolled quizzes
                print(f"Enrolled quizzes after enrollment: {student_profile.quizzes.all()}")  # Debug print
                return HttpResponseRedirect('.')  # Redirect to the current URL
            else:
                return HttpResponseRedirect('/already_enrolled')  # Handle already enrolled scenario
        return HttpResponseRedirect('/error') 
    
class StudentCourseView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'app/student_course.html'

    def post(self, request, *args, **kwargs):
        selected_course_id = request.POST.get('course')
        if selected_course_id:
            course = get_object_or_404(Course, id=selected_course_id)
            student_profile = request.user.profile.student  # This assumes that each Profile has an associated Student.
            if course not in student_profile.courses.all():
                student_profile.courses.add(course)  # Add the course to the student's list of enrolled courses
                return redirect('student_courses')  # Redirect to a page showing enrolled courses
            else:
                return HttpResponseRedirect('/already_enrolled')  # Handle already enrolled scenario
        return HttpResponseRedirect('/error') 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
            student_profile = self.request.user.profile.student
            enrolled_courses = student_profile.courses.all()
            all_courses = Course.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))
        else:
            all_courses = Course.objects.none()  # Show no courses if user is not authenticated or has no profile
        context['all_courses'] = all_courses
        context['enrolled_courses'] = enrolled_courses
        return context

from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

@method_decorator(login_required, name='dispatch')
class ErrorView(TemplateView):
    template_name = 'app/error.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "An unexpected error has occurred. Please try again."
        return context

from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

@method_decorator(login_required, name='dispatch')
class AlreadyEnrolledView(TemplateView):
    template_name = 'app/already_enrolled.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "You are already enrolled."
        return context
    
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from .models import Course, Student

class EnrollCourseView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        course_id = request.POST.get('course_id')  # Change 'course' to 'course_id'
        if course_id:
            course = get_object_or_404(Course, id=course_id)
            student_profile = request.user.profile.student
            if course not in student_profile.courses.all():
                student_profile.courses.add(course)
                quiz = get_object_or_404(Quiz, course=course)
                student_profile.quizzes.add(quiz)
                return redirect('student_courses')
            else:
                return HttpResponseRedirect('/student/already_enrolled')
        return HttpResponseRedirect('/error')


from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

class EnrollQuizView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs): # Check authentication
        quiz_id = request.POST.get('quiz_id')
        
        if not quiz_id:
            return HttpResponseRedirect('/error')  # Log and redirect to error

        quiz = get_object_or_404(Quiz, id=quiz_id)
        student_profile = request.user.profile.student
        if quiz in student_profile.quizzes.all():
            return HttpResponseRedirect('/student/already_enrolled')

        student_profile.quizzes.add(quiz)
        return redirect('student_quiz')
    
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin

    
# Learning Path View
class StudentLearningPathView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'app/student_learningpath.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
            student_profile = self.request.user.profile.student
            enrolled_courses = student_profile.courses.all()
            all_courses = Course.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))
        else:
            all_courses = Course.objects.none()  # Show no courses if user is not authenticated or has no profile
        context['all_courses'] = all_courses
        context['enrolled_courses'] = enrolled_courses
        return context
    
class StudentExamView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'app/student_exam.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
            student_profile = self.request.user.profile.student
            enrolled_courses = student_profile.courses.all()
            all_courses = Course.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))
        else:
            all_courses = Course.objects.none()  # Show no courses if user is not authenticated or has no profile
        context['all_courses'] = all_courses
        context['enrolled_courses'] = enrolled_courses
        return context

    

def stu_dashboard(request):
    return render(request, 'app/stu_dashboard.html')

def te_dashboard(request):
    return render(request, 'app/te_dashboard.html')

#Exam section
from django.shortcuts import render
from .models import Course  # Assuming you have a Course model

def generate_quiz_from_url(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    # Extract text from pdf under courses.pdfs
    pdf_path = course.pdfs.first().file.path
    text = extract_text_from_pdf(pdf_path)
    questions = generate_questions_and_choices(text)
    
    if request.method == 'POST':
        return grade_quiz(request, questions)
    
    return render(request, "chat_with_exam.html", {"questions": questions})

def grade_quiz(request, questions):
    score = 0
    total = len(questions)

    for question in questions:
        user_answer = request.POST.get(str(question['id']))
        if user_answer == question['correct_answer']:
            score += 1

    percentage = score / total * 100
    update_student_role(request.user, percentage)  # Assuming the user is a student

    return render(request, "quiz_results.html", {"score": score, "total": total, "percentage": percentage})

def update_student_role(student, percentage):
    if percentage <= 75:
        role = 'beginner'
    elif 76 <= percentage <= 90:
        role = 'intermediate'
    else:
        role = 'advanced'

    student.profile.role = role  # Assuming the student has a profile attribute with a role
    student.profile.save()
    
# Generate questions and choices
import random

def generate_questions_and_choices(text):
    # Split the text into lines
    lines = text.split('\n')

    # Initialize empty list to store questions
    questions = []

    # Iterate over the lines and extract questions and choices
    current_question = None
    for line in lines:
        line = line.strip()
        if line.endswith('?'):
            # This is a question
            current_question = {
                'question': line,
                'choices': []
            }
            questions.append(current_question)
        elif current_question is not None and line:
            # This is a choice
            current_question['choices'].append(line)

    # Shuffle the choices for each question
    for question in questions:
        random.shuffle(question['choices'])

    return questions



###---------------------------------###

# Crete me a function to get the different information of a student 
#From this function
    
from django.http import JsonResponse

def get_student_info(request):
    try:
        student = Student.objects.get(user=request.user)
        # Assuming 'profile' is a related name for a OneToOneField from User to a Profile model
        return {
            'username': student.user.username,  # Adjusted from student.profile.username
            'fname': student.user.first_name,   # Adjusted for typical Django User model
            'lname': student.user.last_name,    # Adjusted for typical Django User model
            'email': student.user.email,
            'role': student.profile.role,       # Assuming this is correct
            'level': student.level
        }
    except Student.DoesNotExist:
        return None
    

import json
from django.http import JsonResponse
from django.shortcuts import render
from PyPDF2 import PdfReader

from openai import OpenAI
"""

clientTutor = OpenAI(api_key=settings.OPENAI_API_KEY_TUTOR)

def get_pdf_text_tutor(tutor_id):
    try:
        tutor = Tutor.objects.get(pk=tutor_id)
        pdf_files = tutor.pdfs.all()  # Assuming pdfs is a related name for file fields
        text_content = ""
        for pdf_file in pdf_files:
            reader = PdfReader(pdf_file.file.path)
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        return text_content
    except Exception as e:
        print(f"Error reading PDFs: {str(e)}")
        return ""
    
    
#Create a list for memory and always delete the oldest one after 3 messages got added
memoryTutor = {}

def add_message_to_memory_tutor(message, user_id):
    if user_id not in memoryTutor:
        memoryTutor[user_id] = []
    memoryTutor[user_id].append(message)
    if len(memoryTutor[user_id]) > 3:
        memoryTutor[user_id].pop(0)




def ask_openai_for_tutor(request, message, pdf_text, tutor_id):
    try:
        tutor = Tutor.objects.get(pk=tutor_id)
        #print(f"PDFs for tutor {tutor.name}: {pdf_text}")
        report = get_student_info(request)
        print(f"Type of report: {type(report)}, Value of report: {report}")
        
        # Combine PDF text with other context information
        combined_content = f"Tutor Name: {tutor.name}. Short Description: {tutor.description}. PDF Text from tutor: {pdf_text}. Student Information: {json.dumps(report)}. Now as an assistant for students, your first task is to help the student within the context of the tutor's PDFs. Ask for introductory questions to determine their familiarity with the subject. Based on the responses and the level, provide appropriate guidance. If you can, suggest for online resources. Also guide them into how to do certain tasks. In case, the student writes code or the instructions, you correct it and provide feedback. Also, if you want you can engage them in interactive exercises. Finally, do not provide information that is not about the topic in the PDFS, this means you should not provide information that is not in the PDFs. Do not explain questions that are not related to the topic. Subject: {tutor.description}."
        
        student_messages = ""
        for user_id, messages in memoryTutor.items():
            if user_id == request.user.id:
                # add messages to the student_messages
                student_messages = messages
                
        print(f"Type of student_messages: {type(student_messages)}, Value of student_messages: {student_messages}")
        
        # Prepare the prompt with the last six messages as context
        context = " ".join(student_messages)
        prompt = f"{context} {combined_content}"
        
        system_prompt = {
            "role": "system", 
            "content": prompt
        }
        
        user_prompt = {"role": "user", "content": message}
        
        

        chat_completion = clientTutor.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[system_prompt, user_prompt],
            max_tokens=150,
            top_p=0.9
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error accessing OpenAI: {str(e)}")
        return "There was an error processing your request."

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse


def tutor_view(request, tutor_id):
    tutor = get_object_or_404(Tutor, pk=tutor_id)
    
    if request.method == 'POST':
        message = request.POST.get('message')
        add_message_to_memory_tutor(message, request.user.id)
        pdf_text = get_pdf_text_tutor(tutor_id)
        response = ask_openai_for_tutor(request, message, pdf_text, tutor_id)
        return JsonResponse({'message': message, 'response': response})

    return render(request, 'app/chat_with_tutor.html', {'tutor': tutor})
"""
# Quiz section
clientQuiz = OpenAI(api_key=settings.OPENAI_API_KEY_QUIZ)

def get_pdf_text_quiz(quiz_id):
    try:
        quiz = Quiz.objects.get(pk=quiz_id)
        pdf_files = quiz.pdfs.all()  # Assuming pdfs is a related name for file fields
        text_content = ""
        for pdf_file in pdf_files:
            reader = PdfReader(pdf_file.file.path)
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        return text_content
    except Exception as e:
        print(f"Error reading PDFs: {str(e)}")
        return ""
    
memoryQuiz = {}
memoryResponses_quiz = {}

def add_message_to_memory_quiz(message, user_id):
    if user_id not in memoryQuiz:
        memoryQuiz[user_id] = []
    memoryQuiz[user_id].append(message)
    
    
def add_response_to_memory_quiz(response, user_id):
    if user_id not in memoryResponses_quiz:
        memoryResponses_quiz[user_id] = []
    memoryResponses_quiz[user_id].append(response)
    if len(memoryResponses_quiz[user_id]) > 3:
        memoryResponses_quiz[user_id].pop(0)
        
def ask_openai_for_quiz(request, message, quiz_id, questions):
    try:
        quiz = Quiz.objects.get(pk=quiz_id)
        report = get_student_info(request)
        
        student_messages = ""
        for user_id, messages in memoryQuiz.items():
            if user_id == request.user.id:
                # add messages to the student_messages
                student_messages = messages   
                
        
        quiz_name = quiz.name
        
        student_questions = questions
        
        print(f"Type of student_questions: {type(student_questions)}, Value of student_questions: {student_questions}")
        
        last_input = student_messages[-1]
        
        print(f"Last input: {last_input}")
                
        
        #test    
        print(f"Type of student_messages: {type(student_messages)}, Value of student_messages: {student_messages}")
        
        quiz_prompt="""
            Your information:\
            -Quiz Name: {quiz_name}\
            \
            Student information:\
            -All user inputs:\
            {student_messages}\
            -Student information:\
            {report}\
            \
            System information:\
            You are an expert in asking questions. Given the questions below, it is your job to \
            create a question for the user. \
            You should ignore all inputs what are not in the format of "start", "next" or "answer "1,2,3,4"\
            With the provided list of questions you should be able to determine the next question.\
            The student has a level of "beginner", "intermediate" or "advanced". Based on the level you should provide the next question.\
            List  of questions: {student_questions}\
            \
            Question example:
            Question: "What is the capital of France?"\
            "1": "Paris",\
            "2": "Berlin",\
            "3": "Lisbon",\
            "4": "Luxembourg",\
            \
                
            The system should determine the output based on the student input.
            This means:
                
            Student input: "start"\
            System output:\
            Question: "What is the capital of France?"\
            "1": "Paris",\
            "2": "Berlin",\
            "3": "Lisbon",\
            "4": "Luxembourg",\
                    
            Student input: "next"\
            Question: "What is the capital of France?"\
            "1": "Paris",\
            "2": "Berlin",\
            "3": "Lisbon",\
            "4": "Luxembourg",\
                
            Student input: "answer "1,2,3,4"\ 
            System output: You responde "correct" or "incorrect"\
                
            Based on the student input you should determine what to do:
            input: {last_input}\
        """
        
        system_prompt = {
            "role": "system", 
            "content": quiz_prompt
        }
        
        user_prompt = {"role": "user", "content": message}

        chat_completion = clientQuiz.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[system_prompt, user_prompt],
            max_tokens=300,
            top_p=0.9
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error accessing OpenAI: {str(e)}")
        return "There was an error processing your request."
    

memoryQuiz = {}

def add_message_to_memory_quiz(message, user_id):
    if user_id not in memoryQuiz:
        memoryQuiz[user_id] = []
    memoryQuiz[user_id].append(message)
    
def quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    pdf_files = quiz.course.pdfs.all()

    if not pdf_files:
        return JsonResponse({"error": "No PDF files found for the course."}, status=404)

    try:
        pdfreader = PdfReader(pdf_files[0].file.path)
        raw_text = ''.join(page.extract_text() or '' for page in pdfreader.pages)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(raw_text)
    del chunks[:10]

    if not chunks:
        return JsonResponse({"error": "No text could be extracted from the PDF."}, status=404)

    

    if request.method == 'POST':
        message = request.POST.get('message', '').strip().lower()
        
        #Take randomly 1/4 of the chunks
        random_chunks = random.sample(chunks, len(chunks)//4)

        if message == "question":
            prompt_text = f"You are a question maker, provide a question with 4 options a,b,c and d, where one is correct,Based on the chunks, formulate a question based with the content, make it not to complicated it should be coding related:\n\n{random_chunks[0]} Example: What is the default behavior of logging messages in Python? a) All types of messages are displayed and sent to standard error. b) Only debugging messages are suppressed and the output is sent to standard error. c) Only informational and debugging messages are suppressed and the output is sent to standard error. d) No messages are suppressed and all messages are sent to a file."
            
        elif message == "a":
            #Check last response and correct it
            last_response = memoryResponses_quiz[request.user.id][-1]
            #Prompt a correction where it check the answer a to the last question
            prompt_text = f"Answer: a, for the question: {last_response}, correct it and provide with 'correct' or 'incorrect', if the question is wrong or correct, in case of being wrong provide the correct answer."
        
        elif message == "b":
            #Check last response and correct it
            last_response = memoryResponses_quiz[request.user.id][-1]
            #Prompt a correction where it check the answer a to the last question
            prompt_text = f"Answer: b, for the question: {last_response}, correct it and provide with 'correct' or 'incorrect', if the question is wrong or correct, in case of being wrong provide the correct answer."
        
        elif message == "c":
            #Check last response and correct it
            last_response = memoryResponses_quiz[request.user.id][-1]
            #Prompt a correction where it check the answer a to the last question
            prompt_text = f"Answer: c, for the question: {last_response}, correct it and provide with 'correct' or 'incorrect', if the question is wrong or correct, in case of being wrong provide the correct answer."
        
        elif message == "d":
            #Check last response and correct it
            last_response = memoryResponses_quiz[request.user.id][-1]
            #Prompt a correction where it check the answer a to the last question
            prompt_text = f"Answer: d, for the question: {last_response}, correct it and provide with 'correct' or 'incorrect', if the question is wrong or correct, in case of being wrong provide the correct answer."
        
        else :
            prompt_text = f"You should tell the student that he can only reply with 'question' or 'a', 'b', 'c', 'd', Do not provide information that is not about the topic in the , this means you should not provide information that is not in the text: {random_chunks[0]}. DO NOT EXPLAIN QUESTIONS THAT ARE NOT RELATED."
                       
            
        system_prompt = {
            "role": "system", 
            "content": prompt_text
        }
        
        user_prompt = {"role": "user", "content": message}

        chat_completion = clientCourse.chat.completions.create(
            model="gpt-4",
            messages=[system_prompt, user_prompt],
            max_tokens=250,
            top_p=0.9
        )
        
        response = chat_completion.choices[0].message.content.strip()
        add_response_to_memory_quiz(response, request.user.id)
        
        
        return JsonResponse({'message': message, 'response': response})

    return render(request, 'app/chat_with_quiz.html', {'quiz': quiz})

#Course section





from PyPDF2 import PdfReader
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS

from langchain.text_splitter import RecursiveCharacterTextSplitter
#from langchain.embeddings import SentenceTransformerEmbeddingsfrom django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import ChatOpenAI  # Ensure correct import path
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from openai import OpenAI

clientCourse = OpenAI(api_key=settings.OPENAI_API_KEY_COURSE)

def course_view(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    pdf_files = course.pdfs.all()

    if not pdf_files:
        return JsonResponse({"error": "No PDF files found for the course."}, status=404)

    try:
        pdfreader = PdfReader(pdf_files[0].file.path)
        raw_text = ''.join(page.extract_text() or '' for page in pdfreader.pages)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(raw_text)
    del chunks[:10]

    if not chunks:
        return JsonResponse({"error": "No text could be extracted from the PDF."}, status=404)

    # Initialize session data if not already present
    if 'course_interaction' not in request.session:
        request.session['course_interaction'] = {
            'current_chunk_index': 0,
            'total_chunks': len(chunks),
            'last_response': '',
            'detail_level': 1,
        }
    session_data = request.session['course_interaction']


    if request.method == 'POST':
        message = request.POST.get('message', '').strip().lower()
        current_chunk_index = session_data.get('current_chunk_index', 0)
        current_chunk = chunks[current_chunk_index] if chunks else "No content available."

        prompt_text = f"You are a friendly student assistant which helps student out in their learning journey, answer the question based on the input of student: {message}\n\n an the text:{current_chunk}, EVERYTHING ELSE IS NOT ALLOWED."

        if message == "start":
            session_data['current_chunk_index'] = 0
            session_data['detail_level'] = 1
            session_data['last_response'] = ''
            request.session.modified = True
            prompt_text = f"Please summarize this content:\n\n{current_chunk}"
        elif message == "next":
            if current_chunk_index < len(chunks) - 1:
                session_data['current_chunk_index'] += 1
                request.session.modified = True  # Mark session as modified to save changes
            current_chunk = chunks[session_data['current_chunk_index']]
            prompt_text = f"Please summarize this content:\n\n{current_chunk}"
        elif message == "prev":
            if current_chunk_index > 0:
                session_data['current_chunk_index'] -= 1
                request.session.modified = True
            current_chunk = chunks[session_data['current_chunk_index']]
            prompt_text = f"Please summarize this content:\n\n{current_chunk}"
            
        system_prompt = {
            "role": "system", 
            "content": prompt_text
        }
        
        user_prompt = {"role": "user", "content": message}

        chat_completion = clientCourse.chat.completions.create(
            model="gpt-4",
            messages=[system_prompt, user_prompt],
            max_tokens=1000,
            top_p=0.9
        )
        response = chat_completion.choices[0].message.content.strip()
        
        session_data['last_response'] = response
        request.session['course_interaction'] = session_data
        return JsonResponse({'message': message, 'response': response, 'current_chunk': current_chunk})

    return render(request, 'app/chat_with_course.html', {'course': course})
import random
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
import openai

# Ensure your OpenAI client is initialized correctly
clientTutor = openai.OpenAI(api_key=settings.OPENAI_API_KEY_TUTOR)

def exam_view(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    pdf_files = course.pdfs.all()

    if not pdf_files:
        return JsonResponse({"error": "No PDF files found for the course."}, status=404)

    try:
        pdfreader = PdfReader(pdf_files[0].file.path)
        raw_text = ''.join(page.extract_text() or '' for page in pdfreader.pages)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(raw_text)
    if len(chunks) <= 10:
        return JsonResponse({"error": "Not enough text to generate questions from."}, status=404)

    selected_chunk = random.choice(chunks)

    prompt_text = f"""
    You are an exam assistant. You need to analyze the text provided and generate 10 multiple-choice questions based on the content. Each question should have four options labeled A, B, C, and D, with only one correct answer. Format the output as a list of Python dictionaries.

    Text: "{selected_chunk}"

    EXAMPLE FORMAT:
    [
        {{"text": "What is the capital of France?", "options": [
            {{"letter": "A", "text": "Paris", "is_correct": True}},
            {{"letter": "B", "text": "London", "is_correct": False}},
            {{"letter": "C", "text": "Berlin", "is_correct": False}},
            {{"letter": "D", "text": "Madrid", "is_correct": False}}
        ]}},
        # More questions should follow in a similar format
    ]
    
    RETURN JSON RESPONSE WITH THE QUESTIONS
    """
    
    system_prompt = {
        "role": "system", 
        "content": prompt_text
    }
    
    messages = [system_prompt]
    # Assuming you've setup OpenAI API client
    try:
        chat_completion = clientTutor.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            max_tokens=2500,
            response_format={ "type": "json_object" }
        )
          
        
        questions = chat_completion.choices[0].message.content
        print(f"Questions: {questions}")
        response = json.loads(questions)
        questions = response['questions']
    except Exception as e:
        return JsonResponse({"error": "Failed to generate questions: " + str(e)}, status=500)
    
    
    
    if request.method == 'POST':
        score = 0
        for i, question in enumerate(questions, start=1):
            answer = request.POST.get(f'question_{i}')
            correct_option = next((o for o in question['options'] if o['is_correct']), None)
            if correct_option and correct_option['letter'] == answer:
                score += 1
        return JsonResponse({"score": score, "total": len(questions)})

    return render(request, 'app/chat_with_exam.html', {'course': course, 'questions': questions})


    