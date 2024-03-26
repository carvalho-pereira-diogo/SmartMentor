from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import *

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.stu_dashboard, name='student_dashboard'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    
    #Example for the values of database
    path('course/', CourseView.as_view(), name='course'),
    path('course/upload/', views.course_upload, name='course_upload'),
    path('courses/', course_list, name='course_list'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
