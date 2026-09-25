# AI-GENERATED: Antigravity
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import (
    Answer,
    Course,
    CourseBlock,
    Enrollment,
    Exam,
    ExamAttempt,
    GroupCourse,
    GroupLessonAccess,
    Lesson,
    Question,
    StudentLessonProgress,
    StudyGroup,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Создаёт демонстрационные данные StepLearn по плану (курсы Python, блоки, Markdown-уроки, экзамены, группы)'

    def handle(self, *args, **options):
        self.stdout.write('Запуск сидера StepLearn...')

        # 1. Администратор и Преподаватель
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@steplearn.local',
                'first_name': 'Администратор',
                'last_name': 'Системы',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        admin.set_password('admin123')
        admin.role = 'admin'
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        teacher, _ = User.objects.get_or_create(
            username='teacher',
            defaults={
                'email': 'teacher@steplearn.local',
                'first_name': 'Иван',
                'last_name': 'Петров',
                'role': 'teacher',
                'is_staff': True,
            },
        )
        teacher.set_password('teacher123')
        teacher.role = 'teacher'
        teacher.is_staff = True
        teacher.save()

        # 2. Основной студент (Магамет Дзангиев из примера в ТЗ)
        student, _ = User.objects.get_or_create(
            username='student',
            defaults={
                'email': 'student@steplearn.local',
                'first_name': 'Магамет',
                'last_name': 'Дзангиев',
                'role': 'student',
            },
        )
        student.set_password('student123')
        student.first_name = 'Магамет'
        student.last_name = 'Дзангиев'
        student.role = 'student'
        student.save()

        # Дополнительные студенты для группы (Ахмад, Али, Расул, Иса)
        extra_students = [
            ('student_ahmad', 'Ахмад', 'Алиев'),
            ('student_ali', 'Али', 'Магомедов'),
            ('student_rasul', 'Расул', 'Ибрагимов'),
            ('student_isa', 'Иса', 'Умаров'),
        ]
        group_students = [student]
        for uname, fname, lname in extra_students:
            s, _ = User.objects.get_or_create(
                username=uname,
                defaults={
                    'email': f'{uname}@steplearn.local',
                    'first_name': fname,
                    'last_name': lname,
                    'role': 'student',
                }
            )
            s.set_password('secret123')
            s.first_name = fname
            s.last_name = lname
            s.role = 'student'
            s.save()
            group_students.append(s)

        # 3. Учебная группа (Python-01)
        group, _ = StudyGroup.objects.get_or_create(
            name='Python-01',
            defaults={
                'description': 'Основная группа обучения по направлению Python & Web',
                'code': 'GRP-PY01',
                'teacher': teacher,
            }
        )
        for s in group_students:
            group.students.add(s)

        # 4. Курс "Python с нуля" (из ТЗ Раздел 6, 7)
        course_python, _ = Course.objects.get_or_create(
            title='Python с нуля',
            defaults={
                'description': 'Полный практический курс программирования на Python для начинающих разработчиков.',
                'price': 0,
                'rating': 4.9,
                'category': 'Python',
                'level': 'beginner',
                'status': 'published',
                'cover_image': 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&q=80',
                'author': teacher,
                'course_type': 'programming',
                'content': 'Изучение базовых конструкций, структур данных, алгоритмов и практическое решение задач.',
            }
        )

        # Привязываем курс к группе
        GroupCourse.objects.get_or_create(group=group, course=course_python)
        for s in group_students:
            Enrollment.objects.get_or_create(user=s, course=course_python)

        # --- БЛОК 1: Основы Python ---
        b1, _ = CourseBlock.objects.get_or_create(
            course=course_python,
            order=1,
            defaults={
                'title': 'Блок 1. Основы Python',
                'description': 'Введение в язык, переменные, типы данных и условные операторы.',
            }
        )

        md_l1 = """# Что такое Python

Python — высокоуровневый язык программирования общего назначения с динамической типизацией. Он ориентирован на повышение производительности разработчика и читаемости кода.

## Преимущества Python:
- **Простой и понятный синтаксис**: код легко читать и поддерживать.
- **Огромная экосистема библиотек**: от веб-разработки (Django, FastAPI) до искусственного интеллекта (TensorFlow, PyTorch).
- **Кроссплатформенность**: код работает на Windows, Linux и macOS одинаково.

```python
# Ваша первая программа
def greet(name: str) -> str:
    return f"Привет, {name}! Добро пожаловать в StepLearn."

print(greet("Магамет"))
```

> **Совет**: Не бойтесь экспериментировать в интерактивной оболочке Python!
"""

        l1, _ = Lesson.objects.get_or_create(
            course=course_python,
            order=1,
            defaults={
                'block': b1,
                'title': 'Урок 1. Что такое Python',
                'description': 'Знакомство с языком, установка и первая программа.',
                'content': md_l1,
                'lesson_type': 'theory',
                'is_mandatory': True,
            }
        )

        md_l2 = """# Переменные и типы данных в Python

Переменная — это именованная область памяти, которая хранит значение. В Python переменные создаются в момент присваивания им значения.

## Основные типы данных:
1. `int` — целые числа (`42`, `-10`)
2. `float` — числа с плавающей точкой (`3.14`, `0.001`)
3. `str` — строки (`"Hello, World!"`)
4. `bool` — логический тип (`True` или `False`)

## Пример:
```python
user_name = "Magamed"
course_score = 95
is_enrolled = True

print(f"Студент: {user_name}, Балл: {course_score}, Записан: {is_enrolled}")
```

### Практическое правило:
- Имена переменных должны быть понятными (`student_age`, а не `sa`).
- Используйте стиль `snake_case` для переменных.
"""

        l2, _ = Lesson.objects.get_or_create(
            course=course_python,
            order=2,
            defaults={
                'block': b1,
                'title': 'Урок 2. Переменные и типы данных',
                'description': 'Числа, строки, булевы значения и правила именования.',
                'content': md_l2,
                'lesson_type': 'theory',
                'is_mandatory': True,
            }
        )

        md_l3 = """# Условные операторы: if, elif, else

Условные конструкции позволяют выполнять определенный блок кода только при выполнении заданного условия.

## Синтаксис:
```python
score = int(input("Введите ваш балл: "))

if score >= 90:
    print("Отлично! Оценка 5")
elif score >= 70:
    print("Хорошо! Оценка 4")
elif score >= 50:
    print("Удовлетворительно! Оценка 3")
else:
    print("Экзамен не пройден. Попробуйте еще раз!")
```

### Обратите внимание:
В Python отступы (4 пробела) определяют тело блока кода!
"""

        l3, _ = Lesson.objects.get_or_create(
            course=course_python,
            order=3,
            defaults={
                'block': b1,
                'title': 'Урок 3. Условные операторы',
                'description': 'Ветвление логики в программе, операторы сравнения и логические связки.',
                'content': md_l3,
                'lesson_type': 'practice',
                'is_mandatory': True,
            }
        )

        # Экзамен Блока 1
        exam1, _ = Exam.objects.get_or_create(
            block=b1,
            defaults={
                'course': course_python,
                'title': 'Экзамен: Основы Python (Блок 1)',
                'description': 'Проверка знаний по базовому синтаксису, переменным и условным операторам.',
                'passing_score': 70,
                'max_attempts': 3,
            }
        )

        # Вопросы к экзамену Блока 1
        q1, _ = Question.objects.get_or_create(
            course=course_python,
            exam=exam1,
            text='Как в Python вывести текст на экран в консоль?'
        )
        Answer.objects.get_or_create(question=q1, text='echo()', defaults={'is_correct': False})
        Answer.objects.get_or_create(question=q1, text='print()', defaults={'is_correct': True})
        Answer.objects.get_or_create(question=q1, text='console.log()', defaults={'is_correct': False})
        Answer.objects.get_or_create(question=q1, text='System.out.println()', defaults={'is_correct': False})

        q2, _ = Question.objects.get_or_create(
            course=course_python,
            exam=exam1,
            text='Какой тип данных будет у переменной x = 3.14 ?'
        )
        Answer.objects.get_or_create(question=q2, text='int', defaults={'is_correct': False})
        Answer.objects.get_or_create(question=q2, text='float', defaults={'is_correct': True})
        Answer.objects.get_or_create(question=q2, text='str', defaults={'is_correct': False})
        Answer.objects.get_or_create(question=q2, text='decimal', defaults={'is_correct': False})

        q3, _ = Question.objects.get_or_create(
            course=course_python,
            exam=exam1,
            text='Какое ключевое слово используется для проверки дополнительного условия в блоке if?'
        )
        Answer.objects.get_or_create(question=q3, text='else if', defaults={'is_correct': False})
        Answer.objects.get_or_create(question=q3, text='elif', defaults={'is_correct': True})
        Answer.objects.get_or_create(question=q3, text='elseif', defaults={'is_correct': False})
        Answer.objects.get_or_create(question=q3, text='when', defaults={'is_correct': False})

        # --- БЛОК 2: Циклы и коллекции ---
        b2, _ = CourseBlock.objects.get_or_create(
            course=course_python,
            order=2,
            defaults={
                'title': 'Блок 2. Циклы и структуры данных',
                'description': 'Циклы for и while, списки, кортежи и словари.',
            }
        )

        md_l4 = """# Циклы while и for в Python

Циклы используются для повторения определенного действия несколько раз.

## Цикл for с функцией range():
```python
# Выведет числа от 0 до 4
for i in range(5):
    print(f"Итерация №{i}")
```

## Цикл while:
```python
count = 3
while count > 0:
    print(f"Обратный отсчет: {count}")
    count -= 1
print("Пуск!")
```
"""

        l4, _ = Lesson.objects.get_or_create(
            course=course_python,
            order=4,
            defaults={
                'block': b2,
                'title': 'Урок 4. Циклы while и for',
                'description': 'Повторение инструкций, break и continue.',
                'content': md_l4,
                'lesson_type': 'theory',
                'is_mandatory': True,
            }
        )

        md_l5 = """# Списки (list) и словари (dict)

Списки хранят упорядоченную последовательность элементов, а словари — пары ключ-значение.

```python
fruits = ["яблоко", "банан", "апельсин"]
fruits.append("груша")

student_info = {
    "name": "Магамет",
    "group": "Python-01",
    "completed_lessons": 3
}

print(student_info["name"])
```
"""

        l5, _ = Lesson.objects.get_or_create(
            course=course_python,
            order=5,
            defaults={
                'block': b2,
                'title': 'Урок 5. Списки и словари',
                'description': 'Структуры данных для хранения наборов элементов.',
                'content': md_l5,
                'lesson_type': 'practice',
                'is_mandatory': True,
            }
        )

        # Отмечаем пройденные уроки для студента Магамета, чтобы в профиле был виден реальный прогресс
        StudentLessonProgress.objects.get_or_create(user=student, lesson=l1, defaults={'is_completed': True, 'completed_at': timezone.now()})
        StudentLessonProgress.objects.get_or_create(user=student, lesson=l2, defaults={'is_completed': True, 'completed_at': timezone.now()})

        en = Enrollment.objects.filter(user=student, course=course_python).first()
        if en:
            en.completed_lessons = 2
            en.progress_percentage = 40
            en.save()

        # Также фиксируем сдачу экзамена 1 попыткой на 100%
        ExamAttempt.objects.get_or_create(
            user=student,
            exam=exam1,
            defaults={'score': 100, 'passed': True}
        )

        # 5. Дополнительный курс "React с нуля" (как в макете ТЗ)
        course_react, _ = Course.objects.get_or_create(
            title='React с нуля',
            defaults={
                'description': 'Современная разработка пользовательских интерфейсов на React, TypeScript и Vite.',
                'price': 0,
                'rating': 4.8,
                'category': 'Frontend',
                'level': 'intermediate',
                'status': 'published',
                'cover_image': 'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=800&q=80',
                'author': teacher,
                'course_type': 'programming',
                'content': 'Компоненты, хуки, состояние и интеграция с REST API.',
            }
        )
        Enrollment.objects.get_or_create(user=student, course=course_react, defaults={'completed_lessons': 1, 'progress_percentage': 20})

        self.stdout.write(self.style.SUCCESS('Демо-данные StepLearn успешно инициализированы!'))
        self.stdout.write(self.style.SUCCESS('Преподаватель: teacher / teacher123'))
        self.stdout.write(self.style.SUCCESS('Студент: student / student123'))
        self.stdout.write(self.style.SUCCESS('Администратор: admin / admin123'))
