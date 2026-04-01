from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import reverse
from users import views as user_views


def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        f'Sitemap: {request.build_absolute_uri(reverse("sitemap_xml"))}',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


def sitemap_xml(request):
    pages = [
        reverse('users:login'),
        reverse('users:register'),
        reverse('users:password_reset'),
    ]
    base_url = request.build_absolute_uri('/').rstrip('/')
    entries = ''.join(
        f'<url><loc>{base_url}{page}</loc></url>'
        for page in pages
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'{entries}'
        '</urlset>'
    )
    return HttpResponse(xml, content_type='application/xml')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),
    path('users/', include('users.urls', namespace='users')),
    path('clinical/', include('clinical.urls', namespace='clinical')),
    path('appointments/', include('appointments.urls', namespace='appointments')),
    path('rooms/', include('rooms.urls', namespace='rooms')),
    path('audit/', include('audit.urls', namespace='audit')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('reviews/', include('reviews.urls', namespace='reviews')),
    path('drug-checker/', include('drug_checker.urls', namespace='drug_checker')),
    path('heart-risk/', include('heart_risk.urls', namespace='heart_risk')),
    path('prescriptions/', include('prescriptions.urls', namespace='prescriptions')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('lab/', include('lab.urls', namespace='lab')),
    path('', user_views.login_view, name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)