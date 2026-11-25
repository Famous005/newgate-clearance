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
                'first_name': 'Finance',
                'last_name':  'Office',
                'department': 'Bursary',
                'role':       'bursary',
                'email':      'habiba.abubakar@newgate.edu.ng',
            }
        )
        if created:
            bursary.set_password('Officer@1234')
            bursary.save()
        # Force update name in case it already existed
        bursary.first_name = 'Finance'
        bursary.last_name  = 'Office'
        bursary.save()
        self.stdout.write(f'  Bursary: {bursary.get_full_name()}')

        # ── HOD ICT (routing only — not assigned to a unit directly) ─────────
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
        hod_ict.first_name = 'Jamilu'
        hod_ict.last_name  = 'Mai-Panuku'
        hod_ict.save()
        self.stdout.write(f'  HOD ICT: {hod_ict.get_full_name()}')

        # ── Officers and Units ────────────────────────────────────────────────
        # Format: username, first, last, dept, email, password,
        #         unit_order, unit_name
        officers_units = [
            ('lab_officer',
             'Laboratory',     'Office',
             'Laboratory',
             'ahmed.suleiman@newgate.edu.ng',
             1, 'Laboratory Unit'),

            ('hod_cs',
             'Adamu',     'Isah',
             'Computer Science',
             'adamu.isah@newgate.edu.ng',
             2, 'Head of Department'),

            ('dean_fcit',
             'Ramatu',    'Nda Mohammed',
             'Faculty of Computing & IT',
             'ramatu.ndamohammed@newgate.edu.ng',
             3, 'Dean of Faculty'),

            ('security_officer',
             'Hussaini',  'Nuhu',
             'Security Unit',
             'hussaini.nuhu@newgate.edu.ng',
             4, 'Security Unit'),

            ('library_officer',
             'Library',  'Office',
             'Library',
             'khadijat.mohammed@newgate.edu.ng',
             5, 'Library Unit'),

            ('medical_officer',
             'Clinic',     'Office',
             'Medical Unit',
             'usman.bello@newgate.edu.ng',
             6, 'University Clinic'),

            ('estate_officer',
             'Oladele',   'Oluwakemi',
             'Directorate of Estate & Physical Planning',
             'oladele.oluwakemi@newgate.edu.ng',
             7, 'Directorate of Estate & Physical Planning'),

            ('affairs_officer',
             'Samuel',    'Olatunbosun',
             'Directorate of Student Affairs',
             'samuel.olatunbosun@newgate.edu.ng',
             8, 'Directorate of Student Affairs'),

            ('registrar',
             'Registrar', 'Office',
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
            # Force update real names regardless
            user.first_name = first
            user.last_name  = last
            user.email      = email
            user.save()

            Unit.objects.create(
                name=unit_name,
                order=order,
                officer=user,
                is_active=True,
            )
            self.stdout.write(
                f'  Unit {order}: {unit_name} -> {user.get_full_name()}'
            )

        # ── Academic Sessions ─────────────────────────────────────────────────
        for name, active in [('2024/2025', False), ('2025/2026', True)]:
            session, created = AcademicSession.objects.get_or_create(
                name=name,
                defaults={'is_active': active}
            )
            if created:
                self.stdout.write(f'  Created session: {name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nSeeded successfully.'
            f'\n  Units:    {Unit.objects.count()}'
            f'\n  Officers: '
            f'{User.objects.filter(role="unit_officer").count()}'
            f'\n  Bursary:  '
            f'{User.objects.filter(role="bursary").count()}'
            f'\n  Admin:    '
            f'{User.objects.filter(role="admin").count()}'
        ))