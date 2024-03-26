from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from .models import *



# Create your views here.
def home(request):
    return render(request, 'app/home.html')

def dashboard(request):
    return render(request, 'app/dashboard.html')

def student(request):
    return render(request, 'app/studentProfile.html')

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
            return redirect('signin')
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
            return redirect("signin")  # Ensure "signin" is the name of the URL pattern for your sign-in page.
        
    else:
        # For a GET request, just display the sign-in form.
        return render(request, 'app/signin.html')
    
def signout(request):
    logout(request)
    return redirect('home')
