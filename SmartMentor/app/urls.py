from django.urls import path, include
from django.conf import settings
from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.conf.urls.static import static
from . import views
from .views import *

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('signin/', views.signin, name='signin'),
    path('', include('django.contrib.auth.urls')),
    path('logout/', LogoutOnGetView.as_view(), name='logout'),
    path('password_change/', PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),

    path('', views.home, name='home'),
    path('student_dashboard/', views.stu_dashboard, name='student_dashboard'),
    path('teacher_dashboard/', views.te_dashboard, name='teacher_dashboard'),
    
    #Example for the values of database
    path('student/course', StudentCourseView.as_view(), name='student_course'),
    path('teacher/courses', TeacherCourseView.as_view(), name='teacher_courses'),
    # Create course for teacher
    path('teacher/course/create/', TeacherCourseView.as_view(), name='teacher_course_create'),
    
    path('teacher/pdfs/delete/<int:pdf_id>/', delete_pdf, name='delete_pdf'),
    
    path('teacher/pdfs/', TeacherPDFView.as_view(), name='teacher_pdfs'),
    
    path('teacher/course/create/', TeacherCourseView.as_view(), name='teacher_course_create'),
    path('student/enroll/<int:course_id>/', enroll_in_course, name='enroll_in_course'),
    
    path('student/profile', StudentProfileView.as_view(), name='student_profile'),
    path('teacher/profile', TeacherProfileView.as_view(), name='teacher_profile'),
    
    path('student/quiz', StudentQuizView.as_view(), name='student_quiz'),
    path('teacher/quiz', TeacherQuizView.as_view(), name='teacher_quiz'),
    
    path('student/ai_tutor', StudentTutorView.as_view(), name='student_ai_tutor'),
    path('teacher/ai_tutor', TeacherTutorView.as_view(), name='teacher_ai_tutor'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
