from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Ayarlara erişmek için şart
from django.conf.urls.static import static # Medya dosyalarını servis etmek için şart

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('venues.urls')),
]

# Proje geliştirme aşamasında (DEBUG=True) medya dosyalarını görünür kılar
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)