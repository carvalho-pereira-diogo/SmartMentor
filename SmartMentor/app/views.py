import logging
import os
import PyPDF2
import fitz 
import json
import openai
from openai import OpenAI
import random
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.http import FileResponse, Http404, HttpResponse, HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.views.generic import ListView, DetailView, TemplateView
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
from django.views import View
from .models import *
from .forms import *
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS

# -Home page, Dashboard

# return the home page
def home(request):
    return render(request, 'app/home.html')

# stu_dashboard helps to return the student dashboard
def stu_dashboard(request):
    return render(request, 'app/stu_dashboard.html')

# te_dashboard helps to return the teacher dashboard
def te_dashboard(request):
    return render(request, 'app/te_dashboard.html')

# -User login, register, logout

# return the login page
class UserLoginView(LoginView):
    template_name = 'app/login.html'  # Replace with your login template
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')

# return the logout page
class LogoutOnGetView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

# return the signup page (register page)
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
        
        # Basic validations
        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please try another username.")
            return redirect('signup')  # Assuming 'signup' is the name of your signup page URL

        # Check if the email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists. Please try another email.")
            return redirect('signup')

        # Check if the username is too long
        if len(username) > 10:
            messages.error(request, "Username must be under 10 characters.")
            return redirect('signup')

        # Check if the passwords match
        if pass1 != pass2:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')

        # Check if the username contains only letters and numbers
        if not username.isalnum():
            messages.error(request, "Username should only contain letters and numbers.")
            return redirect('signup')

        # Check if the role is either 'Student' or 'Teacher', and create the user 
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, first_name=fname, last_name=lname, email=email, password=pass1)
                profile = Profile(user=user, username=username, fname=fname, lname=lname, email=email, role=role)
                profile.save()
                
                #Create a student or teacher based on the role
                if role.lower() == 'student':
                    student = Student(user=user, profile=profile)
                    student.save()
                elif role.lower() == 'teacher':
                    teacher = Teacher(user=user, profile=profile)
                    teacher.save()

                messages.success(request, "Your account has been created successfully!")
                
                # Redirect to the login page
                return redirect('login')
        except IntegrityError as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('signup')
    else:
        return render(request, 'app/signup.html')

# return the signin page
def signin(request):
    # Check if the request is a POST request, else return the login page
    if request.method == "POST":
        # Check for username and password
        username = request.POST['username']
        pass1 = request.POST['pass1']
        
        # Authenticate the user
        user = authenticate(request, username=username, password=pass1)
        
        # If the user is authenticated, log them in. Otherwise, show an error message.
        if user is not None:
            login(request, user)
            return redirect("home")  
        else:
            messages.error(request, "Invalid credentials, please try again.")
            return redirect("login") 
        
    else:
        return render(request, 'app/login.html')
    
# return the signout page
def signout(request):
    # Sign out the user and redirect to the home page
    logout(request)
    return redirect('home')

# -Teacher section

# return the teacher profile page
class TeacherProfileView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = 'app/teacher_profile.html'
    
    # Get the teacher object
    def get_object(self):
        if hasattr(self.request.user, 'teacher'):
            return self.request.user.teacher
        else:
            return redirect('teacher_profile')
        


# return the teacher pdf upload page
class TeacherPDFView(LoginRequiredMixin, ListView):
    model = PDF
    form_class = PDFUploadForm
    template_name = 'app/teacher_pdf_upload.html'

    # Get the PDFs associated with the teacher
    def get_queryset(self):
        if hasattr(self.request.user, 'teacher'):
            return PDF.objects.filter(uploaded_by=self.request.user.teacher)
        else:
            return PDF.objects.none()

    # Get the context data of the teacher and the PDFs
    def post(self, request, *args, **kwargs):
        # Handle the form submission
        form = self.form_class(request.POST, request.FILES)
        # Check if the form is valid
        if form.is_valid():
            # Save the form
            pdf = form.save(commit=False)
            # Associate the uploaded PDF with the teacher
            if hasattr(request.user, 'teacher'):
                pdf.uploaded_by = request.user.teacher
                pdf.save()
                request.user.teacher.pdfs.add(pdf)
            return redirect('teacher_pdfs')
        else:
            pdfs = self.get_queryset()
            return render(request, self.template_name, {'form': form, 'object_list': pdfs})

