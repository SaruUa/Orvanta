"""
Скрипт заповнення бази даних демонстраційними даними.
Запуск: python seed_salon.py (із директорії src/)
"""

import os
import sys
import django
import random
from datetime import date, time, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from clients.models import Client
from services_catalog.models import Service, ServiceCategory
from appointments.models import Appointment, AppointmentStatus, AppointmentStatusHistory
from users.models import Organization

User = get_user_model()

# ── Налаштування ──────────────────────────────────────────────────────────────

ORGANIZATION_SLUG = None   # None = перша організація в БД
ADMIN_USERNAME    = None   # None = перший адмін в організації

random.seed(42)

# ── Дані ──────────────────────────────────────────────────────────────────────

CATEGORIES_AND_SERVICES = {
    'Волосся': [
        ('Жіноча стрижка',           450,  60),
        ('Чоловіча стрижка',         250,  30),
        ('Дитяча стрижка',           180,  25),
        ('Фарбування волосся',        900, 120),
        ('Мелірування',             1200, 150),
        ('Кератинове випрямлення',  1800, 180),
        ('Укладання',                350,  45),
        ('Плетіння кіс',             400,  60),
    ],
    'Нігті': [
        ('Манікюр класичний',        350,  60),
        ('Манікюр апаратний',        450,  75),
        ('Гель-лак',                 500,  90),
        ('Нарощування нігтів',       900, 120),
        ('Педикюр класичний',        500,  75),
        ('Педикюр апаратний',        650,  90),
    ],
    'Догляд за шкірою': [
        ('Чищення обличчя',          700,  90),
        ('Пілінг обличчя',           650,  60),
        ('Мезотерапія',             1400,  75),
        ('Ін\'єкції краси',         2500,  60),
        ('Масаж обличчя',            500,  45),
    ],
    'Масаж': [
        ('Масаж спини',              600,  60),
        ('Масаж тіла загальний',     900,  90),
        ('Антицелюлітний масаж',     750,  60),
        ('Лімфодренажний масаж',     800,  75),
        ('Масаж голови',             350,  30),
    ],
    'Брови та вії': [
        ('Корекція брів',            250,  30),
        ('Фарбування брів',          200,  20),
        ('Ламінування брів',         600,  60),
        ('Нарощування вій',          900, 120),
        ('Ламінування вій',          700,  90),
        ('Перманентний макіяж брів', 2200, 150),
    ],
}

EMPLOYEES = [
    ('olena_k',    'Олена',    'Коваль',    'olena@salon.ua',    '0501234567'),
    ('natalia_m',  'Наталія',  'Мельник',   'natalia@salon.ua',  '0502345678'),
    ('iryna_s',    'Ірина',    'Савченко',  'iryna@salon.ua',    '0503456789'),
    ('tetyana_p',  'Тетяна',   'Петренко',  'tetyana@salon.ua',  '0504567890'),
    ('oksana_h',   'Оксана',   'Гончар',    'oksana@salon.ua',   '0505678901'),
]

