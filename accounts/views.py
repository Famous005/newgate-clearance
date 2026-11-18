from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import LoginForm, RegisterForm, ProfileUpdateForm

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(
                request,
                f'Welcome back, {user.get_full_name() or user.username}.'
            )
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'
            user.save()
            login(request, user)
            messages.success(request, 'Account created successfully. Welcome!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard_view(request):
    from clearance.models import ClearanceRequest, Approval, Unit
    from django.utils import timezone
    context = {}

    # ── Student ───────────────────────────────────────────────────────────────
    if request.user.is_student:
        try:
            cr = ClearanceRequest.objects.get(student=request.user)
            approvals      = cr.approvals.select_related('unit').all()
            units_total    = approvals.count()
            units_approved = approvals.filter(status='approved').count()
            units_pending  = approvals.filter(status='pending').count()
            progress_percent = int((units_approved / units_total) * 100) \
                               if units_total > 0 else 0

            if cr.status == 'cleared':
                status_display = 'Cleared'
            elif cr.status == 'declined':
                status_display = 'Declined'
            elif not cr.bursary_confirmed:
                status_display = 'Awaiting Bursary'
            else:
                status_display = 'In Progress'

            context.update({
                'clearance_request': cr,
                'approvals':         approvals,
                'units_total':       units_total,
                'units_approved':    units_approved,
                'units_pending':     units_pending,
                'progress_percent':  progress_percent,
                'request_status':    status_display,
            })
        except ClearanceRequest.DoesNotExist:
            context['clearance_request'] = None

    # ── Bursary ───────────────────────────────────────────────────────────────
    elif request.user.is_bursary:
        today         = timezone.now().date()
        all_requests  = ClearanceRequest.objects.all()
        total         = all_requests.count()
        pending_count = all_requests.filter(
                          bursary_confirmed=False
                        ).count()
        confirmed_today = all_requests.filter(
                            bursary_confirmed=True,
                            bursary_confirmed_at__date=today
                          ).count()
        context.update({
            'pending_count':   pending_count,
            'confirmed_count': confirmed_today,
            'total_count':     total,
        })

    # ── Unit Officer ──────────────────────────────────────────────────────────
    elif request.user.is_unit_officer:
        try:
            assigned_unit = Unit.objects.get(
                officer=request.user,
                is_active=True
            )
        except Unit.DoesNotExist:
            assigned_unit = None

        # Pending: either assigned unit queue or HOD routed approvals
        if assigned_unit and assigned_unit.name == 'Head of Department':
            pending_approvals = Approval.objects.filter(
                officer=request.user,
                status='pending',
                request__bursary_confirmed=True
            ).select_related('request__student')
        elif assigned_unit:
            pending_approvals = Approval.objects.filter(
                unit=assigned_unit,
                status='pending',
                request__bursary_confirmed=True
            ).select_related('request__student')
        else:
            # HOD ict case — not default unit officer
            pending_approvals = Approval.objects.filter(
                officer=request.user,
                status='pending',
                request__bursary_confirmed=True
            ).select_related('request__student')

        context.update({
            'assigned_unit':     assigned_unit,
            'pending_approvals': pending_approvals,
            'my_pending':  pending_approvals.count(),
            'my_approved': Approval.objects.filter(
                             officer=request.user,
                             status='approved'
                           ).count(),
            'my_declined': Approval.objects.filter(
                             officer=request.user,
                             status='declined'
                           ).count(),
        })

    # ── Admin ─────────────────────────────────────────────────────────────────
    elif request.user.is_admin_user:
        recent = ClearanceRequest.objects.select_related(
                   'student'
                 ).order_by('-submitted_at')[:10]
        context.update({
            'total_students':  User.objects.filter(role='student').count(),
            'cleared_count':   ClearanceRequest.objects.filter(
                                 status='cleared').count(),
            'pending_count':   ClearanceRequest.objects.filter(
                                 status='pending').count(),
            'declined_count':  ClearanceRequest.objects.filter(
                                 status='declined').count(),
            'recent_requests': recent,
        })

    return render(request, 'clearance/dashboard.html', context)


@login_required
def profile_view(request):
    form = ProfileUpdateForm(
        request.POST or None,
        instance=request.user
    )
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def manage_users_view(request):
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    users = User.objects.all().order_by('role', 'last_name')
    return render(request, 'accounts/manage_users.html', {'users': users})