# return the teacher pdf delete page
@login_required
def delete_pdf(request, pdf_id):
    # Get the PDF object
    pdf = get_object_or_404(PDF, id=pdf_id)
    # Check if the user is authenticated and the PDF was uploaded by the user
    if request.user.is_authenticated and hasattr(request.user, 'teacher') and pdf.uploaded_by == request.user.teacher:
        # Delete the PDF and remove it from the teacher's PDF list
        pdf.delete()
        request.user.teacher.pdfs.remove(pdf)
    return redirect('teacher_pdfs')

# Create courses and quizzes by extracting text from PDFs from the teacher
class TeacherCourseView(LoginRequiredMixin, ListView):
    model = Course
    form_class = CourseForm
    template_name = 'app/teacher_course.html'

    # Get the courses associated with the teacher
    def get_queryset(self):
        if hasattr(self.request.user, 'teacher'):
            return Course.objects.filter(teacher=self.request.user.teacher)
        else:
            return Course.objects.none()

    # Get the context data of the teacher and the courses
    def post(self, request, *args, **kwargs):
        # Handle the form submission
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            # Save the form
            course = form.save(commit=False)
            # Associate the course with the teacher
            if hasattr(request.user, 'teacher'):
                # Save the course and add it to the teacher's course list
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
                quiz = Quiz(course=course, name="Digital Quiz Agent for " + course.name, teacher=request.user.teacher)
                quiz.save()

                # Add the quiz to the teacher's quizzes list
                request.user.teacher.quizzes.add(quiz)

            return redirect('teacher_courses')
        else:
            courses = self.get_queryset()
            return render(request, self.template_name, {'form': form, 'object_list': courses})

# delete the course from the teacher's course list
@login_required
def delete_course(request, course_id):
    # Get the course object
    course = get_object_or_404(Course, id=course_id)
    if request.user.is_authenticated:
        # Check if the user is a teacher and the course belongs to the teacher
        if hasattr(request.user, 'teacher'):
            if course.teacher == request.user.teacher:
                # Remove the quizzes associated with the course
                # Delete the course and remove it from the teacher's course list
                Quiz.objects.filter(course=course).delete()
                course.delete()
            else:
                # Debug print
                print(f"The course's teacher is not the same as the user's teacher. Course teacher: {course.teacher}, User's teacher: {request.user.teacher}")
        else:
            # Debug print
            print("The user does not have a teacher attribute.")
    else:
        # Debug print
        print("The user is not authenticated.")
    # Redirect to the teacher's course view
    return redirect('teacher_courses')

# course_list helps to list the courses
@login_required
def course_list(request):
    # Get the courses from the database
    if hasattr(request.user, 'teacher'):
        teacher_courses = Course.objects.filter(teacher=request.user.teacher)
        other_courses = Course.objects.exclude(teacher=request.user.teacher)
    else:
        # If the user is not a teacher, show all courses (helps the student view all courses)
        teacher_courses = Course.objects.none()
        other_courses = Course.objects.all()
    return render(request, 'stu_course.html', {'teacher_courses': teacher_courses, 'other_courses': other_courses})

# teacher_courses helps to list the teacher's courses
@login_required
def teacher_courses(request):
    # Get the courses from the database
    if hasattr(request.user, 'teacher'):
        # Get the courses associated with the teacher
        courses = Course.objects.filter(teacher=request.user.teacher)
    else:
        # If the user is not a teacher, show no courses
        courses = Course.objects.none()
    return render(request, 'te_courses.html', {'courses': courses})

#- Student section

# StudentProfileView
class StudentProfileView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = 'app/student_profile.html'
    
    #Get the courses of the teacher
    def get_object(self):
        if hasattr(self.request.user, 'student'):
            return self.request.user.student
        else:
            return redirect('student_profile')


# unenroll_course helps to unenroll the course from student
@login_required
def unenroll_course(request, course_id): 
    student_profile = request.user.profile.student
    course = get_object_or_404(Course, id=course_id)  

    # Check if the student is enrolled in the course
    if course in student_profile.courses.all():
        # Remove the course from the student's list of enrolled courses
        student_profile.courses.remove(course)
        
        # Remove the quizzes associated with the course
        quiz = get_object_or_404(Quiz, course=course)
        # Check if the student is enrolled in the quiz
        if quiz in student_profile.quizzes.all():
            # Remove the quiz from the student's list of enrolled quizzes
            student_profile.quizzes.remove(quiz)

    return redirect('student_courses') 

