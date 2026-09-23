from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import (
    Answer,
    Course,
    Enrollment,
    GroupCourse,
    GroupLessonAccess,
    Lesson,
    Question,
    StudentLessonProgress,
    StudyGroup,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Создаёт демонстрационные данные StepLearn (пользователи, группы, модульные курсы, вопросы)'

    def handle(self, *args, **options):
        # 1. Администратор и Преподаватель
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Администратор',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if not admin.check_password('admin123'):
            admin.set_password('admin123')
            admin.role = 'admin'
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()

        teacher, _ = User.objects.get_or_create(
            username='teacher',
            defaults={
                'email': 'teacher@cisco.edu',
                'first_name': 'Иван',
                'last_name': 'Петров',
                'role': 'teacher',
                'is_staff': True,
            },
        )
        if not teacher.check_password('teacher123'):
            teacher.set_password('teacher123')
            teacher.role = 'teacher'
            teacher.is_staff = True
            teacher.save()

        # 2. 10 Студентов для группы
        group_students = []
        for i in range(1, 11):
            s, _ = User.objects.get_or_create(
                username=f'student{i}',
                defaults={
                    'email': f'student{i}@example.com',
                    'first_name': f'Студент {i}',
                    'role': 'student',
                },
            )
            if not s.check_password('secret123'):
                s.set_password('secret123')
                s.role = 'student'
                s.save()
            group_students.append(s)

        # Стандартный студент для одиночного теста
        std_main, _ = User.objects.get_or_create(
            username='student',
            defaults={'email': 'student@example.com', 'first_name': 'Студент', 'role': 'student'},
        )
        if not std_main.check_password('secret123'):
            std_main.set_password('secret123')
            std_main.save()

        # 3. Курс в стиле Stepik / Cisco с последовательными модулями
        cisco_course, _ = Course.objects.get_or_create(
            title='Сетевые технологии Cisco & Python (Stepik / Cisco)',
            defaults={
                'description': 'Практический модульный курс по сетевым технологиям. Доступ к следующим модулям регулируется преподавателем для учебной группы.',
                'price': 0,
                'rating': 4.95,
                'author': teacher,
                'course_type': 'text',
                'content': 'Комплексный модульный курс по сетям и автоматизации.',
            },
        )

        l1, _ = Lesson.objects.get_or_create(
            course=cisco_course,
            order=1,
            defaults={
                'title': 'Модуль 1: Основы сетей и модель OSI',
                'description': 'Введение в архитектуру компьютерных сетей, уровни OSI и стек TCP/IP.',
                'content': '''# Модуль 1: Основы компьютерных сетей

Добро пожаловать в первый модуль курса по сетевым технологиям!

## 1. Что такое компьютерная сеть?
Компьютерная сеть — это система связи между двумя или более устройствами (компьютерами, серверами, маршрутизаторами), позволяющая обмениваться данными и разделять ресурсы.

### Семиуровневая модель OSI:
1. **Физический (Physical)** — передача битов по проводам, оптике или радио.
2. **Канальный (Data Link)** — MAC-адресация, кадры (Frames), коммутаторы (Switches).
3. **Сетевой (Network)** — логическая IP-адресация, маршрутизаторы (Routers).
4. **Транспортный (Transport)** — TCP (с гарантией доставки) и UDP (быстрый, без подтверждения).
5. **Сеансовый (Session)** — управление сессиями связи.
6. **Представительский (Presentation)** — шифрование, сжатие, форматы данных.
7. **Прикладной (Application)** — HTTP, DNS, SSH, FTP.

> **Важно:** Завершите чтение материала и нажмите кнопку **«Завершить модуль»**, чтобы зафиксировать прогресс для вашей группы!
''',
            },
        )

        l2, _ = Lesson.objects.get_or_create(
            course=cisco_course,
            order=2,
            defaults={
                'title': 'Модуль 2: Маршрутизация и IP-адресация (Cisco IOS)',
                'description': 'Настройка маршрутизаторов Cisco, разбиение сетей на подсети (VLSM), протокол OSPF.',
                'content': '''# Модуль 2: Маршрутизация и IP-адресация

В этом модуле рассматривается конфигурирование сетевого оборудования Cisco.

## 1. Базовые команды Cisco IOS
```bash
Router> enable
Router# configure terminal
Router(config)# hostname Core-R1
Core-R1(config)# interface GigabitEthernet0/0
Core-R1(config-if)# ip address 192.168.10.1 255.255.255.0
Core-R1(config-if)# no shutdown
```

## 2. Протокол динамической маршрутизации OSPF
OSPF (Open Shortest Path First) — протокол внутреннего шлюза, использующий алгоритм Дейкстры:
```bash
Core-R1(config)# router ospf 1
Core-R1(config-router)# network 192.168.10.0 0.0.0.255 area 0
```
''',
            },
        )

        l3, _ = Lesson.objects.get_or_create(
            course=cisco_course,
            order=3,
            defaults={
                'title': 'Модуль 3: Автоматизация сетей на Python (Netmiko & NAPALM)',
                'description': 'Программирование сетевой инфраструктуры с использованием скриптов Python.',
                'content': '''# Модуль 3: Автоматизация сетевой инфраструктуры

Современный сетевой инженер автоматизирует рутину с помощью скриптов.

## Пример подключения к Cisco по SSH через Netmiko:
```python
from netmiko import ConnectHandler

device = {
    'device_type': 'cisco_ios',
    'host': '192.168.10.1',
    'username': 'admin',
    'password': 'password123',
}

with ConnectHandler(**device) as net_connect:
    output = net_connect.send_command('show ip int brief')
    print(output)
```
''',
            },
        )

        # 4. Учебная группа «Группа Cisco-101»
        group, _ = StudyGroup.objects.get_or_create(
            code='GRP-CISCO',
            defaults={
                'name': 'Группа Cisco-101',
                'description': 'Учебная группа по сетевой инженерии (10 студентов). Поэтапное открытие модулей.',
                'teacher': teacher,
            },
        )
        group.students.set(group_students)

        # Назначаем курс группе
        gc, _ = GroupCourse.objects.get_or_create(group=group, course=cisco_course)

        # Записываем всех студентов группы на курс
        for s in group_students:
            Enrollment.objects.get_or_create(user=s, course=cisco_course)

        # Настраиваем доступы к модулям:
        # Модуль 1: Открыт
        gla1, _ = GroupLessonAccess.objects.get_or_create(
            group=group,
            lesson=l1,
            defaults={'is_unlocked': True, 'unlocked_at': timezone.now(), 'auto_unlock_when_all_pass': True},
        )
        gla1.is_unlocked = True
        gla1.save()

        # Модуль 2: Заблокирован (откроется, когда все 10 сдадут Модуль 1, или препод откроет вручную)
        gla2, _ = GroupLessonAccess.objects.get_or_create(
            group=group,
            lesson=l2,
            defaults={'is_unlocked': False, 'auto_unlock_when_all_pass': True},
        )
        gla2.is_unlocked = False
        gla2.auto_unlock_when_all_pass = True
        gla2.save()

        # Модуль 3: Заблокирован
        gla3, _ = GroupLessonAccess.objects.get_or_create(
            group=group,
            lesson=l3,
            defaults={'is_unlocked': False, 'auto_unlock_when_all_pass': True},
        )
        gla3.is_unlocked = False
        gla3.save()

        # Симулируем прогресс: 7 из 10 студентов уже сдали Модуль 1!
        # Преподаватель в админке сразу увидит 70% готовности группы.
        for s in group_students[:7]:
            prog, _ = StudentLessonProgress.objects.get_or_create(user=s, lesson=l1)
            prog.is_completed = True
            prog.completed_at = timezone.now()
            prog.save()
            en = Enrollment.objects.filter(user=s, course=cisco_course).first()
            if en:
                en.completed_lessons = 1
                en.progress_percentage = 33
                en.save()

        # 5. Другие демо-курсы для разнообразия
        c1, c1_created = Course.objects.get_or_create(
            title='Основы Python (с тестом)',
            defaults={
                'description': 'Изучите основы языка Python с нуля: переменные, типы данных, циклы и функции.',
                'price': 0,
                'rating': 4.9,
                'author': teacher,
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
            ]
            for q_text, answers in demo_questions:
                q = Question.objects.create(course=c1, text=q_text)
                Answer.objects.bulk_create([
                    Answer(question=q, text=text, is_correct=is_correct)
                    for text, is_correct in answers
                ])

        self.stdout.write(self.style.SUCCESS(
            '✓ Демо-данные успешно созданы:\n'
            '  - Преподаватель: teacher / teacher123\n'
            '  - Администратор: admin / admin123\n'
            '  - 10 студентов: student1 .. student10 / secret123\n'
            '  - Учебная группа: Группа Cisco-101 (код: GRP-CISCO)\n'
            '  - Модульный курс: Сетевые технологии Cisco & Python (Stepik / Cisco)\n'
            '    [Модуль 1: Открыт, сдали 7/10 студентов (70%)]\n'
            '    [Модуль 2: Заблокирован, ждет 100% сдачи или открытия преподавателем]\n'
            '    [Модуль 3: Заблокирован]'
        ))
