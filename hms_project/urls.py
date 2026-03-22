from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
    path('clinical/', include('clinical.urls', namespace='clinical')),
    path('appointments/', include('appointments.urls', namespace='appointments')),
    path('rooms/', include('rooms.urls', namespace='rooms')),
    path('audit/', include('audit.urls', namespace='audit')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('reviews/', include('reviews.urls', namespace='reviews')),
    path('prescriptions/', include('prescriptions.urls', namespace='prescriptions')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('lab/', include('lab.urls', namespace='lab')),
    path('', lambda request: redirect('users:login'), name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)