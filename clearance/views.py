from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from .models import Unit, ClearanceRequest, Approval

from .notifications import (
    notify_bursary_confirmed,
    notify_unit_approved,
    notify_unit_declined,
    notify_cleared,
    notify_officer,
)

User = get_user_model()


# ── Helpers ───────────────────────────────────────────────────────────────────

def role_required(*roles):
    """Decorator: restrict view to specific roles."""
    from functools import wraps
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, 'Access denied.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def create_approval_records(clearance_request):
    """Create one Approval record per active unit for a request."""
    units = Unit.objects.filter(is_active=True).order_by('order')
    for unit in units:
        # Determine officer for HOD unit
        officer = None
        if unit.name == 'Head of Department':
            dept         = clearance_request.student.department
            hod_username = HOD_ROUTING.get(dept)
            if hod_username:
                try:
                    officer = User.objects.get(username=hod_username)
                except User.DoesNotExist:
                    pass

        Approval.objects.get_or_create(
            request=clearance_request,
            unit=unit,
            defaults={
                'status':  'pending',
                'officer': officer,
            }
        )

    # Set current unit to Library (first unit)
    first_unit = units.first()
    if first_unit:
        clearance_request.current_unit = first_unit
        clearance_request.save(update_fields=['current_unit'])


# Department to HOD username mapping
HOD_ROUTING = {
    'Cyber Security Science':  'hod_cs',
    'Software Engineering':    'hod_cs',
    'Artificial Intelligence': 'hod_ict',
    'Information Technology':  'hod_ict',
}

def advance_workflow(clearance_request):
    """
    Move request forward regardless of declines.
    When all units have acted, determine final status:
    - All approved       → cleared
    - Any declined       → conditional
    Officer can later change declined to approved to upgrade to cleared.
    """
    units     = Unit.objects.filter(is_active=True).order_by('order')
    unit_list = list(units)

    # ── Route HOD approvals first ─────────────────────────────────────────────
    for unit in unit_list:
        try:
            approval = Approval.objects.get(
                request=clearance_request,
                unit=unit
            )
        except Approval.DoesNotExist:
            continue

        if unit.name == 'Head of Department':
            dept         = clearance_request.student.department
            hod_username = HOD_ROUTING.get(dept)
            if hod_username:
                try:
                    hod = User.objects.get(username=hod_username)
                    if approval.officer != hod:
                        approval.officer = hod
                        approval.save(update_fields=['officer'])
                except User.DoesNotExist:
                    pass

    # ── Find the next pending unit and notify its officer ─────────────────────
    next_pending = None
    for unit in unit_list:
        try:
            approval = Approval.objects.get(
                request=clearance_request,
                unit=unit
            )
        except Approval.DoesNotExist:
            continue

        if approval.status == 'pending':
            next_pending = (unit, approval)
            break

    if next_pending:
        unit, approval = next_pending
        clearance_request.current_unit = unit
        clearance_request.save(update_fields=['current_unit'])

        # Notify the officer
        officer = approval.officer or unit.officer
        if officer:
            notify_officer(
                officer=officer,
                student_name=clearance_request.student.get_full_name(),
                unit_name=unit.name
            )
        return

    # ── All units have acted (no more pending) ────────────────────────────────
    clearance_request.current_unit = None

    has_declined = Approval.objects.filter(
        request=clearance_request,
        status='declined'
    ).exists()

    if has_declined:
        clearance_request.status = 'conditional'
        clearance_request.completed_at = timezone.now()
        clearance_request.save()
        # Notify student
        declined_units = Approval.objects.filter(
            request=clearance_request,
            status='declined'
        ).select_related('unit')
        unit_names = ', '.join(
            [a.unit.name for a in declined_units]
        )
        from .notifications import notify
        notify(
            user=clearance_request.student,
            title='Clearance Conditional — Action Required',
            message=(
                f'All units have reviewed your clearance request. '
                f'However, the following unit(s) declined: {unit_names}. '
                f'Please visit the declined unit(s) physically to resolve '
                f'the issue. Once resolved, the officer will update your '
                f'status in the system. Your certificate is available but '
                f'marked as CONDITIONAL until all units approve.'
            )
        )
    else:
        clearance_request.status       = 'cleared'
        clearance_request.completed_at = timezone.now()
        clearance_request.save()
        notify_cleared(clearance_request)


