from django.urls import path, include
from django.conf import settings
from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.conf.urls.static import static
from . import views
from .views import *

urlpatterns = [
    # Authentication section
    path('signup/', views.signup, name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('signin/', views.signin, name='signin'),
    path('', include('django.contrib.auth.urls')),
    path('logout/', LogoutOnGetView.as_view(), name='logout'),
    path('password_change/', PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),

    # Home section and dashboard
    path('', views.home, name='home'),
    path('student_dashboard/', views.stu_dashboard, name='student_dashboard'),
    path('teacher_dashboard/', views.te_dashboard, name='teacher_dashboard'),
    
    # Student and teacher profile
    path('student/profile', StudentProfileView.as_view(), name='student_profile'),
    path('teacher/profile', TeacherProfileView.as_view(), name='teacher_profile'),
    
    # Error section
    path('student/already_enrolled', AlreadyEnrolledView.as_view(), name='already_enrolled'),
    path('error', ErrorView.as_view(), name='error'),
    
    # Course section
    path('student/courses', StudentCourseView.as_view(), name='student_courses'),
    path('enroll_course/', EnrollCourseView.as_view(), name='enroll_course'),
    path('unenroll_course/<int:course_id>/', views.unenroll_course, name='unenroll_course'),
    path('teacher/courses', TeacherCourseView.as_view(), name='teacher_courses'),
    path('student/learningpath', StudentLearningPathView.as_view(), name='course_learningpath'),
    path('student/course/chat/<int:course_id>/', views.course_view, name='chat_with_course'),
    
    # Exam section for student
    path('student/exam', StudentExamView.as_view(), name='course_exam'),
    path('student/exam/<int:course_id>/', views.exam_view, name='chat_with_exam'),
    path('student/exam/scores/<int:course_id>/', views.display_scores, name='exam_scores'),
    path('student/exam/results/<int:score_id>/', views.exam_results, name='exam_results'),
    
    # Course section for teacher
    path('teacher/course/create/', TeacherCourseView.as_view(), name='course_create'),
    path('teacher/courses/delete/<int:course_id>/', views.delete_course, name='course_delete'),

    # PDF section for teacher
    path('teacher/pdfs/delete/<int:pdf_id>/', views.delete_pdf, name='delete_pdf'),
    path('teacher/pdfs/', TeacherPDFView.as_view(), name='teacher_pdfs'),
    
    # Quiz section for student
    path('student/quiz', StudentQuizView.as_view(), name='student_quiz'),
    path('student/quiz/<int:quiz_id>/', views.quiz_view, name='chat_with_quiz'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
