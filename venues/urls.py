from django.urls import path
from . import views

urlpatterns = [
    # Kullanıcı İşlemleri
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'), # Asıl mekanlar sayfası burası
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),

    # Mekan ve Filtreleme İşlemleri
    # BURAYI GÜNCELLEDİK: views.index yerine views.dashboard yazdık
    path('index/', views.dashboard, name='index'), 
    
    path('su-an-acik/', views.su_an_acik_olanlar, name='su_an_acik'),
    path('calisma-alanlari/', views.calisma_alanlari, name='calisma_alanlari'),
    path('acil-ihtiyaclar/', views.acil_ihtiyaclar, name='acil_ihtiyaclar'),
    path('favorilerim/', views.favorilerim, name='favorilerim'),
    path('favori-islem/<int:mekan_id>/', views.favori_islem, name='favori_islem'),
    
    path('mekan/<int:mekan_id>/', views.mekan_detay, name='mekan_detay'),
]