# ── Student Views ─────────────────────────────────────────────────────────────

@login_required
@role_required('student')
def submit_clearance(request):
    from .models import AcademicSession
    # Check if already submitted
    existing = ClearanceRequest.objects.filter(
        student=request.user
    ).first()
    if existing:
        messages.info(
            request,
            'You already have a clearance request. '
            'Track its progress below.'
        )
        return redirect('clearance:status')

    sessions = AcademicSession.objects.filter(is_active=True)

    if request.method == 'POST':
        session_id = request.POST.get('session_id', '').strip()

        if not session_id:
            messages.error(request, 'Please select an academic session.')
            return render(request, 'clearance/submit.html',
                          {'sessions': sessions})

        try:
            from .models import AcademicSession
            selected_session = AcademicSession.objects.get(
                pk=session_id,
                is_active=True
            )
        except AcademicSession.DoesNotExist:
            messages.error(
                request,
                'Selected session is not available. '
                'Contact the administrator.'
            )
            return render(request, 'clearance/submit.html',
                          {'sessions': sessions})

        if not Unit.objects.filter(is_active=True).exists():
            messages.error(
                request,
                'No clearance units configured yet. '
                'Contact the administrator.'
            )
            return render(request, 'clearance/submit.html',
                          {'sessions': sessions})

        cr = ClearanceRequest.objects.create(
            student=request.user,
            session_year=selected_session.name,
            status='pending',
            bursary_confirmed=False,
        )
        create_approval_records(cr)
        messages.success(
            request,
            f'Clearance request submitted for {selected_session.name}. '
            'Awaiting bursary confirmation.'
        )
        return redirect('clearance:status')

    return render(request, 'clearance/submit.html',
                  {'sessions': sessions})


@login_required
@role_required('student')
def clearance_status(request):
    try:
        cr       = ClearanceRequest.objects.get(student=request.user)
        approvals = cr.approvals.select_related('unit', 'officer').all()
        units_total    = approvals.count()
        units_approved = approvals.filter(status='approved').count()
        progress = int((units_approved / units_total) * 100) \
                   if units_total > 0 else 0
        context = {
            'cr':           cr,
            'approvals':    approvals,
            'units_total':  units_total,
            'units_approved': units_approved,
            'progress':     progress,
        }
    except ClearanceRequest.DoesNotExist:
        context = {'cr': None}
    return render(request, 'clearance/status.html', context)


