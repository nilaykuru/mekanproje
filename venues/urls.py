from django.urls import path
from . import views

urlpatterns = [
    # Genel sayfalar
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('index/', views.dashboard, name='index'),
    path('arama/', views.arama, name='arama'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),

    # Kullanıcı filtreleri
    path('su-an-acik/', views.su_an_acik_olanlar, name='su_an_acik'),
    path('calisma-alanlari/', views.calisma_alanlari, name='calisma_alanlari'),
    path('acil-ihtiyaclar/', views.acil_ihtiyaclar, name='acil_ihtiyaclar'),
    path('favorilerim/', views.favorilerim, name='favorilerim'),
    path('favori-islem/<int:mekan_id>/', views.favori_islem, name='favori_islem'),

    # Mekan detay
    path('mekan/<int:mekan_id>/', views.mekan_detay, name='mekan_detay'),

    # Mekan sahibi paneli
    path('owner-dashboard/', views.mekan_sahibi_paneli, name='owner_dashboard'),
    path('mekan/olustur/', views.mekan_olustur, name='mekan_olustur'),
    path('mekan/<int:mekan_id>/duzenle/', views.mekan_duzenle, name='mekan_duzenle'),
    path('mekan/<int:mekan_id>/sil/', views.mekan_sil, name='mekan_sil'),
    path('mekan/<int:mekan_id>/durum/', views.durum_guncelle, name='durum_guncelle'),

    # Etkinlik CRUD
    path('mekan/<int:mekan_id>/etkinlik/olustur/', views.etkinlik_olustur, name='etkinlik_olustur'),
    path('etkinlik/<int:etkinlik_id>/duzenle/', views.etkinlik_duzenle, name='etkinlik_duzenle'),
    path('etkinlik/<int:etkinlik_id>/sil/', views.etkinlik_sil, name='etkinlik_sil'),

    # Geriye dönük uyumluluk
    path('mekan/<int:mekan_id>/duyuru/', views.duyuru_guncelle, name='duyuru_guncelle'),
]
