import logging
import os
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

def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.user.is_authenticated and hasattr(request.user, 'teacher') and quiz.teacher == request.user.teacher:
        quiz.delete()
        request.user.teacher.quiz_list.remove(quiz)
    return redirect('teacher_quiz')

class TeacherTutorView(LoginRequiredMixin, ListView):
    model = Tutor
    template_name = 'app/teacher_ai_tutor.html'
    form_class = SimpleTutorForm  # Assume this is a simplified form
    success_url = reverse_lazy('teacher_ai_tutor')

    def get_queryset(self):
        if hasattr(self.request.user, 'teacher'):
            return Tutor.objects.filter(teacher=self.request.user.teacher)
        else:
            return Tutor.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tutor_form'] = self.form_class()  # No need to pass user here if the form is simplified
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            tutor = form.save(commit=False)
            tutor.teacher = request.user.teacher
            tutor.save()

            # add tutor to teacher's tutor list
            request.user.teacher.tutor_list.add(tutor)
            tutor.save()

            messages.success(request, "Tutor created successfully!")
            return redirect(self.success_url)
        else:
            return render(request, self.template_name, {'form': form, 'object_list': self.get_queryset(), 'errors': form.errors})
        

def delete_tutor(request, tutor_id):
    tutor = get_object_or_404(Tutor, id=tutor_id)
    if request.user.is_authenticated and hasattr(request.user, 'teacher') and tutor.teacher == request.user.teacher:
        tutor.delete()
        request.user.teacher.tutor_list.remove(tutor)
    return redirect('teacher_ai_tutor')
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
                    pdf = PDF.objects.get(id=pdf_id)
                    course.pdfs.add(pdf)

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
                course.delete()
                print(f"Course {course_id} deleted.")
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
from .models import Tutor, Student

@login_required
def unenroll_tutor(request, tutor_id):  # Function to handle unenrollment
    student_profile = request.user.profile.student  # Access the student profile
    tutor = get_object_or_404(Tutor, id=tutor_id)  # Get the tutor instance

    # Check if the student is enrolled in the tutor and remove if they are
    if tutor in student_profile.tutors.all():
        student_profile.tutors.remove(tutor)

    return redirect('student_ai_tutor')  # Redirect to a view showing all tutors for the student
 # Redirect to the page where courses are listed or another appropriate page.


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Quiz, Student

@login_required
@login_required
def unenroll_course(request, course_id):  # Change 'quiz_id' to 'course_id'
    student_profile = request.user.profile.student
    course = get_object_or_404(Course, id=course_id)  # Change 'Quiz' to 'Course'

    if course in student_profile.courses.all():
        student_profile.courses.remove(course)

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
    
class StudentTutorView(LoginRequiredMixin, ListView):
    model = Tutor
    template_name = 'app/student_ai_tutor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile') and hasattr(self.request.user.profile, 'student'):
            student_profile = self.request.user.profile.student
            enrolled_tutors = student_profile.tutors.all()
            all_tutors = Tutor.objects.exclude(id__in=enrolled_tutors.values_list('id', flat=True))
        else:
            all_tutors = Tutor.objects.none()  # Show no tutors if user is not authenticated or has no student profile
        context['all_tutors'] = all_tutors
        context['enrolled_tutors'] = enrolled_tutors
        context['form'] = TutorEnrollmentForm(user=self.request.user)  # Adjust form as necessary
        return context

    def post(self, request, *args, **kwargs):
        selected_tutor_id = request.POST.get('tutor')
        if selected_tutor_id:
            tutor = get_object_or_404(Tutor, id=selected_tutor_id)
            student_profile = request.user.profile.student
            if tutor not in student_profile.tutors.all():
                student_profile.tutors.add(tutor)  # Add the tutor to the student's list of enrolled tutors
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
                return redirect('student_courses')
            else:
                return HttpResponseRedirect('/student/already_enrolled')
        return HttpResponseRedirect('/error')


from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Quiz, Student  # Ensure these are correctly imported

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
from .models import Tutor

class EnrollTutorView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        print("User authenticated:", request.user.is_authenticated)
        tutor_id = request.POST.get('tutor_id')
        print("Tutor ID received:", tutor_id)

        if not tutor_id:
            print("No tutor ID provided.")
            return HttpResponseRedirect('/error')

        tutor = get_object_or_404(Tutor, id=tutor_id)
        student_profile = request.user.profile.student
        print("Attempting to enroll in tutor:", tutor.name)

        if tutor in student_profile.tutors.all():
            print("Already enrolled with this tutor.")
            return HttpResponseRedirect('/student/already_enrolled')

        student_profile.tutors.add(tutor)
        print("Enrollment successful.")
        return redirect('student_ai_tutor')

    

def stu_dashboard(request):
    return render(request, 'app/stu_dashboard.html')

def te_dashboard(request):
    return render(request, 'app/te_dashboard.html')


from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from .models import Tutor

def tutor_view(request, tutor_id):
    try:


        # Redirect to a view where these resources are used
        # Example: redirect to a resource display view
        return redirect('display_resources')
    except Tutor.DoesNotExist:
        messages.error(request, "Tutor not found")
        return redirect('error_view')  # Redirect to an error page or appropriate action
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('error_view')  # Redirect to an error page or appropriate action

def display_resources_view(request, tutor_id):
    resources = request.session.get('tutor_resources', [])
    if not resources:
        messages.error(request, "No resources found or session expired.")
        return redirect('some_default_view')

    return HttpResponse('<br>'.join(resources))  # Display resources; customize as needed

