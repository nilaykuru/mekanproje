import uuid
import pyotp
from django.db import models
from django.db.models import Avg, Count
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    ROLE_CHOICES = [
        ('USER', 'Kullanıcı (Öneri Alacak)'),
        ('OWNER', 'Mekan Sahibi'),
    ]
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    rol = models.CharField(max_length=10, choices=ROLE_CHOICES, default='USER')
    foto = models.ImageField(upload_to='profil_fotolari/', blank=True, null=True, verbose_name="Profil Fotoğrafı")
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
        ('balikesir', 'Balıkesir'),
    ]

    ad = models.CharField(max_length=100)
    kategori = models.CharField(max_length=20, choices=KATEGORI_SECIMLERI)
    sehir = models.CharField(max_length=20, choices=SEHIR_SECIMLERI, blank=True, null=True, verbose_name="Şehir")
    adres = models.TextField()
    img = models.ImageField(upload_to='mekanlar/', blank=True, null=True, verbose_name="Mekan Fotoğrafı")
    telefon = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    website = models.URLField(blank=True, null=True, verbose_name="Web Sitesi")
    su_an_acik = models.BooleanField(default=True)
    doluluk_orani = models.IntegerField(null=True, blank=True, help_text="Yüzde olarak doluluk (Örn: 80)")
    acilis_saati = models.TimeField(null=True, blank=True, verbose_name="Açılış Saati")
    kapanis_saati = models.TimeField(null=True, blank=True, verbose_name="Kapanış Saati")
    sahibi = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='mekanlari')
    dogrulanmis_mi = models.BooleanField(default=False)
    dogrulama_token = models.UUIDField(default=uuid.uuid4, unique=True)
    anlik_duyuru = models.CharField(max_length=500, blank=True, null=True)

    # Ruhsat ve onay durumu
    ruhsat_belgesi = models.ImageField(upload_to='ruhsatlar/', null=True, blank=True, verbose_name='Ruhsat Belgesi')
    is_approved = models.BooleanField(default=False)

    goruntuleme_sayisi = models.IntegerField(default=0, verbose_name="Görüntülenme Sayısı")

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
    menu_pdf = models.FileField(upload_to='menuler/', blank=True, null=True, verbose_name='Menü PDF')
    menu_foto = models.ImageField(upload_to='menuler/', blank=True, null=True, verbose_name='Menü Fotoğrafı')
    rezervasyon_aktif = models.BooleanField(default=False, verbose_name='Rezervasyon Kabul Et')

    def __str__(self):
        return f"{self.ad} ({self.kategori})"

    @property
    def acik_mi(self):
        import datetime
        now = timezone.localtime()
        bugun = now.weekday()  # 0=Pazartesi, 6=Pazar
        try:
            gun = self.calisma_gunleri.get(gun=bugun)
            if not gun.acik:
                return False
            if gun.acilis and gun.kapanis:
                t = now.time()
                a, k = gun.acilis, gun.kapanis
                return (a <= t <= k) if a <= k else (t >= a or t <= k)
            return True
        except Exception:
            pass
        if self.acilis_saati and self.kapanis_saati:
            t = now.time()
            a, k = self.acilis_saati, self.kapanis_saati
            return (a <= t <= k) if a <= k else (t >= a or t <= k)
        return self.su_an_acik

    @property
    def ortalama_puan(self):
        result = self.yorumlar.filter(puan__isnull=False).aggregate(avg=Avg('puan'))
        avg = result['avg']
        return round(avg, 1) if avg else None

    @property
    def yorum_sayisi(self):
        return self.yorumlar.count()

    def aktif_etkinlikler(self):
        return self.etkinlikler.filter(bitis__gte=timezone.now()).order_by('baslangic')


