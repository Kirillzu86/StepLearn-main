from django.urls import path

from . import views

urlpatterns = [
    path('users', views.users, name='users'),
    path('users/', views.users, name='users-slash'),
    path('auth/register', views.register, name='register'),
    path('auth/register/', views.register, name='register-slash'),
    path('auth/login', views.login, name='login'),
    path('auth/login/', views.login, name='login-slash'),
    path('v1/enroll', views.enroll, name='enroll'),
    path('v1/enroll/', views.enroll, name='enroll-slash'),
    path('v1/courses', views.course_list, name='course-list'),
    path('v1/courses/', views.course_list, name='course-list-slash'),
    path('v1/courses/create', views.course_create, name='course-create'),
    path('v1/courses/create/', views.course_create, name='course-create-slash'),
    path('v1/course/<int:course_id>', views.course_detail, name='course-detail'),
    path('v1/course/<int:course_id>/', views.course_detail, name='course-detail-slash'),
    path('v1/courses/<int:course_id>', views.course_detail, name='courses-detail-plural'),
    path('v1/courses/<int:course_id>/', views.course_detail, name='courses-detail-plural-slash'),
    path('v1/users/<int:user_id>', views.user_detail, name='user-detail'),
    path('v1/users/<int:user_id>/', views.user_detail, name='user-detail-slash'),
    path('v1/users/<int:user_id>/courses', views.user_courses, name='user-courses'),
    path('v1/users/<int:user_id>/courses/', views.user_courses, name='user-courses-slash'),
    path('v1/users/<int:user_id>/courses/<int:course_id>/progress', views.course_progress, name='course-progress'),
    path('v1/users/<int:user_id>/courses/<int:course_id>/progress/', views.course_progress, name='course-progress-slash'),
]
