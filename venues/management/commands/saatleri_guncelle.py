"""
Mevcut mekanlara OpenStreetMap'ten çalışma saatlerini çeker ve günceller.
Kullanım:
    python manage.py saatleri_guncelle
    python manage.py saatleri_guncelle --sehir istanbul izmir
    python manage.py saatleri_guncelle --hepsini  (zaten saati olanları da güncelle)
"""
import json
import re
import time as time_module
from datetime import time
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError

from django.core.management.base import BaseCommand
from venues.models import Mekan


OVERPASS_URL = 'https://overpass-api.de/api/interpreter'

AMENITY_MAP = {
    'KAFE':      'cafe',
    'RESTORAN':  'restaurant',
    'KUTUPHANE': 'library',
    'ECZANE':    'pharmacy',
    'PUB':       'pub',
}


# ── OSM opening_hours parser ──────────────────────────────────────────────────

def parse_opening_hours(oh_str):
    """
    OSM opening_hours formatını (acilis_saati, kapanis_saati) ikilisine çevirir.
    Örnekler:
        "Mo-Su 08:00-22:00"       → (time(8,0),  time(22,0))
        "24/7"                    → (time(0,0),  time(23,59))
        "Mo-Fr 09:00-20:00"       → (time(9,0),  time(20,0))
        "Mo-Su 09:00-22:00; PH off" → (time(9,0), time(22,0))
    Ayrıştırılamazsa (None, None) döner.
    """
    if not oh_str:
        return None, None

    oh_str = oh_str.strip()

    if oh_str in ('24/7', '24hours', 'open 24/7'):
        return time(0, 0), time(23, 59)

    # İlk HH:MM-HH:MM veya H:MM-H:MM kalıbını bul
    # Not: OSM'de "24:00" = gece yarısı kapanış → 23:59 olarak ele al
    pattern = r'(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})'
    match = re.search(pattern, oh_str)
    if match:
        h1, m1, h2, m2 = (int(match.group(i)) for i in range(1, 5))
        # 24:00 → 23:59 (gece yarısı kapanışı)
        if h2 == 24:
            h2, m2 = 23, 59
        # 25:00, 26:00 vb. → gece yarısını geçen saatler (02:00, 03:00)
        if h2 > 24:
            h2 = h2 - 24
        try:
            return time(h1, m1), time(h2, m2)
        except ValueError:
            pass

    return None, None


# ── Overpass arama ────────────────────────────────────────────────────────────

def _overpass_isle(sorgu, deneme=3, bekleme=4):
    """Overpass sorgusunu retry mantığıyla çalıştır."""
    veri = urlencode({'data': sorgu}).encode()
    istek = Request(OVERPASS_URL, data=veri, headers={'User-Agent': 'AnlikMekan/1.0'})
    for i in range(deneme):
        try:
            with urlopen(istek, timeout=25) as yanit:
                return json.loads(yanit.read().decode()).get('elements', [])
        except (URLError, json.JSONDecodeError, TimeoutError, OSError):
            if i < deneme - 1:
                time_module.sleep(bekleme * (i + 1))   # 4s, 8s, 12s
    return []


def osm_koordinat_ara(amenity, lat, lon, yaricap=200):
    """Verilen koordinat çevresinde belirli türde POI sorgular."""
    sorgu = f"""
[out:json][timeout:20];
node["amenity"="{amenity}"](around:{yaricap},{lat},{lon});
out 5;
"""
    return _overpass_isle(sorgu)


def osm_isimle_ara(amenity, isim, sehir_lat, sehir_lon, yaricap=4000):
    """İsim + şehir merkezi bazlı Overpass sorgusu (koordinat yoksa)."""
    isim_temiz = isim.replace("'", "\\'").replace('"', '')
    sorgu = f"""
[out:json][timeout:20];
node["amenity"="{amenity}"]["name"~"{isim_temiz}",i](around:{yaricap},{sehir_lat},{sehir_lon});
out 3;
"""
    return _overpass_isle(sorgu)


SEHIR_KOORDINAT = {
    'istanbul': (41.0082, 28.9784),
    'izmir':    (38.4192, 27.1287),
    'samsun':   (41.2928, 36.3313),
    'sakarya':  (40.7731, 30.3944),
}


# ── Django management command ─────────────────────────────────────────────────

class Command(BaseCommand):
    help = 'OpenStreetMap opening_hours verisini çekerek mekanlara çalışma saati atar.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sehir', nargs='+',
            default=list(SEHIR_KOORDINAT.keys()),
            help='Güncellenecek şehirler',
        )
        parser.add_argument(
            '--hepsini', action='store_true',
            help='Zaten saati olanları da yeniden sorgula',
        )
        parser.add_argument(
            '--limit', type=int, default=0,
            help='Güncelleme limiti (0 = sınırsız)',
        )

    def handle(self, *args, **options):
        sehirler   = options['sehir']
        hepsini    = options['hepsini']
        limit      = options['limit']

        qs = Mekan.objects.filter(sehir__in=sehirler, is_approved=True)
        if not hepsini:
            qs = qs.filter(acilis_saati__isnull=True)  # sadece saati olmayanlar

        toplam   = qs.count()
        guncellenen = 0
        bulunamayan = 0

        self.stdout.write(f'\n{toplam} mekan işlenecek (--hepsini: {hepsini})\n')

        for i, mekan in enumerate(qs.iterator(), 1):
            if limit and guncellenen >= limit:
                break

            amenity = AMENITY_MAP.get(mekan.kategori)
            if not amenity:
                continue

            ad_goster = mekan.ad[:40].encode('ascii', errors='replace').decode('ascii')
            self.stdout.write(f'[{i}/{toplam}] {ad_goster:<40}', ending=' ')

            try:
                # 1. Koordinat varsa — yakın çevrede ara
                elements = []
                if mekan.latitude and mekan.longitude:
                    elements = osm_koordinat_ara(
                        amenity, float(mekan.latitude), float(mekan.longitude), yaricap=150
                    )

                # 2. Koordinat yoksa — isimle şehir merkezinde ara
                if not elements and mekan.sehir in SEHIR_KOORDINAT:
                    slat, slon = SEHIR_KOORDINAT[mekan.sehir]
                    elements = osm_isimle_ara(amenity, mekan.ad, slat, slon)
            except Exception:
                elements = []

            # OSM kaydından opening_hours bul
            oh_str = None
            for el in elements:
                oh = el.get('tags', {}).get('opening_hours')
                if oh:
                    oh_str = oh
                    break

            if oh_str:
                acilis, kapanis = parse_opening_hours(oh_str)
                if acilis and kapanis:
                    mekan.acilis_saati  = acilis
                    mekan.kapanis_saati = kapanis
                    mekan.save(update_fields=['acilis_saati', 'kapanis_saati'])
                    guncellenen += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'[OK] {oh_str[:30]} -> {acilis:%H:%M}-{kapanis:%H:%M}')
                    )
                else:
                    bulunamayan += 1
                    self.stdout.write(self.style.WARNING(f'[?] Ayristirilamadi: {oh_str[:35]}'))
            else:
                bulunamayan += 1
                self.stdout.write(self.style.WARNING('[-] OSM kaydi yok'))

            # Overpass rate limit aşmamak için kısa bekleme
            time_module.sleep(0.6)

        self.stdout.write(
            self.style.SUCCESS(
                f'\nTamamlandı: {guncellenen} mekan güncellendi, '
                f'{bulunamayan} mekan için OSM verisi bulunamadı.'
            )
        )