@login_required
@role_required('student')
def download_certificate(request, pk):
    import os
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        Table, TableStyle, HRFlowable, Image
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    cr = get_object_or_404(
    ClearanceRequest,
    pk=pk,
    student=request.user,
    )
    if cr.status not in ['cleared', 'conditional']:
        messages.error(
            request,
            'Certificate is not available yet.'
        )
        return redirect('clearance:status')

    approvals = cr.approvals.select_related(
        'unit', 'officer'
    ).order_by('unit__order')

    # ── Setup response ────────────────────────────────────────────────────────
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="clearance_certificate_'
        f'{cr.student.matric_number.replace("/", "-")}.pdf"'
    )

    # ── Document ──────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=1.5*cm,
        bottomMargin=2*cm,
    )

    # ── Colours ───────────────────────────────────────────────────────────────
    NUM_NAVY  = colors.HexColor('#0b3b6f')
    NUM_GOLD  = colors.HexColor('#d4a017')
    NUM_GREEN = colors.HexColor('#198754')
    LIGHT_BG  = colors.HexColor('#f4f6f9')

    # ── Styles ────────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'title',
        fontSize=20,
        fontName='Helvetica-Bold',
        textColor=NUM_NAVY,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'subtitle',
        fontSize=13,
        fontName='Helvetica-Bold',
        textColor=NUM_GOLD,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    motto_style = ParagraphStyle(
        'motto',
        fontSize=9,
        fontName='Helvetica-Oblique',
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        'body',
        fontSize=11,
        fontName='Helvetica',
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=18,
    )
    label_style = ParagraphStyle(
        'label',
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=NUM_NAVY,
        alignment=TA_LEFT,
    )
    value_style = ParagraphStyle(
        'value',
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.black,
        alignment=TA_LEFT,
    )
    section_style = ParagraphStyle(
        'section',
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=NUM_NAVY,
        alignment=TA_CENTER,
        spaceAfter=6,
        spaceBefore=10,
    )
    footer_style = ParagraphStyle(
        'footer',
        fontSize=8,
        fontName='Helvetica-Oblique',
        textColor=colors.grey,
        alignment=TA_CENTER,
    )

    # ── Build content ─────────────────────────────────────────────────────────
    story = []

    # Logo
    logo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'static', 'images', 'num-logo.webp'
    )
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=3*cm, height=3*cm)
        logo.hAlign = 'CENTER'
        story.append(logo)
        story.append(Spacer(1, 0.3*cm))

    # University name
    story.append(Paragraph('NEWGATE UNIVERSITY MINNA', title_style))
    story.append(Paragraph('Faculty of Computing and Information Technology', motto_style))
    story.append(Paragraph('Explore to Excel', motto_style))
    story.append(Spacer(1, 0.3*cm))

    # Gold line
    story.append(HRFlowable(
        width='100%', thickness=3,
        color=NUM_GOLD, spaceAfter=0.3*cm
    ))

    # Conditional banner
    if cr.status == 'conditional':
        banner_style = ParagraphStyle(
            'banner',
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            alignment=TA_CENTER,
            backColor=colors.HexColor('#dc3545'),
            spaceAfter=8,
            spaceBefore=4,
            borderPadding=8,
        )
        story.append(Paragraph(
            'CONDITIONAL — PENDING PHYSICAL RESOLUTION AT DECLINED UNIT(S)',
            banner_style
        ))

    # Certificate title
    story.append(Paragraph('FINAL-YEAR CLEARANCE CERTIFICATE', subtitle_style))

    # Navy line
    story.append(HRFlowable(
        width='100%', thickness=1,
        color=NUM_NAVY, spaceAfter=0.5*cm
    ))

    # Certify text
    story.append(Paragraph(
        'This is to certify that the following student has successfully '
        'completed all final-year clearance requirements and is approved '
        'for result processing and certificate issuance.',
        body_style
    ))
    story.append(Spacer(1, 0.5*cm))

    # Student details table
    student_data = [
        [Paragraph('Full Name', label_style),
         Paragraph(cr.student.get_full_name(), value_style)],
        [Paragraph('Matric Number', label_style),
         Paragraph(cr.student.matric_number or '—', value_style)],
        [Paragraph('Department', label_style),
         Paragraph(cr.student.department or '—', value_style)],
        [Paragraph('Academic Session', label_style),
         Paragraph(cr.session_year, value_style)],
        [Paragraph('Date Cleared', label_style),
         Paragraph(
             cr.completed_at.strftime('%d %B %Y') if cr.completed_at
             else '—',
             value_style
         )],
    ]

    student_table = Table(
        student_data,
        colWidths=[5*cm, 11*cm]
    )
    student_table.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, -1), LIGHT_BG),
        ('BACKGROUND',  (0, 0), (0, -1), colors.HexColor('#e8f0f8')),
        ('GRID',        (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1),
         [LIGHT_BG, colors.white]),
        ('PADDING',     (0, 0), (-1, -1), 8),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story.append(student_table)
    story.append(Spacer(1, 0.6*cm))

    # Approvals section heading
    story.append(HRFlowable(
        width='100%', thickness=1,
        color=NUM_GOLD, spaceAfter=0.2*cm
    ))
    story.append(Paragraph('UNIT APPROVALS', section_style))
    story.append(HRFlowable(
        width='100%', thickness=1,
        color=NUM_GOLD, spaceAfter=0.3*cm
    ))

    # Approvals table
    approval_header = [
        Paragraph('No.', label_style),
        Paragraph('Unit', label_style),
        Paragraph('Approved By', label_style),
        Paragraph('Date', label_style),
    ]
    approval_rows = [approval_header]

    for i, appr in enumerate(approvals, 1):
        officer_name = (
            appr.officer.get_full_name()
            if appr.officer else '—'
        )
        date_str = (
            appr.actioned_at.strftime('%d %b %Y, %I:%M %p')
            if appr.actioned_at else '—'
        )
        status_text = appr.status.upper()
        if appr.status == 'declined':
            status_text = f'DECLINED — {appr.remarks}'

        approval_rows.append([
            Paragraph(str(i), value_style),
            Paragraph(appr.unit.name, value_style),
            Paragraph(officer_name, value_style),
            Paragraph(
                date_str if appr.status != 'declined'
                else f'DECLINED: {appr.remarks}',
                value_style
            ),
        ])

    approval_table = Table(
        approval_rows,
        colWidths=[1*cm, 5*cm, 6*cm, 5*cm]
    )
    approval_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NUM_NAVY),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 10),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1),
         [colors.white, LIGHT_BG]),
        ('GRID',          (0, 0), (-1, -1),
         0.5, colors.HexColor('#dee2e6')),
        ('PADDING',       (0, 0), (-1, -1), 7),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',         (0, 0), (0, -1), 'CENTER'),
    ]))
    story.append(approval_table)
    story.append(Spacer(1, 0.8*cm))

    # Highlight declined rows in red
    for row_idx, appr in enumerate(approvals, 1):
        if appr.status == 'declined':
            approval_table.setStyle(TableStyle([
                ('BACKGROUND', (0, row_idx), (-1, row_idx),
                colors.HexColor('#f8d7da')),
                ('TEXTCOLOR',  (0, row_idx), (-1, row_idx),
                colors.HexColor('#58151c')),
            ]))

    # Validity notice
    story.append(HRFlowable(
        width='100%', thickness=1,
        color=NUM_NAVY, spaceAfter=0.3*cm
    ))
    story.append(Paragraph(
        'This certificate is computer-generated and is valid without a '
        'physical signature. It may be verified through the Newgate '
        'University Minna Academic Registry.',
        footer_style
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f'Generated on: '
        f'{timezone.now().strftime("%d %B %Y at %I:%M %p")} — '
        f'Newgate University Minna Clearance System',
        footer_style
    ))

    # ── Build PDF ─────────────────────────────────────────────────────────────
    doc.build(story)
    return response