def error_view(request):
    return render(request, 'app/error.html', {'error_message': 'A generic error occurred.'})


from django.shortcuts import render, get_object_or_404
from .models import Tutor

def chat_with_tutor(request, tutor_id):
    tutor = get_object_or_404(Tutor, pk=tutor_id)
    
    # Example static introduction
    introduction = f"Hello, I am {tutor.name}, your personal tutor assistant. How can I assist you today?"

    # If you have more dynamic content, you might fetch or generate it here
    
    context = {
        'tutor': tutor,
        'introduction': introduction,
    }
    return render(request, 'app/chat_with_tutor.html', context)

import openai
from django.conf import settings

# Set the API key from Django settings
openai.api_key = settings.OPENAI_API_KEY

import openai
from django.conf import settings

# Set the API key from Django settings
openai.api_key = settings.OPENAI_API_KEY

from openai import OpenAI
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def get_ai_response(prompt, report = None):
    try:
        # Prepare the conversation context with system and previous chat history if needed
        system_prompt = {
            "role":  "system", 
            "content": "You are a assistant chatbot helping students with their queries. You are a teacher explaining a concept to a student. As a python tutor, you are helping a student with a coding problem and simple theoretical questions. Python programming assistant chatbot. Important= Everything else that is not included inside the topic gets deleted. Always ask if student has understood it. Your student information: "+report+" -base the information on it. In case of asking for report return the report of student" }
        
        user_prompt = {"role": "user", "content": prompt}

        # Using the Completion method with conversation context
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Adjust this to the latest available model, if different
            messages=[system_prompt, user_prompt],  # Combine prompts for context
            max_tokens=150,
            top_p=0.9
        )
        # Extracting the response text from the latest API response structure
        return chat_completion.choices[0].message.content.strip()  # Adjust accessing the content
    except Exception as e:
        print(f"Error accessing OpenAI: {str(e)}")
        return "There was an error processing your request."


import json
import openai
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def send_message(request):
    #get student 
    student = request.user.profile.student
    #get selected tutor
    student_rep = student_report(student)
    
    try:
        data = json.loads(request.body,)  # Parsing the JSON body of the POST request
        user_message = data.get('message')
        response_message = get_ai_response(user_message, student_rep)  # Fetching the AI response
        return JsonResponse({'reply': response_message})
    except json.JSONDecodeError as e:
        return JsonResponse({'error': 'Invalid JSON', 'details': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'OpenAI API error', 'details': str(e)}, status=500)


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, HttpResponse
from .models import Course, Student
from django.conf import settings
import openai

# Initialize the OpenAI client with your API key

def student_report(student):
    # Make sure to access the correct attributes based on your Student model structure
    if hasattr(student, 'profile'):
        return f"Student: {student.profile.fname} {student.profile.lname} | Level: {student.level} | Role: {student.profile.role}"
    else:
        return f"Student: {student.user.first_name} {student.user.last_name} | Level: {student.level} | Role: {student.role}"


import openai
from django.conf import settings

# Set the API key globally or in each function as needed
openai.api_key = settings.OPENAI_API_KEY

def get_ai_response(prompt, report=None):
    client = OpenAI(api_key=openai.api_key)
    
    try:
        # Define your messages for the chat API call
        messages = [
            {"role": "system", "content": "You are an assistant chatbot."},
            {"role": "user", "content": prompt}
        ]

        if report:
            messages.append({"role": "system", "content": f"Your student information: {report}"})

        # Make the API call using the chat completion API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
        # Extracting the response text correctly from the API response structure
        
    except Exception as e:
        print(f"Error accessing OpenAI: {str(e)}")
        return "There was an error processing your request."



from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, HttpResponse
from django.http import JsonResponse
from .models import Course, Student
from .agents import CourseCreatorAgent  # Assuming your CourseCreatorAgent is in agents.py
from django.conf import settings

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, HttpResponse
from django.http import JsonResponse
from .models import Course, Student
from .agents import CourseCreatorAgent  # Make sure the import is correct  # Ensure these utility functions are imported if needed
from django.conf import settings

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, HttpResponse
from django.http import JsonResponse
from .models import Course, Student
from .agents import CourseCreatorAgent  # Ensure this is correctly imported
from django.conf import settings
import openai
from .agents import CourseCreatorAgent
from django.conf import settings
import openai

@login_required
def course_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not hasattr(request.user, 'student'):
        return HttpResponse("You need a student profile to access this page.", status=403)

    student = request.user.student
    student_info = student_report(student)
    # Initialize with openai key
    agent = CourseCreatorAgent(openai.api_key)

    if request.method == 'POST':
        print("Received POST data:", request.POST)  # Debugging line to see exactly what is received

        prompt = request.POST.get('prompt', None)
        action = request.POST.get('action', None)

        if prompt:
            response_message = get_ai_response(prompt, student_info)
            return render(request, 'app/course_with_generator.html', {
                'course': course,
                'ai_response': response_message,
                'student_report': student_info
            })

        elif action == 'generate_course':
            pdf_files = [pdf.file.path for pdf in course.pdfs.all()]
            course_content = agent.generate_course_content(student_info, pdf_files)
            return render(request, 'app/course_with_generator.html', {
                'course': course,
                'course_content': course_content,
                'student_report': student_info
            })

        else:
            return HttpResponse(f"Invalid action: {action}")

    else:
        # Display the initial course view without interaction
        return render(request, 'app/student_dashboard.html', {'course': course})