# StudentQuizView helps to list the student's quiz
class StudentQuizView(LoginRequiredMixin, ListView):
    model = Quiz
    template_name = 'app/student_quiz.html'
    
    # Get the context data of the student
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the student's profile
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
            # Get the student's quizzes
            student_profile = self.request.user.profile.student
            enrolled_quizzes = student_profile.quizzes.all()
            all_quizzes = Quiz.objects.exclude(id__in=enrolled_quizzes.values_list('id', flat=True))
        else:
            # Show no quizzes if user is not authenticated or has no profile
            all_quizzes = Quiz.objects.none()  
        
        # Add the quizzes to the context
        context['all_quizzes'] = all_quizzes
        context['enrolled_quizzes'] = enrolled_quizzes
        context['form'] = QuizEnrollmentForm(user=self.request.user)
        return context

    # Post the quiz
    def post(self, request, *args, **kwargs):
        selected_quiz_id = request.POST.get('quiz')
        print(f"Selected quiz ID: {selected_quiz_id}")  # Debug print
        if selected_quiz_id:
            quiz = get_object_or_404(Quiz, id=selected_quiz_id)
            student_profile = request.user.profile.student
            if quiz not in student_profile.quizzes.all():
                student_profile.quizzes.add(quiz)  # Add the quiz to the student's list of enrolled quizzes
                print(f"Enrolled quizzes after enrollment: {student_profile.quizzes.all()}")  # Debug print
                return HttpResponseRedirect('.')  # Redirect to the current URL
            else:
                return HttpResponseRedirect('/already_enrolled')  # Handle already enrolled scenario
        return HttpResponseRedirect('/error') 
    
# StudentCourseView helps to list the student's course
class StudentCourseView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'app/student_course.html'

    # Get the context data of the student
    def post(self, request, *args, **kwargs):
        selected_course_id = request.POST.get('course')
        if selected_course_id:
            # Get the selected course
            course = get_object_or_404(Course, id=selected_course_id)
            student_profile = request.user.profile.student  
            # Check if the student is not already enrolled in the course
            if course not in student_profile.courses.all():
                # Add the course to the student's list of enrolled courses
                student_profile.courses.add(course) 
                return redirect('student_courses')  
            else:
                # Redirect to the already enrolled page
                return HttpResponseRedirect('/already_enrolled')  # Handle already enrolled scenario
        return HttpResponseRedirect('/error') 

    # Get the context data of the student
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the student's profile
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
            # Get the student's courses
            student_profile = self.request.user.profile.student
            enrolled_courses = student_profile.courses.all()
            all_courses = Course.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))
        else:
            # Show no courses if user is not authenticated or has no profile
            all_courses = Course.objects.none() 
        # Add the courses to the context
        context['all_courses'] = all_courses
        context['enrolled_courses'] = enrolled_courses
        return context

# ErrorView helps to show the error page
@method_decorator(login_required, name='dispatch')
class ErrorView(TemplateView):
    template_name = 'app/error.html'

    # Get the context data of the error
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "An unexpected error has occurred. Please try again."
        return context

# AlreadyEnrolledView helps to show the already enrolled page
@method_decorator(login_required, name='dispatch')
class AlreadyEnrolledView(TemplateView):
    template_name = 'app/already_enrolled.html'

    # Get the context data of the already enrolled page
    def get_context_data(self, **kwargs):
        # Get the context data of the already enrolled page
        context = super().get_context_data(**kwargs)
        context['message'] = "You are already enrolled."
        return context

# EnrollCourseView helps to enroll the course for the student
class EnrollCourseView(LoginRequiredMixin, View):
    # Post the course
    def post(self, request, *args, **kwargs):
        # Get the course ID from the POST request
        course_id = request.POST.get('course_id')  # Change 'course' to 'course_id'
        if course_id:
            # Get the course object
            course = get_object_or_404(Course, id=course_id)
            # Get the student's profile
            student_profile = request.user.profile.student
            # Check if the student is not already enrolled in the course
            if course not in student_profile.courses.all():
                # Add the course to the student's list of enrolled courses
                student_profile.courses.add(course)
                # Add the quizzes associated with the course to the student's list of enrolled quizzes
                quiz = get_object_or_404(Quiz, course=course)
                # Check if the student is not already enrolled in the quiz
                student_profile.quizzes.add(quiz)
                return redirect('student_courses')
            else:
                # Redirect to the already enrolled page
                return HttpResponseRedirect('/student/already_enrolled')
        return HttpResponseRedirect('/error')

