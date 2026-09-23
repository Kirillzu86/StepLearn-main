from django.urls import path

from . import views

urlpatterns = [
    # Auth & Users
    path('users', views.users, name='users'),
    path('users/', views.users, name='users-slash'),
    path('auth/register', views.register, name='register'),
    path('auth/register/', views.register, name='register-slash'),
    path('auth/login', views.login, name='login'),
    path('auth/login/', views.login, name='login-slash'),
    path('v1/users/<int:user_id>', views.user_detail, name='user-detail'),
    path('v1/users/<int:user_id>/', views.user_detail, name='user-detail-slash'),
    path('v1/users/<int:user_id>/courses', views.user_courses, name='user-courses'),
    path('v1/users/<int:user_id>/courses/', views.user_courses, name='user-courses-slash'),
    path('v1/users/<int:user_id>/courses/<int:course_id>/progress', views.course_progress, name='course-progress'),
    path('v1/users/<int:user_id>/courses/<int:course_id>/progress/', views.course_progress, name='course-progress-slash'),

    # Courses & Enroll
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

    # Lessons
    path('v1/courses/<int:course_id>/lessons', views.course_lessons_create, name='course-lessons-create'),
    path('v1/courses/<int:course_id>/lessons/', views.course_lessons_create, name='course-lessons-create-slash'),
    path('v1/lessons/<int:lesson_id>', views.lesson_detail, name='lesson-detail'),
    path('v1/lessons/<int:lesson_id>/', views.lesson_detail, name='lesson-detail-slash'),
    path('v1/lessons/<int:lesson_id>/complete', views.complete_lesson, name='lesson-complete'),
    path('v1/lessons/<int:lesson_id>/complete/', views.complete_lesson, name='lesson-complete-slash'),

    # Groups & Stepik/Cisco Gating
    path('v1/groups', views.groups_list, name='groups-list'),
    path('v1/groups/', views.groups_list, name='groups-list-slash'),
    path('v1/groups/join', views.group_join_by_code, name='group-join'),
    path('v1/groups/join/', views.group_join_by_code, name='group-join-slash'),
    path('v1/groups/<int:group_id>', views.group_detail, name='group-detail'),
    path('v1/groups/<int:group_id>/', views.group_detail, name='group-detail-slash'),
    path('v1/groups/<int:group_id>/add-student', views.group_add_student, name='group-add-student'),
    path('v1/groups/<int:group_id>/add-student/', views.group_add_student, name='group-add-student-slash'),
    path('v1/groups/<int:group_id>/remove-student/<int:student_id>', views.group_remove_student, name='group-remove-student'),
    path('v1/groups/<int:group_id>/remove-student/<int:student_id>/', views.group_remove_student, name='group-remove-student-slash'),
    path('v1/groups/<int:group_id>/assign-course', views.group_assign_course, name='group-assign-course'),
    path('v1/groups/<int:group_id>/assign-course/', views.group_assign_course, name='group-assign-course-slash'),
    path('v1/groups/<int:group_id>/progress/<int:course_id>', views.group_progress_matrix, name='group-progress-matrix'),
    path('v1/groups/<int:group_id>/progress/<int:course_id>/', views.group_progress_matrix, name='group-progress-matrix-slash'),
    path('v1/groups/<int:group_id>/lessons/<int:lesson_id>/toggle-access', views.group_toggle_lesson_access, name='group-toggle-lesson-access'),
    path('v1/groups/<int:group_id>/lessons/<int:lesson_id>/toggle-access/', views.group_toggle_lesson_access, name='group-toggle-lesson-access-slash'),
]
