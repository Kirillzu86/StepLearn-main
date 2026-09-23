import uuid
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    Answer,
    Course,
    Enrollment,
    GroupCourse,
    GroupLessonAccess,
    Lesson,
    Question,
    StudentLessonProgress,
    StudyGroup,
    User,
)
from .serializers import (
    CourseCreateSerializer,
    CourseSerializer,
    CourseWithQuestionsSerializer,
    GroupLessonAccessSerializer,
    LessonSerializer,
    LoginSerializer,
    RegisterSerializer,
    StudyGroupSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


def course_list_item(course, enrollment=None, *, enrolled=False):
    students_count = getattr(course, 'students_count', None)
    if students_count is None:
        students_count = course.enrollments.count()

    total_lessons = getattr(course, 'total_lessons', None)
    if total_lessons is None or total_lessons == 0:
        lessons_count = course.lessons.count()
        if lessons_count > 0:
            total_lessons = lessons_count
        else:
            total_questions = course.questions.count()
            if total_questions > 0:
                total_lessons = total_questions
            elif course.content:
                import re
                sections = len(re.findall(r'^#{1,3}\s+', course.content, re.MULTILINE))
                total_lessons = max(1, sections)
            else:
                total_lessons = 0

    is_enrolled = enrolled or (enrollment is not None)
    if is_enrolled:
        price_status = 'Enrolled'
    elif course.price and course.price > 0:
        price_status = 'Paid'
    else:
        price_status = 'Free'

    completed_lessons = enrollment.completed_lessons if enrollment else 0
    progress_percentage = enrollment.progress_percentage if enrollment else 0

    return {
        'id': course.id,
        'title': course.title,
        'description': course.description or '',
        'price': course.price,
        'rating': getattr(course, 'rating', 4.5) or 4.5,
        'course_type': getattr(course, 'course_type', 'quiz'),
        'has_content': bool(course.content),
        'students_count': students_count,
        'price_status': price_status,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'progress_percentage': progress_percentage,
    }


# ==========================================
# 1. ПОЛЬЗОВАТЕЛИ И АУТЕНТИФИКАЦИЯ
# ==========================================

@api_view(['GET'])
def users(request):
    qs = User.objects.all().order_by('id')
    role_filter = request.query_params.get('role')
    if role_filter:
        qs = qs.filter(role=role_filter)
    return Response(UserSerializer(qs, many=True).data)


@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


@api_view(['POST'])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(UserSerializer(serializer.validated_data['user']).data)


@api_view(['GET', 'PUT', 'PATCH'])
def user_detail(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(UserSerializer(user).data)

    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(UserSerializer(user).data)


# ==========================================
# 2. КУРСЫ И УРОКИ
# ==========================================

@api_view(['GET', 'POST'])
def course_list(request):
    if request.method == 'POST':
        serializer = CourseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.save()
        return Response(CourseSerializer(course).data, status=status.HTTP_200_OK)

    query = (request.query_params.get('q') or '').strip()
    qs = Course.objects.annotate(
        students_count=Count('enrollments', distinct=True),
        total_lessons=Count('lessons', distinct=True),
    ).order_by('id')

    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

    return Response([course_list_item(course, enrolled=False) for course in qs])


@api_view(['GET'])
def course_detail(request, course_id):
    try:
        course = Course.objects.prefetch_related('questions__answers', 'lessons__questions__answers').get(pk=course_id)
    except Course.DoesNotExist:
        return Response({'detail': 'Курс не найден'}, status=status.HTTP_404_NOT_FOUND)

    user_id = request.query_params.get('user_id') or request.query_params.get('userId')
    current_user = None
    if user_id:
        try:
            current_user = User.objects.get(pk=int(user_id))
        except (User.DoesNotExist, ValueError):
            pass

    data = CourseWithQuestionsSerializer(course).data

    # Находим группу пользователя для этого курса
    user_group = None
    if current_user:
        user_group = StudyGroup.objects.filter(
            students=current_user,
            group_courses__course=course,
        ).first()

    # Формируем список уроков со статусом блокировки (Stepik / Cisco gating)
    lessons_data = []
    lessons = list(course.lessons.all().order_by('order', 'id'))

    for idx, lesson in enumerate(lessons):
        lesson_dict = LessonSerializer(lesson).data
        is_locked = False
        lock_reason = None
        group_progress_info = None

        if user_group:
            access = GroupLessonAccess.objects.filter(group=user_group, lesson=lesson).first()
            if access:
                is_locked = not access.is_unlocked
                if is_locked:
                    lock_reason = 'Преподаватель еще не открыл доступ к этому модулю для вашей группы.'
                    # Проверяем прогресс по предыдущему модулю
                    if idx > 0:
                        prev_lesson = lessons[idx - 1]
                        total_group_students = user_group.students.count()
                        passed_count = StudentLessonProgress.objects.filter(
                            user__in=user_group.students.all(),
                            lesson=prev_lesson,
                            is_completed=True,
                        ).count()
                        group_progress_info = {
                            'prev_lesson_title': prev_lesson.title,
                            'passed_students': passed_count,
                            'total_students': total_group_students,
                            'completion_percentage': round((passed_count / max(1, total_group_students)) * 100),
                        }
            elif idx > 0:
                is_locked = True
                lock_reason = 'Модуль ожидает открытия преподавателем.'

            # Прогресс текущего студента по этому уроку
            user_prog = StudentLessonProgress.objects.filter(user=current_user, lesson=lesson).first()
            lesson_dict['is_completed'] = user_prog.is_completed if user_prog else False
        else:
            # Для независимых студентов — все уроки доступны
            if current_user:
                user_prog = StudentLessonProgress.objects.filter(user=current_user, lesson=lesson).first()
                lesson_dict['is_completed'] = user_prog.is_completed if user_prog else False
            else:
                lesson_dict['is_completed'] = False

        lesson_dict['is_locked'] = is_locked
        lesson_dict['lock_reason'] = lock_reason
        lesson_dict['group_progress_info'] = group_progress_info
        lessons_data.append(lesson_dict)

    data['lessons'] = lessons_data
    data['group_info'] = {'id': user_group.id, 'name': user_group.name} if user_group else None
    return Response(data)


@api_view(['POST'])
def course_create(request):
    serializer = CourseCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    course = serializer.save()
    return Response(CourseSerializer(course).data, status=status.HTTP_200_OK)


@api_view(['POST'])
def course_lessons_create(request, course_id):
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return Response({'detail': 'Курс не найден'}, status=status.HTTP_404_NOT_FOUND)

    title = request.data.get('title', '').strip()
    if not title:
        return Response({'detail': 'Название урока обязательно'}, status=status.HTTP_400_BAD_REQUEST)

    description = request.data.get('description', '')
    content = request.data.get('content', '')
    order = request.data.get('order')

    if order is None:
        last_lesson = course.lessons.order_by('-order').first()
        order = (last_lesson.order + 1) if last_lesson else 1
    else:
        order = int(order)

    lesson = Lesson.objects.create(
        course=course,
        title=title,
        description=description,
        content=content,
        order=order,
    )

    # Если курс уже назначен группам, создаем записи доступа
    for gc in course.group_courses.all():
        is_first = (order == 1)
        GroupLessonAccess.objects.get_or_create(
            group=gc.group,
            lesson=lesson,
            defaults={'is_unlocked': is_first, 'auto_unlock_when_all_pass': True},
        )

    return Response(LessonSerializer(lesson).data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH', 'DELETE'])
def lesson_detail(request, lesson_id):
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
    except Lesson.DoesNotExist:
        return Response({'detail': 'Урок не найден'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        lesson.delete()
        return Response({'status': 'deleted'})

    title = request.data.get('title')
    if title:
        lesson.title = title.strip()
    if 'description' in request.data:
        lesson.description = request.data['description']
    if 'content' in request.data:
        lesson.content = request.data['content']
    if 'order' in request.data:
        lesson.order = int(request.data['order'])
    lesson.save()

    return Response(LessonSerializer(lesson).data)


@api_view(['POST'])
def complete_lesson(request, lesson_id):
    try:
        lesson = Lesson.objects.select_related('course').get(pk=lesson_id)
    except Lesson.DoesNotExist:
        return Response({'detail': 'Урок не найден'}, status=status.HTTP_404_NOT_FOUND)

    user_id = request.data.get('user_id') or request.data.get('userId')
    if not user_id:
        return Response({'detail': 'user_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(pk=int(user_id))
    except User.DoesNotExist:
        return Response({'detail': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

    # Фиксируем завершение урока студентом
    progress, _ = StudentLessonProgress.objects.get_or_create(user=user, lesson=lesson)
    progress.is_completed = True
    progress.completed_at = timezone.now()
    progress.save()

    # Обновляем общий прогресс курса в Enrollment
    enrollment, _ = Enrollment.objects.get_or_create(user=user, course=lesson.course)
    total_lessons = lesson.course.lessons.count() or 1
    completed_count = StudentLessonProgress.objects.filter(
        user=user,
        lesson__course=lesson.course,
        is_completed=True,
    ).count()

    enrollment.completed_lessons = completed_count
    enrollment.progress_percentage = min(100, int((completed_count / total_lessons) * 100))
    enrollment.save()

    # Авто-открытие следующего урока для группы (логика Stepik / Cisco)
    unlocked_next = False
    next_lesson_info = None

    # Проверяем все группы, в которых состоит студент и к которым привязан курс
    user_groups = StudyGroup.objects.filter(students=user, group_courses__course=lesson.course)
    for group in user_groups:
        total_students = group.students.count()
        if total_students == 0:
            continue

        # Сколько студентов в группе завершили этот урок?
        group_completed_count = StudentLessonProgress.objects.filter(
            user__in=group.students.all(),
            lesson=lesson,
            is_completed=True,
        ).count()

        # Если 100% группы сдали материал
        if group_completed_count >= total_students:
            # Ищем следующий урок
            next_lesson = Lesson.objects.filter(
                course=lesson.course,
                order__gt=lesson.order,
            ).order_by('order').first()

            if next_lesson:
                next_access, _ = GroupLessonAccess.objects.get_or_create(
                    group=group,
                    lesson=next_lesson,
                    defaults={'is_unlocked': False, 'auto_unlock_when_all_pass': True},
                )
                if next_access.auto_unlock_when_all_pass and not next_access.is_unlocked:
                    next_access.is_unlocked = True
                    next_access.unlocked_at = timezone.now()
                    next_access.save()
                    unlocked_next = True
                    next_lesson_info = {
                        'id': next_lesson.id,
                        'title': next_lesson.title,
                        'group_name': group.name,
                    }

    return Response({
        'status': 'ok',
        'is_completed': True,
        'unlocked_next': unlocked_next,
        'next_lesson': next_lesson_info,
        'completed_lessons': enrollment.completed_lessons,
        'progress_percentage': enrollment.progress_percentage,
    })


# ==========================================
# 3. СИСТЕМА ГРУПП (STUDY GROUPS & CISCO/STEPIK GATING)
# ==========================================

@api_view(['GET', 'POST'])
def groups_list(request):
    if request.method == 'POST':
        name = request.data.get('name', '').strip()
        if not name:
            return Response({'detail': 'Название группы обязательно'}, status=status.HTTP_400_BAD_REQUEST)

        description = request.data.get('description', '')
        teacher_id = request.data.get('teacher_id') or request.data.get('teacherId')
        teacher = None
        if teacher_id:
            teacher = User.objects.filter(pk=int(teacher_id)).first()
        if not teacher:
            teacher = User.objects.filter(is_superuser=True).first() or User.objects.first()

        code = StudyGroup.generate_code()
        group = StudyGroup.objects.create(
            name=name,
            description=description,
            code=code,
            teacher=teacher,
        )
        return Response(StudyGroupSerializer(group).data, status=status.HTTP_201_CREATED)

    # GET
    teacher_id = request.query_params.get('teacher_id')
    user_id = request.query_params.get('user_id')

    qs = StudyGroup.objects.select_related('teacher').prefetch_related('students', 'group_courses__course').all()
    if teacher_id:
        qs = qs.filter(teacher_id=teacher_id)
    elif user_id:
        qs = qs.filter(Q(teacher_id=user_id) | Q(students__id=user_id)).distinct()

    return Response(StudyGroupSerializer(qs, many=True).data)


@api_view(['GET', 'DELETE'])
def group_detail(request, group_id):
    try:
        group = StudyGroup.objects.select_related('teacher').prefetch_related('students', 'group_courses__course').get(pk=group_id)
    except StudyGroup.DoesNotExist:
        return Response({'detail': 'Группа не найдена'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        group.delete()
        return Response({'status': 'deleted'})

    return Response(StudyGroupSerializer(group).data)


@api_view(['POST'])
def group_add_student(request, group_id):
    try:
        group = StudyGroup.objects.get(pk=group_id)
    except StudyGroup.DoesNotExist:
        return Response({'detail': 'Группа не найдена'}, status=status.HTTP_404_NOT_FOUND)

    student_id = request.data.get('student_id') or request.data.get('userId')
    username = request.data.get('username')

    student = None
    if student_id:
        student = User.objects.filter(pk=int(student_id)).first()
    elif username:
        student = User.objects.filter(username__iexact=username.strip()).first()

    if not student:
        return Response({'detail': 'Студент не найден'}, status=status.HTTP_404_NOT_FOUND)

    group.students.add(student)

    # Автоматически записываем студента на все назначенные группе курсы
    for gc in group.group_courses.all():
        Enrollment.objects.get_or_create(user=student, course=gc.course)

    return Response(StudyGroupSerializer(group).data)


@api_view(['POST'])
def group_remove_student(request, group_id, student_id):
    try:
        group = StudyGroup.objects.get(pk=group_id)
        student = User.objects.get(pk=student_id)
    except (StudyGroup.DoesNotExist, User.DoesNotExist):
        return Response({'detail': 'Группа или студент не найдены'}, status=status.HTTP_404_NOT_FOUND)

    group.students.remove(student)
    return Response(StudyGroupSerializer(group).data)


@api_view(['POST'])
def group_join_by_code(request):
    code = (request.data.get('code') or '').strip().upper()
    user_id = request.data.get('user_id') or request.data.get('userId')

    if not code or not user_id:
        return Response({'detail': 'Код и идентификатор пользователя обязательны'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(pk=int(user_id))
    except User.DoesNotExist:
        return Response({'detail': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

    group = StudyGroup.objects.filter(code__iexact=code).first()
    if not group:
        return Response({'detail': 'Группа с таким кодом не найдена'}, status=status.HTTP_404_NOT_FOUND)

    group.students.add(user)

    for gc in group.group_courses.all():
        Enrollment.objects.get_or_create(user=user, course=gc.course)

    return Response({
        'status': 'joined',
        'group': StudyGroupSerializer(group).data,
    })


@api_view(['POST'])
def group_assign_course(request, group_id):
    try:
        group = StudyGroup.objects.prefetch_related('students').get(pk=group_id)
    except StudyGroup.DoesNotExist:
        return Response({'detail': 'Группа не найдена'}, status=status.HTTP_404_NOT_FOUND)

    course_id = request.data.get('course_id') or request.data.get('courseId')
    if not course_id:
        return Response({'detail': 'course_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        course = Course.objects.prefetch_related('lessons').get(pk=int(course_id))
    except Course.DoesNotExist:
        return Response({'detail': 'Курс не найден'}, status=status.HTTP_404_NOT_FOUND)

    group_course, _ = GroupCourse.objects.get_or_create(group=group, course=course)

    # Записываем всех студентов группы на курс
    for student in group.students.all():
        Enrollment.objects.get_or_create(user=student, course=course)

    # Создаем правила доступа к урокам для группы:
    # 1-й урок открываем сразу, остальные закрыты (Stepik/Cisco модель)
    lessons = list(course.lessons.all().order_by('order', 'id'))
    for idx, lesson in enumerate(lessons):
        is_first = (idx == 0)
        GroupLessonAccess.objects.get_or_create(
            group=group,
            lesson=lesson,
            defaults={
                'is_unlocked': is_first,
                'unlocked_at': timezone.now() if is_first else None,
                'auto_unlock_when_all_pass': True,
            },
        )

    return Response({
        'status': 'assigned',
        'group_id': group.id,
        'course_id': course.id,
        'lessons_count': len(lessons),
    })


@api_view(['GET'])
def group_progress_matrix(request, group_id, course_id):
    """
    Возвращает для преподавателя полную матрицу успеваемости группы:
    - список уроков с флагами доступа
    - процент сдачи каждым студентом
    - процент готовности группы к открытию следующего модуля
    """
    try:
        group = StudyGroup.objects.prefetch_related('students').get(pk=group_id)
        course = Course.objects.prefetch_related('lessons').get(pk=course_id)
    except (StudyGroup.DoesNotExist, Course.DoesNotExist):
        return Response({'detail': 'Группа или курс не найдены'}, status=status.HTTP_404_NOT_FOUND)

    students = list(group.students.all().order_by('id'))
    total_students = len(students)
    lessons = list(course.lessons.all().order_by('order', 'id'))

    accesses = {
        gla.lesson_id: gla
        for gla in GroupLessonAccess.objects.filter(group=group, lesson__in=lessons)
    }

    progress_records = StudentLessonProgress.objects.filter(
        user__in=students,
        lesson__in=lessons,
        is_completed=True,
    ).values_list('user_id', 'lesson_id')

    completed_set = set(progress_records)

    lessons_stats = []
    for idx, lesson in enumerate(lessons):
        access = accesses.get(lesson.id)
        is_unlocked = access.is_unlocked if access else (idx == 0)
        auto_unlock = access.auto_unlock_when_all_pass if access else True

        completed_count = sum(1 for s in students if (s.id, lesson.id) in completed_set)
        completion_rate = round((completed_count / max(1, total_students)) * 100) if total_students > 0 else 0
        all_passed = (completed_count >= total_students) and (total_students > 0)

        lessons_stats.append({
            'lesson_id': lesson.id,
            'title': lesson.title,
            'order': lesson.order,
            'is_unlocked': is_unlocked,
            'auto_unlock_when_all_pass': auto_unlock,
            'completed_students_count': completed_count,
            'total_students_count': total_students,
            'completion_rate': completion_rate,
            'all_passed': all_passed,
        })

    # Матрица студентов
    students_matrix = []
    for s in students:
        s_lessons_progress = {}
        s_completed_count = 0
        for l in lessons:
            done = (s.id, l.id) in completed_set
            s_lessons_progress[l.id] = done
            if done:
                s_completed_count += 1

        overall_pct = round((s_completed_count / max(1, len(lessons))) * 100) if lessons else 0
        students_matrix.append({
            'id': s.id,
            'username': s.username,
            'name': s.name,
            'avatar_url': s.avatar_url,
            'lessons': s_lessons_progress,
            'completed_lessons_count': s_completed_count,
            'overall_progress': overall_pct,
        })

    return Response({
        'group': {'id': group.id, 'name': group.name, 'code': group.code},
        'course': {'id': course.id, 'title': course.title},
        'total_students': total_students,
        'lessons': lessons_stats,
        'students': students_matrix,
    })


@api_view(['POST'])
def group_toggle_lesson_access(request, group_id, lesson_id):
    """
    Преподаватель принудительно открывает или закрывает урок для группы
    (или переключает флаг автоматического открытия).
    """
    try:
        group = StudyGroup.objects.get(pk=group_id)
        lesson = Lesson.objects.get(pk=lesson_id)
    except (StudyGroup.DoesNotExist, Lesson.DoesNotExist):
        return Response({'detail': 'Группа или урок не найдены'}, status=status.HTTP_404_NOT_FOUND)

    access, _ = GroupLessonAccess.objects.get_or_create(group=group, lesson=lesson)

    if 'is_unlocked' in request.data:
        access.is_unlocked = bool(request.data['is_unlocked'])
        if access.is_unlocked:
            access.unlocked_at = timezone.now()
    else:
        # Toggle
        access.is_unlocked = not access.is_unlocked
        if access.is_unlocked:
            access.unlocked_at = timezone.now()

    if 'auto_unlock_when_all_pass' in request.data:
        access.auto_unlock_when_all_pass = bool(request.data['auto_unlock_when_all_pass'])

    access.save()
    return Response({
        'status': 'updated',
        'access': GroupLessonAccessSerializer(access).data,
    })


# ==========================================
# 4. ОБЩИЕ ЭНДПОИНТЫ ЗАПИСИ И ПРОГРЕССА
# ==========================================

@api_view(['POST'])
def enroll(request):
    user_id = request.data.get('user_id') or request.data.get('userId')
    course_id = request.data.get('course_id') or request.data.get('courseId')
    if not user_id or not course_id:
        return Response({'detail': 'user_id и course_id обязательны'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(pk=int(user_id))
        course = Course.objects.get(pk=int(course_id))
        enrollment, _ = Enrollment.objects.get_or_create(user=user, course=course)
    except User.DoesNotExist:
        return Response({'detail': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
    except Course.DoesNotExist:
        return Response({'detail': 'Курс не найден'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'message': 'Enrolled successfully', 'enrolled': True})


@api_view(['GET'])
def user_courses(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response([])

    enrollments = (
        Enrollment.objects.filter(user=user)
        .select_related('course')
        .prefetch_related('course__questions', 'course__lessons', 'course__enrollments')
        .order_by('id')
    )
    return Response([course_list_item(en.course, enrollment=en, enrolled=True) for en in enrollments])


@api_view(['GET', 'POST'])
def course_progress(request, user_id, course_id):
    user = User.objects.filter(pk=user_id).first()
    course = Course.objects.filter(pk=course_id).first()

    if request.method == 'GET':
        if not user or not course:
            return Response({
                'enrolled': False,
                'current_index': 0,
                'progress_percentage': 0,
                'completed_lessons': 0,
                'correct_answers': 0,
            })
        enrollment = Enrollment.objects.filter(user=user, course=course).first()
        if not enrollment:
            return Response({
                'enrolled': False,
                'current_index': 0,
                'progress_percentage': 0,
                'completed_lessons': 0,
                'correct_answers': 0,
            })
        return Response({
            'enrolled': True,
            'current_index': enrollment.current_index,
            'progress_percentage': enrollment.progress_percentage,
            'completed_lessons': enrollment.completed_lessons,
            'correct_answers': enrollment.correct_answers,
        })

    if not user:
        return Response({'detail': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
    if not course:
        return Response({'detail': 'Курс не найден'}, status=status.HTTP_404_NOT_FOUND)

    enrollment, _ = Enrollment.objects.get_or_create(user=user, course=course)

    current_index = request.data.get('currentIndex')
    if current_index is None:
        current_index = request.data.get('current_index')

    progress_percentage = request.data.get('progress_percentage')
    if progress_percentage is None:
        progress_percentage = request.data.get('progressPercentage')

    correct_answers = request.data.get('correctAnswers')
    if correct_answers is None:
        correct_answers = request.data.get('correct_answers')

    completed_lessons = request.data.get('completed_lessons')
    if completed_lessons is None:
        completed_lessons = request.data.get('completedLessons')
    if completed_lessons is None and current_index is not None:
        completed_lessons = current_index

    if current_index is not None:
        enrollment.current_index = max(0, int(current_index))
    if progress_percentage is not None:
        enrollment.progress_percentage = min(100, max(0, int(progress_percentage)))
    if completed_lessons is not None:
        enrollment.completed_lessons = max(0, int(completed_lessons))
    if correct_answers is not None:
        enrollment.correct_answers = max(0, int(correct_answers))

    enrollment.save()

    return Response({
        'status': 'ok',
        'current_index': enrollment.current_index,
        'progress_percentage': enrollment.progress_percentage,
        'completed_lessons': enrollment.completed_lessons,
        'correct_answers': enrollment.correct_answers,
    })
