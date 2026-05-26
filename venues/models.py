import uuid
import pyotp
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    ROLE_CHOICES = [
        ('USER', 'Kullanıcı (Öneri Alacak)'),
        ('OWNER', 'Mekan Sahibi'),
    ]
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    rol = models.CharField(max_length=10, choices=ROLE_CHOICES, default='USER')
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # TOTP 2FA alanları
    totp_secret_key = models.CharField(max_length=32, default='', blank=True, help_text="TOTP gizli anahtarı")
    is_verified = models.BooleanField(default=False, help_text="2FA doğrulama tamamlandı mı?")

    def __str__(self):
        return f"{self.user.username} - {self.rol}"
    
    def generate_totp_secret(self):
        """Yeni bir TOTP gizli anahtarı oluştur ve kaydet."""
        if not self.totp_secret_key:
            self.totp_secret_key = pyotp.random_base32()
            self.save(update_fields=['totp_secret_key'])
        return self.totp_secret_key
    
    def get_totp_uri(self, issuer_name='AnlikMekan'):
        """Google Authenticator tarafından okunabilir URI formatı."""
        if not self.totp_secret_key:
            self.generate_totp_secret()
        totp = pyotp.TOTP(self.totp_secret_key)
        return totp.provisioning_uri(
            name=self.user.email,
            issuer_name=issuer_name
        )
    
    def verify_totp(self, token):
        """Gelen kodu doğrula (6 haneli)."""
        if not self.totp_secret_key:
            return False
        totp = pyotp.TOTP(self.totp_secret_key)
        return totp.verify(token)


class Mekan(models.Model):
    KATEGORI_SECIMLERI = [
        ('KAFE', 'Kafe'),
        ('KUTUPHANE', 'Kütüphane'),
        ('ECZANE', 'Eczane'),
        ('RESTORAN', 'Restoran'),
        ('PUB', 'Pub'),
    ]

    SEHIR_SECIMLERI = [
        ('istanbul', 'İstanbul'),
        ('izmir', 'İzmir'),
        ('samsun', 'Samsun'),
        ('sakarya', 'Sakarya'),
    ]

    ad = models.CharField(max_length=100)
    kategori = models.CharField(max_length=20, choices=KATEGORI_SECIMLERI)
    sehir = models.CharField(max_length=20, choices=SEHIR_SECIMLERI, blank=True, null=True, verbose_name="Şehir")
    adres = models.TextField()
    img = models.ImageField(upload_to='mekanlar/', blank=True, null=True, verbose_name="Mekan Fotoğrafı")
    telefon = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    website = models.URLField(blank=True, null=True, verbose_name="Web Sitesi")
    su_an_acik = models.BooleanField(default=True)
    doluluk_orani = models.IntegerField(default=0, help_text="Yüzde olarak doluluk (Örn: 80)")
    acilis_saati = models.TimeField(null=True, blank=True, verbose_name="Açılış Saati")
    kapanis_saati = models.TimeField(null=True, blank=True, verbose_name="Kapanış Saati")
    sahibi = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='mekanlari')
    dogrulanmis_mi = models.BooleanField(default=False)
    dogrulama_token = models.UUIDField(default=uuid.uuid4, unique=True)
    anlik_duyuru = models.CharField(max_length=500, blank=True, null=True)

    # Ruhsat ve onay durumu
    ruhsat_belgesi = models.ImageField(upload_to='ruhsatlar/', null=True, blank=True, verbose_name='Ruhsat Belgesi')
    is_approved = models.BooleanField(default=False)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    wifi_var = models.BooleanField(default=False)
    priz_var = models.BooleanField(default=False)
    otopark_var = models.BooleanField(default=False)
    sigara_icin_uygun = models.BooleanField(default=False)
    bahce_var = models.BooleanField(default=False)
    engelli_erisimi_var = models.BooleanField(default=False)
    canli_muzik_var = models.BooleanField(default=False)
    evcil_hayvan_izinli = models.BooleanField(default=False)
    cocuk_oyun_alani_var = models.BooleanField(default=False)
    favorileyenler = models.ManyToManyField(User, related_name='favori_mekanlar', blank=True)

    def __str__(self):
        return f"{self.ad} ({self.kategori})"

    def aktif_etkinlikler(self):
        return self.etkinlikler.filter(bitis__gte=timezone.now()).order_by('baslangic')


class Etkinlik(models.Model):
    mekan = models.ForeignKey(Mekan, on_delete=models.CASCADE, related_name='etkinlikler')
    baslik = models.CharField(max_length=200, verbose_name="Etkinlik Başlığı")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    baslangic = models.DateTimeField(verbose_name="Başlangıç")
    bitis = models.DateTimeField(verbose_name="Bitiş")
    foto = models.ImageField(upload_to='etkinlikler/', blank=True, null=True, verbose_name="Afiş / Fotoğraf")
    olusturulma = models.DateTimeField(auto_now_add=True)

    def aktif_mi(self):
        return self.bitis >= timezone.now()

    def __str__(self):
        return f"{self.baslik} @ {self.mekan.ad}"


class Yorum(models.Model):
    mekan = models.ForeignKey(Mekan, on_delete=models.CASCADE, related_name='yorumlar')
    yazar = models.ForeignKey(User, on_delete=models.CASCADE)
    icerik = models.TextField(verbose_name="Yorumunuz")
    fotoğraf = models.ImageField(upload_to='yorum_fotolari/', null=True, blank=True)
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.yazar.username} - {self.mekan.ad}"