CLIENT_NAMES = [
    ('Аліна Бондаренко',    '+380671112233', '1995-03-12'),
    ('Вікторія Кравченко',  '+380672223344', '1988-07-24'),
    ('Марина Шевченко',     '+380673334455', '2000-01-08'),
    ('Юлія Лисенко',        '+380674445566', '1993-11-30'),
    ('Олена Руденко',       '+380675556677', '1985-05-17'),
    ('Катерина Мороз',      '+380676667788', '1997-09-03'),
    ('Ірина Білик',         '+380677778899', '1991-04-22'),
    ('Наталія Захаренко',   '+380678889900', '2002-12-15'),
    ('Тетяна Дмитренко',    '+380679990011', '1989-08-07'),
    ('Людмила Яременко',    '+380680001122', '1983-02-28'),
    ('Оксана Кириченко',    '+380681112233', '1996-06-19'),
    ('Анна Коломієць',      '+380682223344', '1994-10-11'),
    ('Дарина Гнатенко',     '+380683334455', '2001-03-25'),
    ('Поліна Тимченко',     '+380684445566', '1999-07-14'),
    ('Світлана Пономаренко','+380685556677', '1987-01-09'),
    ('Галина Ткаченко',     '+380686667788', '1982-11-21'),
    ('Надія Василенко',     '+380687778899', '1998-04-05'),
    ('Олеся Панченко',      '+380688889900', '1992-08-30'),
    ('Христина Мартиненко', '+380689990011', '2003-12-03'),
    ('Валентина Клименко',  '+380690001122', '1980-06-16'),
    ('Софія Литвиненко',    '+380691112233', '2004-02-20'),
    ('Антоніна Зінченко',   '+380692223344', '1986-09-08'),
    ('Жанна Гаврилюк',      '+380693334455', '1995-03-27'),
    ('Лариса Павленко',     '+380694445566', '1990-07-13'),
    ('Ганна Стець',         '+380695556677', '1984-01-31'),
    ('Вікторія Дяченко',    '+380696667788', '1997-05-06'),
    ('Марія Власенко',      '+380697778899', '2000-09-22'),
    ('Таїсія Федоренко',    '+380698889900', '1993-11-04'),
    ('Карина Швець',        '+380699990011', '2002-04-18'),
    ('Євгенія Мусієнко',    '+380700001122', '1988-08-12'),
    ('Олена Сердюк',        '+380701112233', '1996-02-25'),
    ('Руслана Пилипенко',   '+380702223344', '1991-06-09'),
    ('Анастасія Кулик',     '+380703334455', '1999-10-01'),
    ('Яна Радченко',        '+380704445566', '1994-03-14'),
    ('Валерія Бойченко',    '+380705556677', '1987-07-28'),
]

COMMENTS = [
    'Клієнт постійний, любить класику.',
    'Перший візит, рекомендована подругою.',
    'Алергія на деякі барвники, уточнити.',
    'Вчасно не прийшла минулого разу.',
    'Дуже задоволена результатом.',
    'Просила знижку — обговорити з адміном.',
    'Бажає запис щомісяця.',
    'Привела подругу.',
    '',
    '',
    '',
]

# ── Логіка ────────────────────────────────────────────────────────────────────

def get_organization():
    if ORGANIZATION_SLUG:
        return Organization.objects.get(slug=ORGANIZATION_SLUG)
    # Шукаємо організацію де є адмін
    admin = User.objects.filter(role='admin', organization__isnull=False).first()
    if admin:
        org = admin.organization
        print(f'  Організація: {org.name}')
        return org
    raise RuntimeError('Організацію з адміністратором не знайдено.')


def get_admin(org):
    admin = User.objects.filter(organization=org, role='admin').first()
    if not admin:
        raise RuntimeError(f'Адміністратора не знайдено в організації "{org.name}".')
    print(f'  Адміністратор: {admin.username}')
    return admin


def create_employees(org, admin):
    employees = []
    for username, first, last, email, phone in EMPLOYEES:
        user, created = User.objects.get_or_create(
            username=username,
            defaults=dict(
                first_name=first,
                last_name=last,
                email=email,
                phone=phone,
                organization=org,
                role='employee',
                is_active=True,
            )
        )
        if created:
            user.set_password('Salon2024!')
            user.save()
            print(f'  + Співробітник: {user.get_full_name()}')
        else:
            print(f'  ~ Співробітник вже існує: {user.username}')
        employees.append(user)
    return employees


def create_services(org, admin):
    services = []
    for cat_name, items in CATEGORIES_AND_SERVICES.items():
        category, _ = ServiceCategory.objects.get_or_create(
            organization=org,
            name=cat_name,
        )
        for svc_name, price, duration in items:
            svc, created = Service.objects.get_or_create(
                organization=org,
                category=category,
                name=svc_name,
                defaults=dict(
                    price=Decimal(str(price)),
                    duration_minutes=duration,
                    is_active=True,
                )
            )
            if created:
                print(f'  + Послуга: {svc_name}')
            services.append(svc)
    return services


