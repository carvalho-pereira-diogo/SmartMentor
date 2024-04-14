import os
import fitz 
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
from .agents import LearningAgents
from .tools import *
from .tasks import *

learning_agents = LearningAgents(openai_api_key='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')

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
                    student = Student(profile=profile, level=level)
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
class TeacherQuizView(ListView):
    model = Quiz
    template_name = 'app/teacher_quiz.html'
    
    def get_object(self):
        if hasattr(self.request.user, 'teacher'):
            return self.request.user.teacher
        else:
            return redirect('teacher_quiz')
        
class TeacherTutorView(LoginRequiredMixin, ListView):
    template_name = 'app/teacher_ai_tutor.html'

    def get_queryset(self):
        # Override this method to return a QuerySet of Tutor objects that belong to the current user's Teacher instance
        if hasattr(self.request.user, 'teacher'):
            return Tutor.objects.filter(teacher=self.request.user.teacher)
        else:
            return Tutor.objects.none()
        
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

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

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
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()

            # Use the CourseAgent to process PDFs for the course
            course_agent = learning_agents.course_agent()
            pdf_paths = []  # Replace with the actual PDF paths
            course_materials = course_agent.process_pdfs_for_course(pdf_paths)

            # Associate the processed PDFs with the course
            for material in course_materials:
                pdf = PDF.objects.create(file=material)  # Replace with the actual PDF creation code
                course.pdfs.add(pdf)

            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm()

    return render(request, 'app/teacher_course.html', {'form': form})

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
@require_POST
def enroll_in_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    request.user.student.courses.add(course)
    return redirect('course_detail', course_id=course.id) 

@login_required
def unenroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    student = request.user.profile.student  # Adjust this based on how your Student model is linked to User

    if course in student.courses.all():
        student.courses.remove(course)
        messages.success(request, "You have successfully unenrolled from the course.")
    else:
        messages.error(request, "You are not enrolled in this course.")

    return redirect('student_courses')  # Redirect to the page where courses are listed or another appropriate page.

@login_required
@require_POST
def enroll_in_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    student = get_object_or_404(Student, profile__user=request.user)
    # Use the QuizAgent to do something
    quiz_agent = learning_agents.quiz_agent()
    # quiz_agent.do_something()

    return redirect('quiz_detail', quiz_id=quiz.id)

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

        
class StudentQuizView(ListView):
    template_name = 'app/student_ai_tutor.html'

    def get_queryset(self):
        # Override this method to return a QuerySet of Tutor objects that belong to the current user's Teacher instance
        if hasattr(self.request.user, 'student'):
            return Tutor.objects.filter(student=self.request.user.student)
        else:
            return Tutor.objects.none()
        
class StudentTutorView(ListView):

    model = Course
    template_name = 'app/student_ai_tutor.html'
    
    def get_queryset(self):
        # Override this method to return a QuerySet of Tutor objects that belong to the current user's Teacher instance
        if hasattr(self.request.user, 'student'):
            return Tutor.objects.filter(teacher=self.request.user.student)
        else:
            return Tutor.objects.none()

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
        context['message'] = "You are already enrolled in this course."
        return context
    
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from .models import Course, Student

class EnrollCourseView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        course_id = request.POST.get('course')
        if course_id:
            course = get_object_or_404(Course, id=course_id)
            student_profile = request.user.profile.student
            if course not in student_profile.courses.all():
                student_profile.courses.add(course)
                return redirect('student_courses')
            else:
                return HttpResponseRedirect('/student/already_enrolled')
        return HttpResponseRedirect('/error')


def stu_dashboard(request):
    return render(request, 'app/stu_dashboard.html')

def te_dashboard(request):
    return render(request, 'app/te_dashboard.html')
