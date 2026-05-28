# 📍 Anlık Mekan

Türkiye'deki kafe, restoran, kütüphane ve diğer mekânların anlık durumunu, etkinliklerini ve kampanyalarını keşfetmeye yarayan tam kapsamlı bir Django web uygulaması.

---

## 🖼️ Özellikler

### 👤 Kullanıcılar İçin
| Özellik | Açıklama |
|---------|----------|
| 🔍 Mekan Keşfi | Şehir, kategori ve 8 özellik filtresiyle arama |
| 🗺️ İnteraktif Harita | Leaflet.js tabanlı harita, anlık açık/kapalı pinleri |
| ❤️ Favori & Liste | Mekan favorileme, kişisel listeler oluşturma |
| 💬 Yorum & Puan | Yorum yazma, fotoğraf ekleme, yorum beğenme |
| 👥 Takip | Mekan sahiplerini takip et, takipçi akışı |
| 📅 Etkinlik Takvimi | FullCalendar.js ile aylık/haftalık etkinlik görünümü |
| 🔔 Bildirimler | Anlık bildirim merkezi, navbar'da okunmamış sayacı |
| 📋 Rezervasyon | Online masa/yer rezervasyonu |
| 🌓 Karanlık Mod | Sistem temasına göre otomatik, manuel geçiş |

### 🏪 Mekan Sahipleri İçin
| Özellik | Açıklama |
|---------|----------|
| 📊 İstatistik Paneli | Chart.js ile haftalık görüntüleme, puan dağılımı grafikleri |
| 🕐 Çalışma Saatleri | Gün bazlı açık/kapalı + saat + 24 saat açık, toplu kopyalama |
| 📢 Anlık Duyuru | Takipçilere push bildirim gönderme |
| 🎯 Kampanya | Özel indirim ve kampanya ilanları |
| 📋 Menü Yönetimi | PDF veya fotoğraf olarak menü yükleme, QR kod |
| 🗓️ Etkinlik | Etkinlik oluşturma ve takvime ekleme |
| 💬 Yorum Yanıtlama | Müşteri yorumlarına işletmeci cevabı |
| 📷 Galeri | Çoklu mekan fotoğrafı yükleme |

### 🔐 Güvenlik & Kimlik
- OTP tabanlı şifre sıfırlama (6 haneli kod, e-posta ile)
- TOTP iki faktörlü doğrulama (pyotp)
- Rol tabanlı erişim kontrolü (`USER` / `OWNER`)
- Admin paneli ruhsat belgesi doğrulama sistemi

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Backend | Django 5.2 |
| Veritabanı | SQLite (geliştirme) |
| Harita | Leaflet.js |
| Takvim | FullCalendar.js 6 |
| Grafikler | Chart.js |
| E-posta | Gmail SMTP |
| 2FA | PyOTP (TOTP) |
| QR Kod | qrcode |
| Görseller | Pillow |

---

## 🚀 Kurulum

### 1. Repoyu klonla

```bash
git clone https://github.com/kullanici-adi/mekanproje-1.git
cd mekanproje-1
```

### 2. Sanal ortam oluştur ve bağımlılıkları kur

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. E-posta ayarlarını yapılandır

```bash
# Örnek dosyayı kopyala
cp config/local_settings.example.py config/local_settings.py
```

`config/local_settings.py` dosyasını aç ve kendi Gmail bilgilerini gir:

```python
EMAIL_HOST_USER     = 'senin@gmail.com'
EMAIL_HOST_PASSWORD = 'uygulama-sifresi-16-hane'
```

> **Gmail Uygulama Şifresi:** [Google Hesabım → Güvenlik → 2 Adımlı Doğrulama → Uygulama Şifreleri](https://myaccount.google.com/security)

### 4. Veritabanını oluştur

```bash
python manage.py migrate
```

### 5. (İsteğe bağlı) Örnek veri yükle

```bash
python manage.py veri_yukle
```

### 6. Süper kullanıcı oluştur

```bash
python manage.py createsuperuser
```

### 7. Sunucuyu başlat

```bash
python manage.py runserver
```

Uygulama `http://127.0.0.1:8000` adresinde çalışmaya başlar.

---

## 📁 Proje Yapısı

```
mekanproje-1/
├── config/
│   ├── settings.py               # Ana ayarlar
│   ├── local_settings.py         # 🔒 Gizli ayarlar (git'e girmez)
│   ├── local_settings.example.py # Örnek şablon (git'e girer)
│   └── urls.py
├── venues/
│   ├── models.py                 # 15 model
│   ├── views.py                  # Tüm view'lar
│   ├── urls.py                   # URL yönlendirme
│   ├── forms.py                  # Form sınıfları
│   ├── templates/venues/         # HTML şablonlar
│   ├── management/commands/      # Yönetim komutları
│   └── migrations/               # Veritabanı migration'ları
├── media/                        # Kullanıcı yüklemeleri (git'e girmez)
├── fixtures/                     # Örnek veri
├── requirements.txt
└── manage.py
```

---

## 🗂️ Veri Modelleri

```
Profile       → Kullanıcı rolü (USER / OWNER), profil fotoğrafı, 2FA
Mekan         → Mekan bilgileri, konum, özellikler
├── MekanFoto       → Galeri fotoğrafları
├── CalismaGunu     → Günlük çalışma saatleri (0=Pzt … 6=Paz)
├── Etkinlik        → Takvim etkinlikleri
├── Kampanya        → İndirim/kampanya ilanları
└── Goruntuleme     → Ziyaret sayacı

Yorum         → Kullanıcı yorumları + puan (1–5)
├── YorumFoto       → Yorum fotoğrafları
├── YorumBegeni     → Beğeni
└── YorumYanit      → İşletmeci yanıtı

Takip         → Kullanıcı → mekan sahibi takip
Bildirim      → Uygulama içi bildirimler
MekanListesi  → Kişisel mekan listeleri
Rezervasyon   → Online rezervasyon
SifreSifirlamaKodu → OTP şifre sıfırlama
```

---

## 🔑 Önemli URL'ler

| URL | Açıklama |
|-----|----------|
| `/` | Landing page |
| `/mekanlar/` | Mekan listesi + filtreler |
| `/harita/` | İnteraktif harita |
| `/populer/` | Popüler mekanlar |
| `/takvim/` | Etkinlik takvimi |
| `/profil/` | Kullanıcı profili |
| `/listelerim/` | Kişisel listeler |
| `/rezervasyonlarim/` | Rezervasyonlarım |
| `/bildirimler/` | Bildirim merkezi |
| `/panel/` | Mekan sahibi paneli |
| `/admin/` | Django admin paneli |
| `/sifre-sifirla/` | OTP şifre sıfırlama |

---

## ⚙️ Ortam Değişkenleri / Gizli Ayarlar

`config/local_settings.py` dosyası git'e **commit edilmez**. Bu dosyada şunlar bulunur:

```python
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = '...'   # Gmail adresi
EMAIL_HOST_PASSWORD = '...'   # Gmail uygulama şifresi
DEFAULT_FROM_EMAIL  = EMAIL_HOST_USER
```

> Şablon dosyası: `config/local_settings.example.py`

---

## 🤝 Katkı Sağlayanlar

| Geliştirici | Katkı |
|-------------|-------|
| [Nilay](https://github.com/nilaykr) | Proje mimarisi, UI/UX, tüm özellikler |
| [Elif Güven](https://github.com/ElifGuvenn) | Admin paneli, ruhsat sistemi, QR kod |

---

## 📄 Lisans

Bu proje MIT lisansı altında dağıtılmaktadır.