def create_clients(org, admin):
    clients = []
    for full_name, phone, birth_date in CLIENT_NAMES:
        client, created = Client.objects.get_or_create(
            organization=org,
            phone=phone,
            defaults=dict(
                full_name=full_name,
                birth_date=birth_date,
                is_active=True,
                created_by=admin,
            )
        )
        if created:
            print(f'  + Клієнт: {full_name}')
        clients.append(client)
    return clients


def make_time(hour, minute=0):
    return time(hour, minute)


def create_appointments(org, admin, clients, services, employees):
    today = date.today()
    count_created = 0
    count_skipped = 0

    # Розподіл: минулі 90 днів + майбутні 30 днів
    date_ranges = (
        # (start_offset, end_offset, кількість, статуси з вагами)
        (-90, -30, 80, [
            (AppointmentStatus.COMPLETED,  75),
            (AppointmentStatus.CANCELLED,  15),
            (AppointmentStatus.CONFIRMED,  10),
        ]),
        (-29, -1, 60, [
            (AppointmentStatus.COMPLETED,  60),
            (AppointmentStatus.CONFIRMED,  25),
            (AppointmentStatus.CANCELLED,  10),
            (AppointmentStatus.PLANNED,     5),
        ]),
        (0, 30, 40, [
            (AppointmentStatus.PLANNED,    55),
            (AppointmentStatus.CONFIRMED,  45),
        ]),
    )

    WORK_HOURS = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18]

    for start_offset, end_offset, count, status_weights in date_ranges:
        statuses, weights = zip(*status_weights)
        for _ in range(count):
            offset      = random.randint(start_offset, end_offset)
            appt_date   = today + timedelta(days=offset)
            service     = random.choice(services)
            client      = random.choice(clients)
            employee    = random.choice(employees)
            hour        = random.choice(WORK_HOURS)
            start       = make_time(hour)
            end_hour    = hour + max(1, service.duration_minutes // 60)
            end_min     = service.duration_minutes % 60
            end         = make_time(min(end_hour, 20), end_min)
            status      = random.choices(statuses, weights=weights)[0]
            comment     = random.choice(COMMENTS)

            # Фактична вартість — тільки для виконаних (80% заповнені), без копійок
            actual_price = None
            if status == AppointmentStatus.COMPLETED and random.random() < 0.80:
                variation    = Decimal(str(random.uniform(0.85, 1.2)))
                actual_price = Decimal(round(service.price * variation))

            appt = Appointment.objects.create(
                client          = client,
                service         = service,
                employee        = employee,
                created_by      = admin,
                appointment_date= appt_date,
                start_time      = start,
                end_time        = end,
                status          = status,
                actual_price    = actual_price,
                comment         = comment,
                organization    = org,
            )
            count_created += 1

            # Історія статусу для виконаних і скасованих
            if status in (AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED):
                AppointmentStatusHistory.objects.create(
                    appointment  = appt,
                    old_status   = AppointmentStatus.PLANNED,
                    new_status   = status,
                    changed_by   = admin,
                    organization = org,
                )

    print(f'  + Записів створено: {count_created}')


def main():
    print('\n=== Seed: Демо-дані Orvanta ===\n')

    print('[1/5] Організація та адмін...')
    org   = get_organization()
    admin = get_admin(org)

    print('\n[2/5] Співробітники...')
    employees = create_employees(org, admin)

    print('\n[3/5] Категорії та послуги...')
    services = create_services(org, admin)

    print('\n[4/5] Клієнти...')
    clients = create_clients(org, admin)

    print('\n[5/5] Записи...')
    create_appointments(org, admin, clients, services, employees)

    print('\n✓ Готово! База заповнена демонстраційними даними.\n')


if __name__ == '__main__':
    main()