# ── Bursary Views ─────────────────────────────────────────────────────────────

@login_required
@role_required('bursary')
def bursary_list(request):
    pending   = ClearanceRequest.objects.filter(
                  bursary_confirmed=False
                ).select_related('student').order_by('-submitted_at')
    confirmed = ClearanceRequest.objects.filter(
                  bursary_confirmed=True
                ).select_related('student').order_by('-bursary_confirmed_at')
    return render(request, 'clearance/bursary_list.html', {
        'pending':   pending,
        'confirmed': confirmed,
    })


@login_required
@role_required('bursary')
def bursary_confirm(request, pk):
    cr = get_object_or_404(ClearanceRequest, pk=pk)
    if request.method == 'POST':
        cr.bursary_confirmed    = True
        cr.bursary_confirmed_by = request.user
        cr.bursary_confirmed_at = timezone.now()
        cr.save()
        # Advance workflow to first unit
        advance_workflow(cr)
        notify_bursary_confirmed(cr)
        messages.success(
            request,
            f'Payment confirmed for '
            f'{cr.student.get_full_name()}. '
            f'Clearance workflow started.'
        )
    return redirect('clearance:bursary_list')


# ── Unit Officer Views ────────────────────────────────────────────────────────

@login_required
@role_required('unit_officer')
def officer_queue(request):
    try:
        unit = Unit.objects.get(officer=request.user, is_active=True)
        # Standard unit queue
        approvals = Approval.objects.filter(
            unit=unit,
            status='pending',
            request__bursary_confirmed=True
        ).select_related('request__student').order_by(
            'request__submitted_at'
        )
    except Unit.DoesNotExist:
        unit = None
        approvals = Approval.objects.none()

    # HOD officers also see routed approvals assigned to them
    # even if they are not the unit's default officer
    hod_approvals = Approval.objects.filter(
        officer=request.user,
        status='pending',
        request__bursary_confirmed=True,
        unit__name='Head of Department'
    ).select_related('request__student')

    # Merge — avoid duplicates
    if unit and unit.name == 'Head of Department':
        all_approvals = hod_approvals
    elif hod_approvals.exists():
        all_approvals = hod_approvals
    else:
        all_approvals = approvals

    return render(request, 'clearance/officer_queue.html', {
        'unit':      unit,
        'approvals': all_approvals,
    })


