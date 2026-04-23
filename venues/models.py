from django.db import models
from django.contrib.auth.models import User # Bunu ekledik

class Mekan(models.Model):
    KATEGORI_SECIMLERI = [
        ('KAFE', 'Kafe'),
        ('KUTUPHANE', 'Kütüphane'),
        ('ECZANE', 'Eczane'),
        ('RESTORAN', 'Restoran'),
    ]

    ad = models.CharField(max_length=100)
    kategori = models.CharField(max_length=20, choices=KATEGORI_SECIMLERI)
    adres = models.TextField()
    img = models.ImageField(upload_to='mekanlar/', blank=True, null=True, verbose_name="Mekan Fotoğrafı")
    
    su_an_acik = models.BooleanField(default=True)
    doluluk_orani = models.IntegerField(default=0, help_text="Yüzde olarak doluluk (Örn: 80)")
    acilis_saati = models.TimeField(null=True, blank=True, verbose_name="Açılış Saati")
    kapanis_saati = models.TimeField(null=True, blank=True, verbose_name="Kapanış Saati")
    
    wifi_var = models.BooleanField(default=False)
    priz_var = models.BooleanField(default=False)
    otopark_var = models.BooleanField(default=False)
    sigara_icin_uygun = models.BooleanField(default=False)
    bahce_var = models.BooleanField(default=False)
    engelli_erisimi_var = models.BooleanField(default=False)
    canli_muzik_var = models.BooleanField(default=False)
    evcil_hayvan_izinli = models.BooleanField(default=False)
    cocuk_oyun_alani_var = models.BooleanField(default=False)

    # FAVORİ ÖZELLİĞİ İÇİN BU SATIRI EKLE:
    favorileyenler = models.ManyToManyField(User, related_name='favori_mekanlar', blank=True)

    def __str__(self):
        return f"{self.ad} ({self.kategori})"

    # venues/models.py içindeki Mekan sınıfının ALTINA ekle:

class Yorum(models.Model):
    mekan = models.ForeignKey(Mekan, on_delete=models.CASCADE, related_name='yorumlar')
    yazar = models.ForeignKey(User, on_delete=models.CASCADE)
    icerik = models.TextField(verbose_name="Yorumunuz")
    fotoğraf = models.ImageField(upload_to='yorum_fotolari/', null=True, blank=True)
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.yazar.username} - {self.mekan.ad}"