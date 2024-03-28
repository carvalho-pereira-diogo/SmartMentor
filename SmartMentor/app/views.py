from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.views.generic import ListView, DetailView
from django.views import generic
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.db import IntegrityError
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Defome courses inside the home view T

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

        # Create User and Profile instances within an atomic transaction
        # Create User
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, first_name=fname, last_name=lname, email=email, password=pass1)
                profile = Profile(user=user, username=username, fname=fname, lname=lname, email=email, role=role)
                profile.save()

                if role.lower() == 'student':
                    student = Student(profile=profile, level=level)
                    student.save()
                elif role.lower() == 'teacher':
                    teacher = Teacher(profile=profile)
                    teacher.save()

                messages.success(request, "Your account has been created successfully!")
                return redirect('login')
        except IntegrityError as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('signup')
    else:
        # If it's not a POST request, just render the signup form page.
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
    
class StudentProfileView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = 'app/student_profile.html'
    
    def get_object(self):
        if hasattr(self.request.user, 'student'):
            return self.request.user.student
        else:
            return redirect('student_profile')
    
from django.shortcuts import redirect

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
        
class StudentQuizView(ListView):
    model = Quiz
    template_name = 'app/student_quiz.html'
    
    def get_object(self):
        if hasattr(self.request.user, 'student'):
            return self.request.user.student
        else:
            return redirect('student_quiz')
        
class TeacherTutorView(ListView):
    model = Tutor
    template_name = 'app/teacher_ai_tutor.html'
    
    def get_object(self):
        if hasattr(self.request.user, 'teacher'):
            return self.request.user.teacher
        else:
            return redirect('teacher_ai_tutor')
        
class StudentTutorView(ListView):
    model = Tutor
    template_name = 'app/student_ai_tutor.html'
    
    def get_object(self):
        if hasattr(self.request.user, 'student'):
            return self.request.user.student
        else:
            return redirect('student_ai_tutor')

# is this possible that 
@method_decorator(login_required, name='dispatch')
class TeacherCourseView(ListView):
    model = Course
    template_name = 'app/teacher_course.html'
    
    def get_queryset(self):
        if hasattr(self.request.user, 'teacher'):
            return self.request.user.teacher.course_set.all()
        else:
            return Course.objects.none()  # Return an empty QuerySet
        
    def get_object(self):
        if hasattr(self.request.user, 'teacher'):
            return self.request.user.teacher
        else:
            return redirect('teacher_course')
    
class StudentCourseView(ListView):
    model = Course
    template_name = 'app/student_course.html'
    
    def get_object(self):
        if hasattr(self.request.user, 'student'):
            return self.request.user.student
        else:
            return redirect('student_ai_tutor')

@login_required
def upload_course_pdf(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('course')
        else:
            form = CourseForm()
        return render(request, 'app/upload_course.html', {'form': form})
    
@login_required
def course_upload(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('course_list')  # Redirect to a URL where you list the courses
    else:
        form = CourseForm()
    return render(request, 'app/course_upload.html', {'form': form})

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

def stu_dashboard(request):
    return render(request, 'app/stu_dashboard.html')

def te_dashboard(request):
    return render(request, 'app/te_dashboard.html')


#Later on, create UpdateCourseView and DeleteCourseView classes
#Create 2 different profile views, one for students and one for teachers
    