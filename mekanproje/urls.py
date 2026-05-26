from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('venues.urls')),
    path("__reload__/", include("django_browser_reload.urls")),
]

# BU KISIM LISTENIN TAMAMEN DISINDA OLMALI
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)