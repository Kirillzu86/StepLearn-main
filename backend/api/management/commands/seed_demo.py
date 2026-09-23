from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from api.models import Answer, Course, Enrollment, Question

User = get_user_model()


class Command(BaseCommand):
    help = 'Создаёт демонстрационные данные StepLearn (пользователи, курсы, вопросы)'

    def handle(self, *args, **options):
        # 1. Пользователи
        student, _ = User.objects.get_or_create(
            username='student',
            defaults={'email': 'student@example.com', 'first_name': 'Студент'},
        )
        if not student.check_password('secret123'):
            student.set_password('secret123')
            student.save()

        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Администратор',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if not admin.check_password('admin123'):
            admin.set_password('admin123')
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()

        # 2. Курс 1: Python
        c1, c1_created = Course.objects.get_or_create(
            title='Основы Python (с тестом)',
            defaults={
                'description': 'Изучите основы языка Python с нуля: переменные, типы данных, циклы и функции.',
                'price': 0,
                'rating': 4.9,
                'author': admin,
            },
        )
        if c1_created:
            demo_questions = [
                ('Какая функция используется для вывода текста на экран?', [
                    ('print()', True), ('input()', False), ('scan()', False)
                ]),
                ('Какой символ используется для комментариев в Python?', [
                    ('#', True), ('//', False), ('--', False)
                ]),
                ("Что вернет выражение 3 * 'A'?", [
                    ("'AAA'", True), ("'3A'", False), ('Ошибка', False)
                ]),
            ]
            for q_text, answers in demo_questions:
                q = Question.objects.create(course=c1, text=q_text)
                Answer.objects.bulk_create([
                    Answer(question=q, text=text, is_correct=is_correct)
                    for text, is_correct in answers
                ])

        # 3. Курс 2: Django & React
        c2, c2_created = Course.objects.get_or_create(
            title='Fullstack-разработка: Django & React',
            defaults={
                'description': 'Практический курс по созданию современных веб-приложений с Django REST API и React frontend.',
                'price': 2490,
                'rating': 4.8,
                'author': admin,
            },
        )
        if c2_created:
            q1 = Question.objects.create(
                course=c2,
                text='Какой файл отвечает за маршруты URL в проекте Django?',
            )
            Answer.objects.bulk_create([
                Answer(question=q1, text='urls.py', is_correct=True),
                Answer(question=q1, text='routes.py', is_correct=False),
                Answer(question=q1, text='views.py', is_correct=False),
            ])

        # 4. Курс 3: PostgreSQL
        c3, c3_created = Course.objects.get_or_create(
            title='Базы данных и PostgreSQL',
            defaults={
                'description': 'Реляционные базы данных, SQL запросы, индексы, транзакции и оптимизация.',
                'price': 0,
                'rating': 4.7,
                'author': admin,
            },
        )
        if c3_created:
            q1 = Question.objects.create(
                course=c3,
                text='Какая команда используется для выборки данных из таблицы SQL?',
            )
            Answer.objects.bulk_create([
                Answer(question=q1, text='SELECT', is_correct=True),
                Answer(question=q1, text='GET', is_correct=False),
                Answer(question=q1, text='FETCH', is_correct=False),
            ])

        # 5. Курс 4: Markdown лонгрид (без вопросов)
        git_md_content = """# Полное руководство по Git и GitHub

Добро пожаловать в полное практическое руководство по системе контроля версий **Git**! Этот курс полностью текстовый, оформлен в виде подробного Markdown-конспекта.

---

## 1. Введение в Git

**Git** — это распределенная система управления версиями, созданная Линусом Торвальдсом в 2005 году.

### Основные концепции:
- **Рабочая директория (Working Directory)** — файлы, которые вы редактируете прямо сейчас.
- **Индекс (Staging Area)** — подготовленные к фиксации изменения.
- **Хранилище (Repository)** — база данных всех коммитов и истории.

---

## 2. Базовые команды

### Инициализация и клонирование
```bash
# Инициализировать новый репозиторий в текущей папке
git init

# Склонировать удаленный репозиторий
git clone https://github.com/username/repo.git
```

### Проверка статуса и фиксация изменений
```bash
# Проверить состояние файлов
git status

# Добавить файл в индекс
git add main.py

# Добавить все измененные файлы
git add .

# Сделать коммит с понятным сообщением
git commit -m "feat: добавить авторизацию пользователей"
```

---

## 3. Работа с ветками (Branching)

Ветки позволяют изолированно разрабатывать новую функциональность:

| Команда | Описание |
|---|---|
| `git branch` | Список локальных веток |
| `git checkout -b feature/auth` | Создать и переключиться на ветку |
| `git switch main` | Переключиться на ветку main |
| `git merge feature/auth` | Влить ветку в текущую |

---

## 4. Полезные трюки и советы

> **Совет:** Делайте коммиты атомарными! Один коммит = одно логическое изменение.

### Отмена изменений:
```bash
# Отменить изменения в файле до индексации
git restore filename.py

# Мягкий откат последнего коммита
git reset --soft HEAD~1
```

Вы успешно изучили основы Git! Нажмите кнопку **«Завершить изучение курса»**, чтобы зафиксировать 100% прогресс.
"""

        c4, _ = Course.objects.get_or_create(
            title='Шпаргалка и руководство по Git (Markdown)',
            defaults={
                'description': 'Полный текстовый курс-конспект по работе с Git и GitHub без тестов. Удобное оглавление и примеры команд.',
                'price': 0,
                'rating': 5.0,
                'author': admin,
                'course_type': 'text',
                'content': git_md_content,
            },
        )
        if not c4.content:
            c4.content = git_md_content
            c4.course_type = 'text'
            c4.save()

        # Записать студента на 1-й курс с некоторым прогрессом
        en, _ = Enrollment.objects.get_or_create(
            user=student,
            course=c1,
            defaults={
                'current_index': 1,
                'progress_percentage': 33,
                'completed_lessons': 1,
                'correct_answers': 1,
            },
        )

        self.stdout.write(self.style.SUCCESS('Демо-данные успешно созданы / обновлены!'))
