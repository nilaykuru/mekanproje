# ──────────────────────────────────────────────────────────────────────────────
#  KURULUM TALİMATI
#  Bu dosyayı kopyalayıp "local_settings.py" olarak kaydet:
#
#      cp config/local_settings.example.py config/local_settings.py
#
#  Ardından aşağıdaki değerleri kendi bilgilerinle doldur.
#  local_settings.py git'e commit EDİLMEZ (.gitignore'da kayıtlı).
# ──────────────────────────────────────────────────────────────────────────────

# ── E-posta (Gmail SMTP) ──────────────────────────────────────────────────────
#
#  Gmail App Password oluşturmak için:
#  1. https://myaccount.google.com/security → "2 Adımlı Doğrulama"yı aktif et
#  2. Arama çubuğuna "Uygulama şifreleri" yaz → Posta / Windows → Oluştur
#  3. 16 haneli şifreyi EMAIL_HOST_PASSWORD'e yapıştır (boşluksuz)
#
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = 'nilaykr11@gmail.com'
EMAIL_HOST_PASSWORD = 'xkiquedhtokfwbfm'
DEFAULT_FROM_EMAIL  = 'AnlıkMekan <nilaykr11@gmail.com>'

# ── Geliştirme ortamı (isteğe bağlı) ─────────────────────────────────────────
# DEBUG = True
# SECRET_KEY = 'gelistirme-icin-gecici-anahtar'
