from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from dashboard.views import (
    home,
    owner_dashboard,
    guest258_admin_dashboard,
    admin_property_approval,
    admin_approve_property,
    admin_reject_property,
    admin_review_approval,
    admin_approve_review,
    admin_reject_review,
    admin_payment_approval,
    admin_booking_list,
    admin_toggle_featured_property,
    admin_confirm_payment,
    admin_reject_payment,
    admin_audit_log_list,
)

from properties import views as property_views
from bookings import views as booking_views
from support import views as support_views
from pages import pwa_views
from pages.health import healthz, readyz


def robots_txt(request):
    content = """User-agent: *
Allow: /

Sitemap: https://258guest.com/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")


def sitemap_xml(request):
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://258guest.com/</loc>
        <priority>1.0</priority>
    </url>
</urlset>
"""
    return HttpResponse(content, content_type="application/xml")


urlpatterns = [
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),

    path('service-worker.js', pwa_views.service_worker, name='service_worker'),
    path('healthz/', healthz, name='healthz'),
    path('readyz/', readyz, name='readyz'),
    path('admin/', admin.site.urls),

    path('', home, name='home'),

    path('', include('accounts.urls')),

    path('properties/', include('properties.urls')),
    path('reservas/', include('bookings.urls')),
    path('reviews/', include('reviews.urls')),
    path('pagamentos/', include('payments.urls')),
    path('notificacoes/', include('notifications.urls')),
    path('suporte/', include('support.urls')),
    path('mensagens/', include('messaging.urls')),
    path('institucional/', include('pages.urls')),
    path('comercial/', include('monetization.urls')),

    path('proprietario/dashboard/', owner_dashboard, name='owner_dashboard'),

    path('proprietario/propriedades/', property_views.owner_property_list, name='owner_property_list'),
    path('proprietario/propriedades/nova/', property_views.owner_property_create, name='owner_property_create'),
    path('proprietario/propriedades/<int:pk>/editar/', property_views.owner_property_edit, name='owner_property_edit'),
    path('proprietario/propriedades/<int:property_id>/preparar/', property_views.owner_property_setup, name='owner_property_setup'),

    path('proprietario/propriedades/<int:property_id>/quartos/', property_views.owner_room_list, name='owner_room_list'),
    path('proprietario/propriedades/<int:property_id>/quartos/novo/', property_views.owner_room_create, name='owner_room_create'),
    path('proprietario/quartos/<int:room_id>/editar/', property_views.owner_room_edit, name='owner_room_edit'),
    path('proprietario/quartos/<int:room_id>/alternar/', property_views.owner_room_toggle, name='owner_room_toggle'),
    path('proprietario/quartos/<int:room_id>/duplicar/', property_views.owner_room_duplicate, name='owner_room_duplicate'),

    path('proprietario/propriedades/<int:property_id>/fotos/', property_views.owner_photo_gallery, name='owner_photo_gallery'),
    path('proprietario/propriedades/<int:property_id>/fotos/nova/', property_views.owner_photo_create, name='owner_photo_create'),
    path('proprietario/fotos/<int:photo_id>/principal/', property_views.owner_photo_set_main, name='owner_photo_set_main'),
    path('proprietario/fotos/<int:photo_id>/apagar/', property_views.owner_photo_delete, name='owner_photo_delete'),

    path('proprietario/propriedades/<int:property_id>/disponibilidade/', booking_views.owner_availability_calendar, name='owner_availability_calendar'),
    path('proprietario/propriedades/<int:property_id>/disponibilidade/events/', booking_views.owner_availability_events, name='owner_availability_events'),
    path('proprietario/propriedades/<int:property_id>/disponibilidade/bloquear/', booking_views.owner_availability_block_create, name='owner_availability_block_create'),
    path('proprietario/disponibilidade/<int:block_id>/apagar/', booking_views.owner_availability_block_delete, name='owner_availability_block_delete'),

    path('258-admin/', guest258_admin_dashboard, name='guest258_admin_dashboard'),

    path('258-admin/propriedades/', admin_property_approval, name='guest258_admin_properties'),
    path('258-admin/propriedades/<int:property_id>/aprovar/', admin_approve_property, name='guest258_admin_approve_property'),
    path('258-admin/propriedades/<int:property_id>/rejeitar/', admin_reject_property, name='guest258_admin_reject_property'),
    path('258-admin/propriedades/<int:property_id>/destaque/', admin_toggle_featured_property, name='guest258_admin_toggle_featured_property'),

    path('258-admin/reservas/', admin_booking_list, name='guest258_admin_bookings'),

    path('258-admin/avaliacoes/', admin_review_approval, name='guest258_admin_reviews'),
    path('258-admin/avaliacoes/<int:review_id>/aprovar/', admin_approve_review, name='guest258_admin_approve_review'),
    path('258-admin/avaliacoes/<int:review_id>/rejeitar/', admin_reject_review, name='guest258_admin_reject_review'),

    path('258-admin/pagamentos/', admin_payment_approval, name='guest258_admin_payments'),
    path('258-admin/pagamentos/<int:payment_id>/confirmar/', admin_confirm_payment, name='guest258_admin_confirm_payment'),
    path('258-admin/pagamentos/<int:payment_id>/rejeitar/', admin_reject_payment, name='guest258_admin_reject_payment'),

    path('258-admin/auditoria/', admin_audit_log_list, name='admin_audit_log_list'),

    path('258-admin/suporte/', support_views.admin_support_ticket_list, name='admin_support_ticket_list'),
    path('258-admin/suporte/<int:ticket_id>/', support_views.admin_support_ticket_detail, name='admin_support_ticket_detail'),
]

if settings.DJANGO_SERVE_MEDIA:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
