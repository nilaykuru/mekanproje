import json
import time
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError

from django.core.management.base import BaseCommand
from venues.models import Mekan
from venues.management.commands.saatleri_guncelle import parse_opening_hours


SEHIR_AYARLARI = {
    'istanbul':  {'ad': 'İstanbul',  'lat': 41.0082, 'lon': 28.9784, 'yaricap': 6000},
    'izmir':     {'ad': 'İzmir',     'lat': 38.4192, 'lon': 27.1287, 'yaricap': 4000},
    'samsun':    {'ad': 'Samsun',    'lat': 41.2928, 'lon': 36.3313, 'yaricap': 4000},
    'sakarya':   {'ad': 'Sakarya',   'lat': 40.7731, 'lon': 30.3944, 'yaricap': 4000},
    'balikesir': {'ad': 'Balıkesir', 'lat': 39.6484, 'lon': 27.8826, 'yaricap': 4000},
}

KATEGORI_ESLESME = {
    'cafe':       'KAFE',
    'restaurant': 'RESTORAN',
    'library':    'KUTUPHANE',
    'pharmacy':   'ECZANE',
    'pub':        'PUB',
}

OVERPASS_URL = 'https://overpass-api.de/api/interpreter'


def overpass_sorgula(amenity, lat, lon, yaricap, limit):
    sorgu = f"""
[out:json][timeout:30];
node["amenity"="{amenity}"]["name"](around:{yaricap},{lat},{lon});
out {limit};
"""
    veri = urlencode({'data': sorgu}).encode()
    istek = Request(OVERPASS_URL, data=veri, headers={'User-Agent': 'AnlikMekan/1.0'})
    try:
        with urlopen(istek, timeout=35) as yanit:
            return json.loads(yanit.read().decode())
    except (URLError, json.JSONDecodeError):
        return None


class Command(BaseCommand):
    help = 'OpenStreetMap/Overpass API üzerinden gerçek mekan verisi çeker.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sehir', nargs='+',
            default=['istanbul', 'izmir', 'samsun', 'sakarya'],
            help='Veri çekilecek şehirler (varsayılan: hepsi)',
        )
        parser.add_argument(
            '--limit', type=int, default=25,
            help='Şehir+kategori başına max mekan sayısı (varsayılan: 25)',
        )

    def handle(self, *args, **options):
        sehirler = options['sehir']
        limit = options['limit']
        toplam = 0

        for sehir_kodu in sehirler:
            if sehir_kodu not in SEHIR_AYARLARI:
                self.stdout.write(self.style.WARNING(f'Bilinmeyen şehir: {sehir_kodu}'))
                continue

            ayar = SEHIR_AYARLARI[sehir_kodu]
            self.stdout.write(f'\n{ayar["ad"]} isleniyor...')

            for amenity, kategori in KATEGORI_ESLESME.items():
                self.stdout.write(f'  {amenity} sorgulanıyor...')
                sonuc = overpass_sorgula(amenity, ayar['lat'], ayar['lon'], ayar['yaricap'], limit)

                if sonuc is None:
                    self.stdout.write(self.style.ERROR(f'  Hata: {amenity} sorgusu basarisiz'))
                    continue

                eklenen = 0
                for el in sonuc.get('elements', []):
                    tags = el.get('tags', {})
                    ad = tags.get('name', '').strip()
                    if not ad:
                        continue

                    parcalar = []
                    sokak = tags.get('addr:street', '')
                    bina_no = tags.get('addr:housenumber', '')
                    if sokak:
                        parcalar.append(f'{sokak} {bina_no}'.strip())
                    ilce = tags.get('addr:suburb', '') or tags.get('addr:district', '')
                    if ilce:
                        parcalar.append(ilce)
                    parcalar.append(ayar['ad'])
                    adres = ', '.join(parcalar)

                    telefon = (tags.get('phone') or tags.get('contact:phone') or '')[:20]
                    website = tags.get('website') or tags.get('contact:website') or ''
                    if website and not website.startswith(('http://', 'https://')):
                        website = ''

                    # Çalışma saatleri (OSM opening_hours)
                    oh_str = tags.get('opening_hours', '')
                    acilis, kapanis = parse_opening_hours(oh_str)

                    mekan, olusturuldu = Mekan.objects.get_or_create(
                        ad=ad,
                        sehir=sehir_kodu,
                        defaults={
                            'kategori': kategori,
                            'adres': adres,
                            'telefon': telefon or None,
                            'website': website[:200] or None,
                            'latitude': el.get('lat'),
                            'longitude': el.get('lon'),
                            'dogrulanmis_mi': True,
                            'is_approved': True,
                            'su_an_acik': True,
                            'acilis_saati': acilis,
                            'kapanis_saati': kapanis,
                        }
                    )
                    if olusturuldu:
                        eklenen += 1
                        toplam += 1
                        try:
                            self.stdout.write(f'    + {ad}')
                        except UnicodeEncodeError:
                            self.stdout.write(f'    + [mekan eklendi]')

                self.stdout.write(f'  {eklenen} yeni mekan eklendi.')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f'\nTamamlandi. Toplam {toplam} yeni mekan eklendi.'))