# EnrollQuizView helps to enroll the quiz for the student
class StudentLearningPathView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'app/student_learningpath.html'

    # Get the context data of the student
    def get_context_data(self, **kwargs):
        # Get the context data of the student
        context = super().get_context_data(**kwargs)
        # Get the student's profile
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
            # Get the student's courses
            student_profile = self.request.user.profile.student
            enrolled_courses = student_profile.courses.all()
            all_courses = Course.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))
        else:
            # Show no courses if user is not authenticated or has no profile
            all_courses = Course.objects.none()
        # Add the courses to the context
        context['all_courses'] = all_courses
        context['enrolled_courses'] = enrolled_courses
        return context
    
# StudentExamView helps to list the student's exam
class StudentExamView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'app/student_exam.html'

    # Get the context data of the student
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the student's profile
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
            # Get the student's courses
            student_profile = self.request.user.profile.student
            # Get the courses associated with the student
            enrolled_courses = student_profile.courses.all()
            # Get the courses not associated with the student
            all_courses = Course.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))
        else:
            # Show no courses if user is not authenticated or has no profile 
            all_courses = Course.objects.none()
        # Add the courses to the context
        context['all_courses'] = all_courses
        context['enrolled_courses'] = enrolled_courses
        return context

# get_student_info helps to get the student information
def get_student_info(request):
    try:
        # Get the student object
        student = Student.objects.get(user=request.user)
        # Return the student information
        return {
            'username': student.user.username, 
            'fname': student.user.first_name,
            'lname': student.user.last_name,  
            'email': student.user.email,
            'role': student.profile.role, 
            'level': student.level
        }
    except Student.DoesNotExist:
        return None



# -Quiz section

# memoryResponses_quiz helps to store the responses of the quiz
memoryResponses_quiz = {}
    
# add_response_to_memory_quiz helps to add the response to the memory of the quiz
def add_response_to_memory_quiz(response, user_id):
    # Check if the user ID is not in the memory
    if user_id not in memoryResponses_quiz:
        # Add the user ID to the memory
        memoryResponses_quiz[user_id] = []
    # Add the response to the memory
    memoryResponses_quiz[user_id].append(response)
    # Check if the memory has more than 3 responses
    if len(memoryResponses_quiz[user_id]) > 3:
        # Remove the first response from the memory
        memoryResponses_quiz[user_id].pop(0)
        
    
# ClientQuiz helps to create a client for OpenAI
clientQuiz = OpenAI(api_key=settings.OPENAI_API_KEY_QUIZ)