@login_required
@role_required('unit_officer')
def officer_history(request):
    try:
        unit = Unit.objects.get(officer=request.user, is_active=True)
    except Unit.DoesNotExist:
        unit = None

    # Include approvals where this officer was the routed HOD officer
    approvals = Approval.objects.filter(
        officer=request.user,
        status__in=['approved', 'declined']
    ).select_related(
        'request__student', 'unit'
    ).order_by('-actioned_at')

    return render(request, 'clearance/officer_history.html', {
        'unit':      unit,
        'approvals': approvals,
    })


@login_required
@role_required('unit_officer')
def officer_action(request, pk):
    approval = get_object_or_404(Approval, pk=pk)

    # Security: officer must either own the unit or be the routed HOD officer
    try:
        unit = Unit.objects.get(officer=request.user, is_active=True)
        is_assigned = (approval.unit == unit)
    except Unit.DoesNotExist:
        unit        = None
        is_assigned = False

    # Allow if they are the routed officer on this approval
    is_routed_officer = (approval.officer == request.user)

    if not is_assigned and not is_routed_officer:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        action  = request.POST.get('action')
        remarks = request.POST.get('remarks', '').strip()

        if action == 'approve':
            approval.status      = 'approved'
            approval.officer     = request.user
            approval.remarks     = remarks
            approval.actioned_at = timezone.now()
            approval.save()
            # Find next unit name for notification
            next_unit = Unit.objects.filter(
                is_active=True,
                order__gt=approval.unit.order
            ).order_by('order').first()
            notify_unit_approved(
                clearance_request=approval.request,
                unit_name=approval.unit.name,
                next_unit_name=next_unit.name if next_unit else None
            )
            advance_workflow(approval.request)
            messages.success(
                request,
                f'Clearance approved for '
                f'{approval.request.student.get_full_name()}.'
            )

        elif action == 'decline':
            if not remarks:
                messages.error(
                    request,
                    'Please provide a reason for declining.'
                )
                return render(
                    request,
                    'clearance/officer_action.html',
                    {'approval': approval}
                )
            approval.status      = 'declined'
            approval.officer     = request.user
            approval.remarks     = remarks
            approval.actioned_at = timezone.now()
            approval.save()

            # Notify student of decline but continue workflow
            notify_unit_declined(
                clearance_request=approval.request,
                unit_name=approval.unit.name,
                remarks=remarks
            )

            # Continue workflow to next unit
            advance_workflow(approval.request)

            messages.warning(
                request,
                f'Clearance declined for '
                f'{approval.request.student.get_full_name()}. '
                f'Workflow continues to remaining units.'
            )

        return redirect('clearance:officer_queue')

    return render(request, 'clearance/officer_action.html', {
        'approval': approval
    })

@login_required
@role_required('unit_officer')
def officer_reverse_decline(request, pk):
    """Allow an officer to change their decline to approved."""
    approval = get_object_or_404(Approval, pk=pk)

    # Security check
    if approval.officer != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if approval.status != 'declined':
        messages.error(
            request,
            'This approval is not declined and cannot be reversed.'
        )
        return redirect('clearance:officer_history')

    if request.method == 'POST':
        remarks = request.POST.get('remarks', '').strip()
        approval.status      = 'approved'
        approval.remarks     = f'[Reversed] {remarks}' if remarks \
                               else '[Reversed after physical resolution]'
        approval.actioned_at = timezone.now()
        approval.save()

        # Check if all units are now approved
        cr = approval.request
        still_declined = Approval.objects.filter(
            request=cr,
            status='declined'
        ).exists()

        still_pending = Approval.objects.filter(
            request=cr,
            status='pending'
        ).exists()

        if not still_declined and not still_pending:
            # Upgrade to fully cleared
            cr.status       = 'cleared'
            cr.completed_at = timezone.now()
            cr.save()
            notify_cleared(cr)
            messages.success(
                request,
                f'{cr.student.get_full_name()} is now fully cleared!'
            )
        elif not still_declined:
            # Still pending at some units but no declines
            cr.status = 'pending'
            cr.save()
            messages.success(
                request,
                f'Decision reversed. '
                f'Workflow continues for '
                f'{cr.student.get_full_name()}.'
            )
        else:
            messages.success(
                request,
                f'Decision reversed successfully.'
            )

        return redirect('clearance:officer_history')

    return render(
        request,
        'clearance/officer_reverse.html',
        {'approval': approval}
    )

