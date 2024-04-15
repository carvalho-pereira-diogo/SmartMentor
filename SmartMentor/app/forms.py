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

from django import forms
from .models import Quiz, Course, PDF

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['name', 'description', 'course', 'pdfs']  # Assuming these fields exist

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(QuizForm, self).__init__(*args, **kwargs)
        if user is not None:
            # Filter course field based on user's teacher role
            self.fields['course'].queryset = Course.objects.filter(teacher=user.teacher)

from django import forms
from .models import Quiz

# Assuming 'course' and potentially 'pdfs' are fields managed by the form
class SimpleQuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['name', 'description', 'course', 'pdfs']  # Assuming these are the fields

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'teacher'):
            self.fields['course'].queryset = Course.objects.filter(teacher=user.teacher)


class QuizEnrollmentForm(forms.ModelForm):
    quiz = forms.ModelChoiceField(queryset=Quiz.objects.none())  # Initially no quizzes

    class Meta:
        model = QuizEnrollment
        fields = ['quiz']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated and hasattr(user, 'teacher'):
            teacher_courses = Course.objects.filter(teacher=user.teacher)  # Get the teacher's courses
            all_quizzes = Quiz.objects.filter(course__in=teacher_courses)  # Get quizzes associated with the teacher's courses
            self.fields['quiz'].queryset = all_quizzes

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
        
class SimpleTutorForm(forms.ModelForm):
    #do it like SimleQuizForm
    class Meta:
        model = Tutor
        fields = ['name', 'course']
        
class TutorForm(forms.ModelForm):
    
    class Meta:
        model = Tutor
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TutorForm, self).__init__(*args, **kwargs)
        if user is not None:
            self.fields['course'].queryset = Course.objects.filter(teacher=user.teacher)

class TutorEnrollmentForm(forms.ModelForm):
    class Meta:
        model = TutorEnrollment
        fields = ['tutor']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated and hasattr(user, 'teacher'):
            teacher_tutors = Tutor.objects.filter(teacher=user.teacher)
            self.fields['tutor'].queryset = teacher_tutors

# In forms.py
class UploadFileForm(forms.ModelForm):
    class Meta:
        model = PDF
        fields = ['file']
        
class PDFUploadForm(forms.ModelForm):
    class Meta:
        model = PDF
        fields = ['file']
