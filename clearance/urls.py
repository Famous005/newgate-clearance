from django.urls import path
from . import views

app_name = 'clearance'

urlpatterns = [
    # Student
    path('submit/',
         views.submit_clearance,    name='submit'),
    path('status/',
         views.clearance_status,    name='status'),
    path('certificate/<int:pk>/',
         views.download_certificate, name='download_certificate'),

    # Bursary
    path('bursary/',
         views.bursary_list,        name='bursary_list'),
    path('bursary/confirm/<int:pk>/',
         views.bursary_confirm,     name='bursary_confirm'),

    # Unit Officer
    path('officer/queue/',
         views.officer_queue,       name='officer_queue'),
    path('officer/history/',
         views.officer_history,     name='officer_history'),
    path('officer/action/<int:pk>/',
         views.officer_action,      name='officer_action'),

    # Admin
    path('admin/requests/',
         views.admin_requests,      name='admin_requests'),
    path('admin/units/',
         views.admin_units,         name='admin_units'),
    path('admin/units/add/',
         views.add_unit,            name='add_unit'),
    path('admin/units/delete/<int:pk>/',
         views.delete_unit,         name='delete_unit'),
    path('reports/',
         views.reports,             name='reports'),

    # Sessions
    path('admin/sessions/',
         views.admin_sessions,     name='admin_sessions'),
    path('admin/sessions/add/',
         views.add_session,        name='add_session'),
    path('admin/sessions/activate/<int:pk>/',
         views.activate_session,   name='activate_session'),
    path('admin/sessions/delete/<int:pk>/',
         views.delete_session,     name='delete_session'),

     # Notifications
    path('notifications/',
         views.notifications_view,       name='notifications'),
    path('notifications/read/<int:pk>/',
         views.mark_notification_read,   name='mark_read'),
]
