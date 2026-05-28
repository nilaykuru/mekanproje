from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('venues.urls')),
    path("__reload__/", include("django_browser_reload.urls")),

    # Şifre sıfırlama (Django built-in views)
    path('sifre/sifirla/', auth_views.PasswordResetView.as_view(
        template_name='venues/password_reset_form.html',
        email_template_name='venues/password_reset_email.txt',
        subject_template_name='venues/password_reset_subject.txt',
    ), name='password_reset'),
    path('sifre/sifirla/gonderildi/', auth_views.PasswordResetDoneView.as_view(
        template_name='venues/password_reset_done.html',
    ), name='password_reset_done'),
    path('sifre/sifirla/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='venues/password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('sifre/sifirla/tamamlandi/', auth_views.PasswordResetCompleteView.as_view(
        template_name='venues/password_reset_complete.html',
    ), name='password_reset_complete'),
]

# BU KISIM LISTENIN TAMAMEN DISINDA OLMALI
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)