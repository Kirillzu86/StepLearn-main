from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Course, Enrollment, User
from .serializers import (
    CourseCreateSerializer,
    CourseSerializer,
    CourseWithQuestionsSerializer,
    EnrollmentProgressSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


def course_list_item(course, enrollment=None, *, enrolled=False):
    students_count = getattr(course, 'students_count', None)
    if students_count is None:
        students_count = course.enrollments.count()

    total_lessons = getattr(course, 'total_lessons', None)
    if total_lessons is None or total_lessons == 0:
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


@api_view(['GET'])
def users(request):
    qs = User.objects.all().order_by('id')
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
        total_lessons=Count('questions', distinct=True),
    ).order_by('id')

    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

    return Response([course_list_item(course, enrolled=False) for course in qs])


@api_view(['GET'])
def course_detail(request, course_id):
    try:
        course = Course.objects.prefetch_related('questions__answers').get(pk=course_id)
    except Course.DoesNotExist:
        return Response({'detail': 'Курс не найден'}, status=status.HTTP_404_NOT_FOUND)
    return Response(CourseWithQuestionsSerializer(course).data)


@api_view(['POST'])
def course_create(request):
    serializer = CourseCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    course = serializer.save()
    return Response(CourseSerializer(course).data, status=status.HTTP_200_OK)


@api_view(['POST'])
def enroll(request):
    user_id = request.data.get('user_id') or request.data.get('userId')
    course_id = request.data.get('course_id') or request.data.get('courseId')
    if not user_id or not course_id:
        return Response({'detail': 'user_id и course_id обязательны'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_id = int(user_id)
        course_id = int(course_id)
    except (ValueError, TypeError):
        return Response({'detail': 'Неверный формат идентификаторов'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            user = User.objects.get(pk=user_id)
            course = Course.objects.get(pk=course_id)
            enrollment, _ = Enrollment.objects.get_or_create(user=user, course=course)
    except User.DoesNotExist:
        return Response({'detail': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
    except Course.DoesNotExist:
        return Response({'detail': 'Курс не найден'}, status=status.HTTP_404_NOT_FOUND)
    except IntegrityError:
        return Response({'detail': 'Ошибка при записи на курс'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        .prefetch_related('course__questions', 'course__enrollments')
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
