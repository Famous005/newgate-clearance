from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views

urlpatterns = [
    path('admin/',     admin.site.urls),
    path('accounts/',  include('accounts.urls')),
    path('clearance/', include('clearance.urls')),
    path('dashboard/', account_views.dashboard_view, name='dashboard'),
    path('',           account_views.login_view,     name='login'),
    path('logout/',    account_views.logout_view,    name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)