# quiz_view helps to view the quiz
def quiz_view(request, quiz_id):
    # Get the quiz object
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    pdf_files = quiz.course.pdfs.all()

    # Check if there are no PDF files
    if not pdf_files:
        return JsonResponse({"error": "No PDF files found for the course."}, status=404)

    # Extract text from the first PDF file
    try:
        pdfreader = PdfReader(pdf_files[0].file.path)
        raw_text = ''.join(page.extract_text() or '' for page in pdfreader.pages)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # Split the text into chunks
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200)
    # Split the text
    chunks = text_splitter.split_text(raw_text)
    # Get the first 10 chunks, delete them which is the introduction of the pdf
    del chunks[:10]

    # Check if there are no chunks
    if not chunks:
        return JsonResponse({"error": "No text could be extracted from the PDF."}, status=404)
    
    # Get the last message
    if request.method == 'POST':
        # Get the message from the request
        message = request.POST.get('message', '').strip().lower()
        
        # random_chunks helps to get the random chunks
        random_chunks = random.sample(chunks, len(chunks)//4)
        
        response = ""

        # Check if message is question, and prompt it
        if message == "question":
            prompt_text = f"You are a question maker, provide a question with 4 options a,b,c and d, where one is correct,Based on the chunks, formulate a question based with the content, make it not to complicated it should be coding related:\n\n{random_chunks[0]} Example: What is the default behavior of logging messages in Python? a) All types of messages are displayed and sent to standard error. b) Only debugging messages are suppressed and the output is sent to standard error. c) Only informational and debugging messages are suppressed and the output is sent to standard error. d) No messages are suppressed and all messages are sent to a file. Do not ask question about chapters, versions, sections and code snippets."
        # Check if message is a, b, c, or d, and prompt it
        elif message == "a":
            # Check last response and correct it
            last_response = memoryResponses_quiz[request.user.id][-1]
            prompt_text = f"Answer: a, for the question: {last_response}, correct it and provide with 'correct' or 'incorrect', if the question is wrong or correct, in case of being wrong provide the correct answer. Also explain why it is correct or incorrect. Give always a small explanation."
        
        elif message == "b":
            #Check last response and correct it
            last_response = memoryResponses_quiz[request.user.id][-1]
            prompt_text = f"Answer: b, for the question: {last_response}, correct it and provide with 'correct' or 'incorrect', if the question is wrong or correct, in case of being wrong provide the correct answer. Also explain why it is correct or incorrect. Give always a small explanation."
        
        elif message == "c":
            #Check last response and correct it
            last_response = memoryResponses_quiz[request.user.id][-1]
            prompt_text = f"Answer: c, for the question: {last_response}, correct it and provide with 'correct' or 'incorrect', if the question is wrong or correct, in case of being wrong provide the correct answer. Also explain why it is correct or incorrect. Give always a small explanation."
        
        elif message == "d":
            #Check last response and correct it
            last_response = memoryResponses_quiz[request.user.id][-1]
            prompt_text = f"Answer: d, for the question: {last_response}, correct it and provide with 'correct' or 'incorrect', if the question is wrong or correct, in case of being wrong provide the correct answer. Also explain why it is correct or incorrect. Give always a small explanation."
        
        else :
            # Check if the message is not a, b, c, d, or question and prompt it
            prompt_text = f"You should tell the student that he can only reply with 'question' or 'a', 'b', 'c', 'd', Do not provide information that is not about the topic in the , this means you should not provide information that is not in the text: {random_chunks[0]}. DO NOT EXPLAIN QUESTIONS THAT ARE NOT RELATED."
            
        # Check if message is a, b, c, or d, and start the chat        
        if message == "a" or message == "b" or message == "c" or message == "d":
            system_prompt = {
                "role": "system", 
                "content": prompt_text
            }
            
            # get the user prompt
            user_prompt = {"role": "user", "content": message}

            # Create a chat completion
            chat_completion = clientCourse.chat.completions.create(
                model="gpt-4",
                messages=[system_prompt, user_prompt],
                max_tokens=250,
                top_p=0.9
            )
            
            # Get the response
            response = chat_completion.choices[0].message.content.strip()
            # Add the response to the memory
            add_response_to_memory_quiz(response, request.user.id)
        
        # Check if message is question, and start the chat
        if message == "question":
            system_prompt = {
                "role": "system", 
                "content": prompt_text
            }
            
            # get the user prompt
            user_prompt = {"role": "user", "content": message}

            # Create a chat completion
            chat_completion = clientQuiz.chat.completions.create(
                model="gpt-4",
                messages=[system_prompt, user_prompt],
                max_tokens=250,
                top_p=0.9
            )
            # Get the response
            response = chat_completion.choices[0].message.content.strip()
            # Add new lines before a), b), c), and d)
            for option in ['a)', 'b)', 'c)', 'd)']:
                response = response.replace(option, '<br>' + option)
            # Add the response to the memory
            add_response_to_memory_quiz(response, request.user.id)
        
        return JsonResponse({'message': message, 'response': response})

    return render(request, 'app/chat_with_quiz.html', {'quiz': quiz})

#-Course section

# Initialize the OpenAI client for Course
clientCourse = OpenAI(api_key=settings.OPENAI_API_KEY_COURSE)

# course_view helps to view the course
def course_view(request, course_id):
    # Get the course object
    course = get_object_or_404(Course, pk=course_id)
    # Get the PDF files associated with the course
    pdf_files = course.pdfs.all()

    # Check if there are no PDF files
    if not pdf_files:
        return JsonResponse({"error": "No PDF files found for the course."}, status=404)

    # Extract text from the first PDF file
    try:
        # Extract text from the first PDF file
        pdfreader = PdfReader(pdf_files[0].file.path)
        # Get the raw text
        raw_text = ''.join(page.extract_text() or '' for page in pdfreader.pages)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # Split the text into chunks
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200)
    # Split the text
    chunks = text_splitter.split_text(raw_text)
    # Delete the first 10 chunks, which is the introduction of the pdf
    del chunks[:10]

    # Check if there are no chunks
    if not chunks:
        return JsonResponse({"error": "No text could be extracted from the PDF."}, status=404)

    # Check if the course_interaction is not in the request.session
    if 'course_interaction' not in request.session:
        request.session['course_interaction'] = {
            'current_chunk_index': 0,
            'total_chunks': len(chunks),
            'last_response': '',
            'detail_level': 1,
        }
    # Get the session data
    session_data = request.session['course_interaction']


    # Check if the request method is POST
    if request.method == 'POST':
        # Get the message from the request
        message = request.POST.get('message', '').strip().lower()
        # Get the current chunk index
        current_chunk_index = session_data.get('current_chunk_index', 0)
        # Get the current chunk
        current_chunk = chunks[current_chunk_index] if chunks else "No content available."

        # prompt_text helps to prompt the text
        prompt_text = f"You are a friendly student assistant which helps student out in their learning journey, answer the question based on the input of student: {message}\n\n an the text:{current_chunk}, EVERYTHING ELSE IS NOT ALLOWED."

        # Check if message is start, and prompt it
        if message == "start":
            # Reset the current chunk index
            session_data['current_chunk_index'] = 0
            # Reset the detail level
            session_data['detail_level'] = 1
            # Reset the last response
            session_data['last_response'] = ''
            # Modify the session
            request.session.modified = True
            # prompt_text helps to prompt the text
            prompt_text = f"Please summarize this content:\n\n{current_chunk}"
        # Check if message is next, and prompt it
        elif message == "next":
            # Check if the current chunk index is less than the total chunks
            if current_chunk_index < len(chunks) - 1:
                # Increment the current chunk index
                session_data['current_chunk_index'] += 1
                # Modify the session
                request.session.modified = True 
            # Get the current chunk
            current_chunk = chunks[session_data['current_chunk_index']]
            # prompt_text helps to prompt the text
            prompt_text = f"Please summarize this content:\n\n{current_chunk}"
        # Check if message is prev, and prompt it
        elif message == "prev":
            # Check if the current chunk index is greater than 0
            if current_chunk_index > 0:
                # Decrement the current chunk index
                session_data['current_chunk_index'] -= 1
                # Modify the session
                request.session.modified = True
            # Get the current chunk
            current_chunk = chunks[session_data['current_chunk_index']]
            # prompt_text helps to prompt the text
            prompt_text = f"Please summarize this content:\n\n{current_chunk}"
            
        # Check if message is detail, and prompt it
        system_prompt = {
            "role": "system", 
            "content": prompt_text
        }
        
        # get the user prompt
        user_prompt = {"role": "user", "content": message}

        # Create a chat completion
        chat_completion = clientCourse.chat.completions.create(
            model="gpt-4",
            messages=[system_prompt, user_prompt],
            max_tokens=1000,
            top_p=0.9
        )
        # Get the response
        response = chat_completion.choices[0].message.content.strip()
        
        # Add the message to the memory
        session_data['last_response'] = response
        request.session['course_interaction'] = session_data
        return JsonResponse({'message': message, 'response': response, 'current_chunk': current_chunk})

    return render(request, 'app/chat_with_course.html', {'course': course})

