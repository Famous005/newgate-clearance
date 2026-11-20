from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clearance.models import Unit, AcademicSession

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed initial data: admin, officers, units, session'

    def handle(self, *args, **kwargs):

        # ── Admin ─────────────────────────────────────────────────────────────
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'System',
                'last_name':  'Administrator',
                'email':      'admin@num.edu.ng',
                'role':       'admin',
                'is_staff':   True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('Admin@1234')
            admin.save()
            self.stdout.write(f'  Created admin')
        else:
            self.stdout.write(f'  Admin exists')

        # ── Officers ──────────────────────────────────────────────────────────
        officers_data = [
            ('library_officer',  'Khadijat', 'Mohammed',
             'Library',                       'khadijat.mohammed@newgate.edu.ng'),
            ('medical_officer',  'Usman',    'Bello',
             'Medical Unit',                  'usman.bello@newgate.edu.ng'),
            ('hod_cs',           'Adamu',    'Isah',
             'Computer Science',              'adamu.isah@newgate.edu.ng'),
            ('hod_ict',          'Jamilu',   'Mai-Panuku',
             'Information & Communication Technology',
             'jamilu.maipanuku@newgate.edu.ng'),
            ('dean_fcit',        'Dean',     'FCIT',
             'Faculty of Computing & IT',    'dean.fcit@newgate.edu.ng'),
            ('academic_officer', 'Hadijah',  'Yamman',
             'Academic Unit',                'hadijah.yamman@newgate.edu.ng'),
        ]

        created_officers = {}
        for username, first, last, dept, email in officers_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name':  last,
                    'department': dept,
                    'role':       'unit_officer',
                    'email':      email,
                }
            )
            if created:
                user.set_password('Officer@1234')
                user.save()
                self.stdout.write(f'  Created officer: {user.get_full_name()}')
            created_officers[username] = user

        # ── Bursary ───────────────────────────────────────────────────────────
        bursary, created = User.objects.get_or_create(
            username='bursary_officer',
            defaults={
                'first_name': 'Habiba',
                'last_name':  'Abubakar',
                'department': 'Bursary',
                'role':       'bursary',
                'email':      'habiba.abubakar@newgate.edu.ng',
            }
        )
        if created:
            bursary.set_password('Officer@1234')
            bursary.save()
            self.stdout.write(f'  Created bursary officer')

        # ── Units ─────────────────────────────────────────────────────────────
        units_data = [
            (1, 'Library',             'library_officer'),
            (2, 'Medical Unit',        'medical_officer'),
            (3, 'Head of Department',  'hod_cs'),
            (4, 'Dean of Faculty',     'dean_fcit'),
            (5, 'Academic Unit',       'academic_officer'),
        ]

        for order, name, officer_username in units_data:
            officer = created_officers.get(officer_username)
            unit, created = Unit.objects.get_or_create(
                order=order,
                defaults={
                    'name':      name,
                    'officer':   officer,
                    'is_active': True,
                }
            )
            if not created:
                unit.name    = name
                unit.officer = officer
                unit.save()
            self.stdout.write(f'  Unit {order}: {name}')

        # ── Academic Session ──────────────────────────────────────────────────
        session, created = AcademicSession.objects.get_or_create(
            name='2025/2026',
            defaults={'is_active': True}
        )
        if created:
            self.stdout.write(f'  Created session: 2025/2026')

        self.stdout.write(self.style.SUCCESS(
            '\nData seeded successfully.'
        ))