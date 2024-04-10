from django import forms
from .models import *
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'
        
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'
        
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description', 'pdfs']
        
from django import forms
from .models import Quiz, QuizEnrollment, QuizScore, Tutor

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['course', 'name']

class QuizEnrollmentForm(forms.ModelForm):
    class Meta:
        model = QuizEnrollment
        fields = ['student', 'quiz']

class QuizScoreForm(forms.ModelForm):
    class Meta:
        model = QuizScore
        fields = ['student', 'quiz', 'score']
# Replace with the actual fields of the Tutor model
        
class LearningPathForm(forms.ModelForm):
    class Meta:
        model = LearningPath
        fields = '__all__'
        
        
class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = '__all__'
        
class TutorForm(forms.ModelForm):
    class Meta:
        model = Tutor
        fields = '__all__'
        
# In forms.py
class UploadFileForm(forms.ModelForm):
    class Meta:
        model = PDF
        fields = ['file']
        
class PDFUploadForm(forms.ModelForm):
    class Meta:
        model = PDF
        fields = ['file']