# Initialize the OpenAI client for Tutor
clientTutor = openai.OpenAI(api_key=settings.OPENAI_API_KEY_TUTOR)

# exam_view helps to view the exam
def exam_view(request, course_id):
    # Get the course object
    course = get_object_or_404(Course, pk=course_id)

    # Check if the request method is POST
    if request.method == 'POST':
        # Get the questions from the session
        questions = request.session.get(f'questions_{course_id}_{request.user.id}', [])
        # Check if there are no questions
        score = 0
        # Initialize the user answers
        user_answers = {}
        # Iterate over the questions
        for i, question in enumerate(questions, start=1):
            # Get the answer from the request
            answer = request.POST.get(f'question_{i}')
            # Check if the answer is not None
            if answer:
                # Add the answer to the user answers
                user_answers[str(question['session_id'])] = answer
                # Get the correct option
                correct_option = next((o for o in question['options'] if o['is_correct']), None)
                # Check if the correct option is not None and the correct option letter is equal to the answer
                if correct_option and correct_option['letter'] == answer:
                    # Increment the score
                    score += 1

        # Calculate the score
        score_record = Score.objects.create(user=request.user, course=course, value=score, answers=user_answers)
        
        # Store the questions in the session
        request.session[f'questions_{score_record.id}'] = questions

        return redirect('exam_results', score_id=score_record.id)

    # Get the PDF files associated with the course
    pdf_files = course.pdfs.all()

    # Check if there are no PDF files
    if not pdf_files:
        # Return the error message
        return JsonResponse({"error": "No PDF files found for the course."}, status=404)

    # Extract text from the first PDF file 
    try:
        # Extract text from the first PDF file
        pdfreader = PdfReader(pdf_files[0].file.path)
        # Get the raw text
        raw_text = ''.join(page.extract_text() or '' for page in pdfreader.pages)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # Split the text into chunks 
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200)
    # Split the text
    chunks = text_splitter.split_text(raw_text)
    # Check if there are no chunks
    if len(chunks) <= 10:
        return JsonResponse({"error": "Not enough text to generate questions from."}, status=404)

    # Select a random chunk
    selected_chunk = random.choice(chunks)

    # Prompt the user to generate questions
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

    # Create a system prompt
    system_prompt = {
        "role": "system",
        "content": prompt_text
    }

    # Create a chat completion
    messages = [system_prompt]
    try:
        # Create a chat completion
        chat_completion = clientTutor.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            max_tokens=2500,
            response_format={ "type": "json_object" }
        )

        # Get the questions from the chat completion
        questions = chat_completion.choices[0].message.content
        # Store the questions in the session as a JSON string
        questions = json.loads(questions)['questions']

        # Store the questions in the session
        session_questions = []
        # Iterate over the questions
        for idx, question in enumerate(questions):
            # Assign session_id for session storage
            question['session_id'] = idx + 1  
            # Append the question to the session questions
            session_questions.append(question)

        # Store the questions in the session
        request.session[f'questions_{course_id}_{request.user.id}'] = session_questions

        # Return the questions
        for question_data in session_questions:
            # Get the correct option
            correct_option = next(option for option in question_data['options'] if option['is_correct'])
            # generate the question
            question = Question.objects.create(
                course=course,
                text=question_data['text'],
                correct_option=correct_option['letter']
            )
            # Generate the options
            for option_data in question_data['options']:
                Option.objects.create(
                    question=question,
                    letter=option_data['letter'],
                    text=option_data['text'],
                    is_correct=option_data['is_correct']
                )
            # Return the questions
            question_data['id'] = question.id

        # Return the questions
        request.session[f'questions_{course_id}_{request.user.id}'] = session_questions

    except Exception as e:
        return render(request, 'app/exam_error.html', {'error_message': "Failed to generate questions: " + str(e), 'course': course})

    return render(request, 'app/chat_with_exam.html', {'course': course, 'questions': questions})