class MekanFoto(models.Model):
    """Mekana ait ek fotoğraflar (galeri)."""
    mekan = models.ForeignKey(Mekan, on_delete=models.CASCADE, related_name='fotolar')
    foto = models.ImageField(upload_to='mekan_fotolari/', verbose_name="Fotoğraf")
    siralama = models.IntegerField(default=0, verbose_name="Sıralama")
    yuklenme = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['siralama', 'yuklenme']
        verbose_name = "Mekan Fotoğrafı"

    def __str__(self):
        return f"{self.mekan.ad} – Fotoğraf #{self.pk}"


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
    PUAN_SECENEKLERI = [(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')]

    mekan = models.ForeignKey(Mekan, on_delete=models.CASCADE, related_name='yorumlar')
    yazar = models.ForeignKey(User, on_delete=models.CASCADE)
    icerik = models.TextField(verbose_name="Yorumunuz")
    puan = models.IntegerField(
        choices=PUAN_SECENEKLERI,
        null=True, blank=True,
        verbose_name="Puan (1-5)"
    )
    fotoğraf = models.ImageField(upload_to='yorum_fotolari/', null=True, blank=True)
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.yazar.username} - {self.mekan.ad}"


class YorumFoto(models.Model):
    """Bir yoruma ait birden fazla fotoğraf."""
    yorum = models.ForeignKey(Yorum, on_delete=models.CASCADE, related_name='fotolar')
    foto = models.ImageField(upload_to='yorum_fotolari/')
    yuklenme = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['yuklenme']

    def __str__(self):
        return f"Foto – {self.yorum}"


class SifreSifirlamaKodu(models.Model):
    """6 haneli OTP — URL içermez, spam filtrelerini geçer."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sifre_kodlari')
    kod = models.CharField(max_length=6)
    olusturuldu = models.DateTimeField(auto_now_add=True)
    kullanildi = models.BooleanField(default=False)

    class Meta:
        ordering = ['-olusturuldu']

    def gecerli_mi(self):
        from datetime import timedelta
        return (
            not self.kullanildi and
            (timezone.now() - self.olusturuldu) < timedelta(minutes=15)
        )

    def __str__(self):
        return f"{self.user.username} – {self.kod}"


class CalismaGunu(models.Model):
    GUN_SECENEKLERI = [(0,'Pazartesi'),(1,'Salı'),(2,'Çarşamba'),(3,'Perşembe'),(4,'Cuma'),(5,'Cumartesi'),(6,'Pazar')]
    mekan = models.ForeignKey(Mekan, on_delete=models.CASCADE, related_name='calisma_gunleri')
    gun = models.IntegerField(choices=GUN_SECENEKLERI)
    acik = models.BooleanField(default=True)
    acilis = models.TimeField(null=True, blank=True)
    kapanis = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ('mekan', 'gun')
        ordering = ['gun']

    def __str__(self):
        return f"{self.mekan.ad} – {self.get_gun_display()}"


class YorumBegeni(models.Model):
    yorum = models.ForeignKey(Yorum, on_delete=models.CASCADE, related_name='begeniler')
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='begendigi_yorumlar')
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('yorum', 'kullanici')


class Bildirim(models.Model):
    TIP_SECENEKLERI = [
        ('YORUM','Yeni Yorum'),
        ('BEGENI','Beğeni'),
        ('TAKIP','Takipçi'),
        ('ONAY','Mekan Onayı'),
        ('YANIT','Yanıt'),
        ('KAMPANYA','Kampanya'),
        ('REZERVASYON','Rezervasyon'),
        ('DUYURU','Duyuru'),
    ]
    alici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bildirimler')
    gonderen = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='gonderilen_bildirimler')
    tip = models.CharField(max_length=15, choices=TIP_SECENEKLERI)
    mesaj = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    okundu = models.BooleanField(default=False)
    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-olusturuldu']

    def __str__(self):
        return f"{self.alici.username} – {self.tip}"


class Takip(models.Model):
    takipci = models.ForeignKey(User, on_delete=models.CASCADE, related_name='takip_ettikleri')
    takip_edilen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='takipcileri')
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('takipci', 'takip_edilen')

    def __str__(self):
        return f"{self.takipci.username} → {self.takip_edilen.username}"


class MekanListesi(models.Model):
    olusturan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mekan_listeleri')
    ad = models.CharField(max_length=100, verbose_name='Liste Adı')
    aciklama = models.TextField(blank=True, verbose_name='Açıklama')
    mekanlar = models.ManyToManyField(Mekan, related_name='listeler', blank=True)
    herkese_acik = models.BooleanField(default=True, verbose_name='Herkese Açık')
    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-olusturuldu']

    def __str__(self):
        return f"{self.ad} ({self.olusturan.username})"


class YorumYanit(models.Model):
    yorum = models.OneToOneField(Yorum, on_delete=models.CASCADE, related_name='yanit')
    yazan = models.ForeignKey(User, on_delete=models.CASCADE)
    icerik = models.TextField(verbose_name='Yanıt')
    tarih = models.DateTimeField(auto_now_add=True)
    guncellendi = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Yanıt: {self.yazan.username} → {self.yorum}"


class Rezervasyon(models.Model):
    DURUM_SECENEKLERI = [
        ('BEKLIYOR','Bekliyor'),
        ('ONAYLANDI','Onaylandı'),
        ('REDDEDILDI','Reddedildi'),
        ('IPTAL','İptal Edildi'),
    ]
    mekan = models.ForeignKey(Mekan, on_delete=models.CASCADE, related_name='rezervasyonlar')
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rezervasyonlarim')
    tarih = models.DateField(verbose_name='Tarih')
    saat = models.TimeField(verbose_name='Saat')
    kisi_sayisi = models.PositiveIntegerField(default=1, verbose_name='Kişi Sayısı')
    not_mesaj = models.TextField(blank=True, verbose_name='Not')
    durum = models.CharField(max_length=15, choices=DURUM_SECENEKLERI, default='BEKLIYOR')
    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tarih', '-saat']

    def __str__(self):
        return f"{self.kullanici.username} → {self.mekan.ad} ({self.tarih})"


class Kampanya(models.Model):
    mekan = models.ForeignKey(Mekan, on_delete=models.CASCADE, related_name='kampanyalar')
    baslik = models.CharField(max_length=200, verbose_name='Başlık')
    aciklama = models.TextField(verbose_name='Açıklama')
    baslangic = models.DateTimeField(verbose_name='Başlangıç')
    bitis = models.DateTimeField(verbose_name='Bitiş')
    foto = models.ImageField(upload_to='kampanyalar/', blank=True, null=True)
    olusturuldu = models.DateTimeField(auto_now_add=True)

    def aktif_mi(self):
        return self.baslangic <= timezone.now() <= self.bitis

    def __str__(self):
        return f"{self.baslik} @ {self.mekan.ad}"

    class Meta:
        ordering = ['-olusturuldu']
