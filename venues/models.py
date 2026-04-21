from django.db import models

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
    
    # Anlık veriler için
    su_an_acik = models.BooleanField(default=True)
    doluluk_orani = models.IntegerField(default=0, help_text="Yüzde olarak doluluk (Örn: 80)")
    
    # Ekstra özellikler (Filtreleme için)
    wifi_var = models.BooleanField(default=False)
    priz_var = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.ad} ({self.kategori})"

# Create your models here.