# exam_results helps to get the exam results
def exam_results(request, score_id):
    score = get_object_or_404(Score, pk=score_id)
    course = score.course

    # Retrieve questions using the unique session key with the score ID
    session_questions = request.session.get(f'questions_{score_id}', [])

    # Ensure questions are fetched correctly and do not mix with other exams
    questions = []
    for q in session_questions:
        question = Question.objects.get(id=q['id'])
        question.session_id = q['session_id']
        questions.append(question)

    # Get the options for the questions
    options = Option.objects.filter(question__in=questions)

    # context helps to get the context
    context = {
        'course': course,
        'score': score,
        'questions': questions,
        'user_answers': score.answers,
        'options': options
    }
    return render(request, 'app/exam_results.html', context)

# display_scores helps to display the scores
def display_scores(request, course_id):
    # Get the course object
    course = Course.objects.get(id=course_id)

    # Fetch the scores for the current user and course
    scores = Score.objects.filter(user=request.user, course=course)

    # Check if the student has any scores
    if not scores:
        level = 'To be determined'
        average = 'N/A'
    else:
        # Get the last 10 scores
        last_scores = scores.order_by('-id')[:10]

        # Create an average
        score_values = [score.value for score in last_scores]
        average = sum(score_values) / len(score_values) if score_values else 0
        average *= 10
        average = round(average, 2)

        # Determine the level based on the average
        if 0 <= average <= 74:
            level = 'Beginner'
        elif 75 <= average <= 89:
            level = 'Intermediate'
        elif 90 <= average <= 100:
            level = 'Advanced'

    # Render the scores page
    return render(request, 'app/exam_scores.html', {'course': course, 'scores': scores, 'level': level, 'average': average})