# ── Admin Views ───────────────────────────────────────────────────────────────

@login_required
@role_required('admin')
def admin_requests(request):
    status_filter = request.GET.get('status', '')
    requests = ClearanceRequest.objects.select_related(
        'student', 'current_unit'
    ).order_by('-submitted_at')
    if status_filter:
        requests = requests.filter(status=status_filter)
    return render(request, 'clearance/admin_requests.html', {
        'requests':      requests,
        'status_filter': status_filter,
    })


@login_required
@role_required('admin')
def admin_units(request):
    units = Unit.objects.select_related('officer').order_by('order')
    officers = User.objects.filter(role='unit_officer')
    return render(request, 'clearance/admin_units.html', {
        'units':    units,
        'officers': officers,
    })


@login_required
@role_required('admin')
def add_unit(request):
    if request.method == 'POST':
        name     = request.POST.get('name', '').strip()
        order    = request.POST.get('order', '').strip()
        officer_id = request.POST.get('officer')
        if name and order:
            officer = None
            if officer_id:
                officer = User.objects.filter(pk=officer_id).first()
            Unit.objects.create(
                name=name,
                order=int(order),
                officer=officer
            )
            messages.success(request, f'Unit "{name}" added successfully.')
        else:
            messages.error(request, 'Name and order are required.')
    return redirect('clearance:admin_units')


@login_required
@role_required('admin')
def delete_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    unit.delete()
    messages.success(request, f'Unit "{unit.name}" deleted.')
    return redirect('clearance:admin_units')


@login_required
@role_required('admin')
def reports(request):
    from django.db.models import Count
    total     = ClearanceRequest.objects.count()
    cleared   = ClearanceRequest.objects.filter(status='cleared').count()
    pending   = ClearanceRequest.objects.filter(status='pending').count()
    declined  = ClearanceRequest.objects.filter(status='declined').count()
    by_dept   = User.objects.filter(
                  role='student'
                ).values('department').annotate(
                  total=Count('id')
                ).order_by('-total')
    return render(request, 'clearance/reports.html', {
        'total':    total,
        'cleared':  cleared,
        'pending':  pending,
        'declined': declined,
        'by_dept':  by_dept,
        'clear_rate': int((cleared / total) * 100) if total > 0 else 0,
    })

@login_required
@role_required('admin')
def admin_sessions(request):
    from .models import AcademicSession
    sessions = AcademicSession.objects.all()
    return render(request, 'clearance/admin_sessions.html', {
        'sessions': sessions,
    })


@login_required
@role_required('admin')
def add_session(request):
    from .models import AcademicSession
    if request.method == 'POST':
        name      = request.POST.get('name', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        if name:
            session, created = AcademicSession.objects.get_or_create(
                name=name,
                defaults={'is_active': is_active}
            )
            if not created:
                messages.error(
                    request,
                    f'Session {name} already exists.'
                )
            else:
                if is_active:
                    session.is_active = True
                    session.save()
                messages.success(
                    request,
                    f'Session {name} added successfully.'
                )
        else:
            messages.error(request, 'Session name is required.')
    return redirect('clearance:admin_sessions')


@login_required
@role_required('admin')
def activate_session(request, pk):
    from .models import AcademicSession
    if request.method == 'POST':
        session = get_object_or_404(AcademicSession, pk=pk)
        session.is_active = True
        session.save()
        messages.success(
            request,
            f'{session.name} is now the active session.'
        )
    return redirect('clearance:admin_sessions')


@login_required
@role_required('admin')
def delete_session(request, pk):
    from .models import AcademicSession
    if request.method == 'POST':
        session = get_object_or_404(AcademicSession, pk=pk)
        session.delete()
        messages.success(request, f'Session deleted.')
    return redirect('clearance:admin_sessions')

@login_required
def notifications_view(request):
    from .models import Notification
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    # Mark all as read
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'clearance/notifications.html', {
        'notifications': notifications,
    })


@login_required
def mark_notification_read(request, pk):
    from .models import Notification
    notif = get_object_or_404(
        Notification, pk=pk, user=request.user
    )
    notif.is_read = True
    notif.save()
    return redirect('clearance:notifications')