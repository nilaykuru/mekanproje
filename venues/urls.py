from django.urls import path
from . import views

urlpatterns = [
    # Genel sayfalar
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('index/', views.dashboard, name='index'),
    path('arama/', views.arama, name='arama'),
    path('arama/api/', views.arama_api, name='arama_api'),
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
    path('mekan/<int:mekan_id>/takip/', views.mekan_takip, name='mekan_takip'),

    # Etkinlik CRUD
    path('mekan/<int:mekan_id>/etkinlik/olustur/', views.etkinlik_olustur, name='etkinlik_olustur'),
    path('etkinlik/<int:etkinlik_id>/duzenle/', views.etkinlik_duzenle, name='etkinlik_duzenle'),
    path('etkinlik/<int:etkinlik_id>/sil/', views.etkinlik_sil, name='etkinlik_sil'),

    # Hesap e-posta doğrulama
    path('hesap/dogrula/<uuid:token>/', views.hesap_dogrula, name='hesap_dogrula'),
    path('hesap/dogrulama-gonder/', views.hesap_dogrulama_yeniden_gonder, name='hesap_dogrulama_gonder'),

    # TOTP 2FA QR Kod doğrulama (yeni sistem)
    path('2fa/qr-kod/', views.qr_kod_olustur, name='qr_kod_olustur'),
    path('2fa/qr-kod-dogrula/', views.qr_kod_dogrula, name='qr_kod_dogrula'),

    # Gizli yetkili admin sayfaları
    path('yetkili-giris/', views.admin_login, name='admin_login'),
    path('degerlendirme-paneli/', views.admin_panel, name='admin_panel'),
    path('degerlendirme/onayla/<int:mekan_id>/', views.admin_approve, name='admin_approve'),
    path('degerlendirme/reddet/<int:mekan_id>/', views.admin_reject, name='admin_reject'),

    # Geriye dönük uyumluluk
    path('mekan/<int:mekan_id>/duyuru/', views.duyuru_guncelle, name='duyuru_guncelle'),

    # Profil
    path('profil/', views.profil, name='profil'),

    # Harita
    path('harita/', views.mekan_harita, name='mekan_harita'),

    # Yorum düzenle / sil
    path('yorum/<int:yorum_id>/sil/', views.yorum_sil, name='yorum_sil'),
    path('yorum/<int:yorum_id>/duzenle/', views.yorum_duzenle, name='yorum_duzenle'),
    path('yorum/foto/<int:foto_id>/sil/', views.yorum_foto_sil, name='yorum_foto_sil'),

    # Mekan galerisi (çoklu fotoğraf)
    path('mekan/<int:mekan_id>/foto/yukle/', views.mekan_foto_yukle, name='mekan_foto_yukle'),
    path('mekan/foto/<int:foto_id>/sil/', views.mekan_foto_sil, name='mekan_foto_sil'),

    # OTP şifre sıfırlama (URL'siz, Outlook uyumlu)
    path('sifremi-sifirla/', views.sifre_sifirla_talep, name='sifre_sifirla_talep'),
    path('sifremi-sifirla/kod/', views.sifre_sifirla_kod, name='sifre_sifirla_kod'),

    # Bildirimler
    path('bildirimler/', views.bildirimler, name='bildirimler'),
    path('bildirim/sayi/', views.bildirim_okundu_isle, name='bildirim_sayi'),

    # Yorum beğeni
    path('yorum/<int:yorum_id>/begen/', views.yorum_begen, name='yorum_begen'),

    # Takip
    path('kullanici/<int:kullanici_id>/takip/', views.kullanici_takip, name='kullanici_takip'),
    path('kullanici/<int:kullanici_id>/', views.kullanici_profil, name='kullanici_profil'),

    # Listeler
    path('listelerim/', views.listelerim, name='listelerim'),
    path('liste/<int:liste_id>/', views.liste_detay, name='liste_detay'),
    path('liste/<int:liste_id>/ekle/<int:mekan_id>/', views.liste_mekan_ekle, name='liste_mekan_ekle'),
    path('liste/<int:liste_id>/cikar/<int:mekan_id>/', views.liste_mekan_cikar, name='liste_mekan_cikar'),
    path('liste/<int:liste_id>/sil/', views.liste_sil, name='liste_sil'),

    # Yorum yanıt
    path('yorum/<int:yorum_id>/yanit/', views.yorum_yanit, name='yorum_yanit'),

    # Rezervasyon
    path('mekan/<int:mekan_id>/rezervasyon/', views.rezervasyon_olustur, name='rezervasyon_olustur'),
    path('rezervasyonlarim/', views.rezervasyonlarim, name='rezervasyonlarim'),
    path('rezervasyon/<int:rezervasyon_id>/guncelle/', views.rezervasyon_guncelle, name='rezervasyon_guncelle'),
    path('rezervasyon/<int:rezervasyon_id>/iptal/', views.rezervasyon_iptal, name='rezervasyon_iptal'),

    # Kampanya
    path('mekan/<int:mekan_id>/kampanya/olustur/', views.kampanya_olustur, name='kampanya_olustur'),
    path('kampanya/<int:kampanya_id>/sil/', views.kampanya_sil, name='kampanya_sil'),

    # Menü
    path('mekan/<int:mekan_id>/menu/', views.menu_yukle, name='menu_yukle'),

    # Çalışma saatleri
    path('mekan/<int:mekan_id>/calisma-saatleri/', views.calisma_saatleri_duzenle, name='calisma_saatleri_duzenle'),

    # Duyuru (takipçilere)
    path('mekan/<int:mekan_id>/duyuru/yayinla/', views.duyuru_yayinla, name='duyuru_yayinla'),

    # Popüler
    path('populer/', views.populer_mekanlar, name='populer_mekanlar'),

    # Etkinlik takvimi
    path('etkinlikler/takvim/', views.etkinlik_takvimi, name='etkinlik_takvimi'),
]
