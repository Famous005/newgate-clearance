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
                'first_name':   'System',
                'last_name':    'Administrator',
                'email':        'admin@newgate.edu.ng',
                'role':         'admin',
                'is_staff':     True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('Admin@1234')
            admin.save()
            self.stdout.write('  Created admin')
        else:
            self.stdout.write('  Admin exists')

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
            self.stdout.write('  Created bursary officer')

        # ── HOD ICT (not a unit officer but needed for routing) ───────────────
        hod_ict, created = User.objects.get_or_create(
            username='hod_ict',
            defaults={
                'first_name': 'Jamilu',
                'last_name':  'Mai-Panuku',
                'department': 'Information & Communication Technology',
                'role':       'unit_officer',
                'email':      'jamilu.maipanuku@newgate.edu.ng',
            }
        )
        if created:
            hod_ict.set_password('Officer@1234')
            hod_ict.save()
            self.stdout.write('  Created HOD ICT')

        # ── Officers and Units (in approval sequence order) ───────────────────
        officers_units = [
            # (username, first, last, dept, email, order, unit_name)
            ('lab_officer',      'Laboratory',    'Office',
             'Laboratory',
             'ahmed.suleiman@newgate.edu.ng',
             1, 'Laboratory Unit'),

            ('hod_cs',           'Adamu',    'Isah',
             'Computer Science',
             'adamu.isah@newgate.edu.ng',
             2, 'Head of Department'),

            ('dean_fcit',        'Dean',     'FCIT',
             'Faculty of Computing & IT',
             'dean.fcit@newgate.edu.ng',
             3, 'Dean of Faculty'),

            ('security_officer', 'Hussaini',     'Nuhu',
             'Security Unit',
             'hussaini.nuhu@newgate.edu.ng',
             4, 'Security Unit'),

            ('library_officer',  'Khadijat', 'Mohammed',
             'Library',
             'khadijat.mohammed@newgate.edu.ng',
             5, 'Library Unit'),

            ('medical_officer',  'Clinic',    'Office',
             'Medical Unit',
             'usman.bello@newgate.edu.ng',
             6, 'University Clinic'),

            ('estate_officer',   'Oladele',  'Oluwakemi',
             'Directorate of Estate & Physical Planning',
             'oladele.oluwakemi@newgate.edu.ng',
             7, 'Directorate of Estate & Physical Planning'),

            ('affairs_officer',  'Samuel', 'Olatunbosun',
             'Directorate of Student Affairs',
             'abubakar.sadiq@newgate.edu.ng',
             8, 'Directorate of Student Affairs'),

            ('registrar',        'Registrar', 'Office',
             'Registrar Office',
             'registrar@newgate.edu.ng',
             9, 'Registrar'),
        ]

        # Delete existing units before recreating
        Unit.objects.all().delete()

        for (username, first, last, dept, email,
             order, unit_name) in officers_units:

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
                self.stdout.write(
                    f'  Created officer: {user.get_full_name()}'
                )
            else:
                self.stdout.write(
                    f'  Exists: {user.get_full_name()}'
                )

            Unit.objects.create(
                name=unit_name,
                order=order,
                officer=user,
                is_active=True,
            )
            self.stdout.write(f'  Unit {order}: {unit_name}')

        # ── Academic Session ──────────────────────────────────────────────────
        for session_name in ['2024/2025', '2025/2026']:
            session, created = AcademicSession.objects.get_or_create(
                name=session_name,
                defaults={'is_active': session_name == '2025/2026'}
            )
            if created:
                self.stdout.write(f'  Created session: {session_name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nData seeded successfully.'
            f'\n  Units:    {Unit.objects.count()}'
            f'\n  Officers: {User.objects.filter(role="unit_officer").count()}'
            f'\n  Bursary:  {User.objects.filter(role="bursary").count()}'
            f'\n  Admin:    {User.objects.filter(role="admin").count()}'
        ))