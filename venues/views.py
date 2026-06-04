from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db.models import Q, Avg, F
import json
import random
import string
import qrcode
import io
import base64
from .models import (Mekan, Yorum, Profile, Etkinlik, MekanFoto, YorumFoto,
                     SifreSifirlamaKodu, YorumBegeni, Bildirim, Takip,
                     MekanListesi, YorumYanit, Rezervasyon, Kampanya, CalismaGunu)
from .forms import (YorumForm, MekanForm, EtkinlikForm, KayitFormu,
                    RezervasyonForm, KampanyaForm, MekanListesiForm,
                    YorumYanitForm, CalismaGunuForm, MenuForm)

SAYFA_BOYUTU = 12

TUM_SEHIRLER = [
    ('adana','Adana'),('adiyaman','Adıyaman'),('afyonkarahisar','Afyonkarahisar'),
    ('agri','Ağrı'),('amasya','Amasya'),('ankara','Ankara'),('antalya','Antalya'),
    ('artvin','Artvin'),('aydin','Aydın'),('balikesir','Balıkesir'),
    ('bilecik','Bilecik'),('bingol','Bingöl'),('bitlis','Bitlis'),('bolu','Bolu'),
    ('burdur','Burdur'),('bursa','Bursa'),('canakkale','Çanakkale'),
    ('cankiri','Çankırı'),('corum','Çorum'),('denizli','Denizli'),
    ('diyarbakir','Diyarbakır'),('edirne','Edirne'),('elazig','Elazığ'),
    ('erzincan','Erzincan'),('erzurum','Erzurum'),('eskisehir','Eskişehir'),
    ('gaziantep','Gaziantep'),('giresun','Giresun'),('gumushane','Gümüşhane'),
    ('hakkari','Hakkari'),('hatay','Hatay'),('isparta','Isparta'),
    ('mersin','Mersin'),('istanbul','İstanbul'),('izmir','İzmir'),
    ('kars','Kars'),('kastamonu','Kastamonu'),('kayseri','Kayseri'),
    ('kirklareli','Kırklareli'),('kirsehir','Kırşehir'),('kocaeli','Kocaeli'),
    ('konya','Konya'),('kutahya','Kütahya'),('malatya','Malatya'),
    ('manisa','Manisa'),('kahramanmaras','Kahramanmaraş'),('mardin','Mardin'),
    ('mugla','Muğla'),('mus','Muş'),('nevsehir','Nevşehir'),('nigde','Niğde'),
    ('ordu','Ordu'),('rize','Rize'),('sakarya','Sakarya'),('samsun','Samsun'),
    ('siirt','Siirt'),('sinop','Sinop'),('sivas','Sivas'),('tekirdag','Tekirdağ'),
    ('tokat','Tokat'),('trabzon','Trabzon'),('tunceli','Tunceli'),
    ('sanliurfa','Şanlıurfa'),('usak','Uşak'),('van','Van'),('yozgat','Yozgat'),
    ('zonguldak','Zonguldak'),('aksaray','Aksaray'),('bayburt','Bayburt'),
    ('karaman','Karaman'),('kirikkale','Kırıkkale'),('batman','Batman'),
    ('sirnak','Şırnak'),('bartin','Bartın'),('ardahan','Ardahan'),
    ('igdir','Iğdır'),('yalova','Yalova'),('karabuk','Karabük'),
    ('kilis','Kilis'),('osmaniye','Osmaniye'),('duzce','Düzce'),
]


def bildirim_olustur(alici, tip, mesaj, link='', gonderen=None):
    """Kullanıcıya bildirim oluştur."""
    if alici != gonderen:
        Bildirim.objects.create(alici=alici, gonderen=gonderen, tip=tip, mesaj=mesaj, link=link)


# ── Yardımcı decorator ──────────────────────────────────────────────────────

def owner_required(view_func):
    """Sadece OWNER rolündeki kullanıcılara izin verir."""
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or request.user.profile.rol != 'OWNER':
            messages.error(request, "Bu sayfaya sadece mekan sahipleri erişebilir.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Kimlik Doğrulama ─────────────────────────────────────────────────────────

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'venues/landing.html')


def _hesap_dogrulama_emaili_gonder(request, user, profile):
    if not user.email:
        return False
    if settings.DEBUG:
        # Geliştirme ortamında sahte e-posta kullandığımız için doğrulamayı otomatik tamamla.
        profile.email_verified = True
        profile.save(update_fields=['email_verified'])
        return True
    dogrulama_url = request.build_absolute_uri(
        reverse('hesap_dogrula', args=[profile.email_verification_token])
    )
    send_mail(
        subject='Anlık Mekan — E-posta Adresinizi Doğrulayın',
        message=(
            f'Merhaba {user.username},\n\n'
            f'Anlık Mekan hesabınızı doğrulamak için aşağıdaki bağlantıya tıklayın:\n\n'
            f'{dogrulama_url}\n\n'
            f'Bu bağlantı yalnızca size özeldir. Hesabınızı oluşturmadıysanız bu e-postayı yok sayın.'
        ),
        from_email='noreply@anlikmekan.com',
        recipient_list=[user.email],
        fail_silently=True,
    )
    return True


def register(request):
    if request.method == 'POST':
        form = KayitFormu(request.POST)
        if form.is_valid():
            user = form.save()
            secilen_rol = request.POST.get('rol', 'USER')
            profile = Profile.objects.create(user=user, rol=secilen_rol)
            
            login(request, user)

            if secilen_rol == 'OWNER':
                messages.success(
                    request,
                    f"Hoş geldiniz {user.username}! Mekan sahibi hesabınızı güvenli hale getirmek için Google Authenticator kurulumunu tamamlayın."
                )
                return redirect('qr_kod_olustur')

            messages.success(request, f"Hoş geldiniz {user.username}! Mekanları keşfetmeye başlayabilirsiniz.")
            return redirect('dashboard')
    else:
        form = KayitFormu()
    default_rol = request.GET.get('rol', 'USER')
    return render(request, 'venues/register.html', {'form': form, 'default_rol': default_rol})


def hesap_dogrula(request, token):
    profile = get_object_or_404(Profile, email_verification_token=token)
    if not profile.email_verified:
        profile.email_verified = True
        profile.save(update_fields=['email_verified'])
        messages.success(request, 'E-postanız doğrulandı! Artık mekan ekleyebilirsiniz.')
    else:
        messages.info(request, 'E-postanız zaten doğrulanmış.')
    if request.user.is_authenticated:
        if profile.rol == 'OWNER':
            return redirect('owner_dashboard')
        return redirect('dashboard')
    return redirect('login')


# ── Gizli Yetkili Admin (Özel Arayüz) ──────────────────────────────────────

def admin_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                return redirect('admin_panel')
            messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı.')
    else:
        form = AuthenticationForm()
    return render(request, 'venues/admin_login.html', {'form': form})


@user_passes_test(lambda u: u.is_staff, login_url='admin_login')
def admin_panel(request):
    bekleyen_mekanlar = Mekan.objects.filter(is_approved=False)
    return render(request, 'venues/admin_panel.html', {'mekanlar': bekleyen_mekanlar})


@user_passes_test(lambda u: u.is_staff, login_url='admin_login')
@require_POST
def admin_approve(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id)
    mekan.is_approved = True
    mekan.save(update_fields=['is_approved'])
    messages.success(request, f'"{mekan.ad}" onaylandı ve sitede aktif oldu.')
    return redirect('admin_panel')


@user_passes_test(lambda u: u.is_staff, login_url='admin_login')
@require_POST
def admin_reject(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id)
    mekan.is_approved = False
    mekan.save(update_fields=['is_approved'])
    messages.success(request, f'"{mekan.ad}" reddedildi.')
    return redirect('admin_panel')


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if hasattr(user, 'profile') and user.profile.rol == 'OWNER':
                return redirect('owner_dashboard')
            return redirect('dashboard')
        messages.error(request, "Kullanıcı adı veya şifre hatalı!")
    else:
        form = AuthenticationForm()
    return render(request, 'venues/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('landing')


# ── Kullanıcı Sayfaları ───────────────────────────────────────────────────────

@login_required(login_url='login')
def dashboard(request):
    mekanlar = Mekan.objects.filter(is_approved=True).annotate(
        ort_puan=Avg('yorumlar__puan')
    )

    # Parametreleri al
    f = {
        'sehir':    request.GET.get('sehir', ''),
        'kategori': request.GET.get('kategori', ''),
        'acik':     request.GET.get('acik', ''),
        'wifi':     request.GET.get('wifi', ''),
        'priz':     request.GET.get('priz', ''),
        'bahce':    request.GET.get('bahce', ''),
        'pet':      request.GET.get('pet', ''),
        'engelli':  request.GET.get('engelli', ''),
        'muzik':    request.GET.get('muzik', ''),
        'cocuk':    request.GET.get('cocuk', ''),
        'siralama': request.GET.get('siralama', ''),
    }

    if f['sehir']:    mekanlar = mekanlar.filter(sehir=f['sehir'])
    if f['kategori']: mekanlar = mekanlar.filter(kategori=f['kategori'])
    if f['wifi']:     mekanlar = mekanlar.filter(wifi_var=True)
    if f['priz']:     mekanlar = mekanlar.filter(priz_var=True)
    if f['bahce']:    mekanlar = mekanlar.filter(bahce_var=True)
    if f['pet']:      mekanlar = mekanlar.filter(evcil_hayvan_izinli=True)
    if f['engelli']:  mekanlar = mekanlar.filter(engelli_erisimi_var=True)
    if f['muzik']:    mekanlar = mekanlar.filter(canli_muzik_var=True)
    if f['cocuk']:    mekanlar = mekanlar.filter(cocuk_oyun_alani_var=True)

    if f['siralama'] == 'puan':
        mekanlar = mekanlar.order_by(F('ort_puan').desc(nulls_last=True))
    elif f['siralama'] == 'doluluk_az':
        mekanlar = mekanlar.order_by('doluluk_orani')
    elif f['siralama'] == 'doluluk_cok':
        mekanlar = mekanlar.order_by('-doluluk_orani')
    elif f['siralama'] == 'isim_az':
        mekanlar = mekanlar.order_by('ad')
    elif f['siralama'] == 'isim_za':
        mekanlar = mekanlar.order_by('-ad')

    # acik_mi property DB'de hesaplanamaz (gece yarısı geçen saatler dahil) → Python filtresi
    if f['acik']:
        mekanlar = [m for m in mekanlar if m.acik_mi]

    aktif_filtre_sayisi = sum(1 for v in f.values() if v)

    # İnsan okunabilir görünen adlar (chip'lerde ve başlıkta kullanılır)
    sehir_adlari    = dict(TUM_SEHIRLER)
    kategori_adlari = dict(Mekan.KATEGORI_SECIMLERI)
    f['sehir_adi']    = sehir_adlari.get(f['sehir'], f['sehir'])
    f['kategori_adi'] = kategori_adlari.get(f['kategori'], f['kategori'])

    paginator = Paginator(mekanlar, SAYFA_BOYUTU)
    page_obj = paginator.get_page(request.GET.get('page'))
    sayfa_araligi = paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)

    return render(request, 'venues/index.html', {
        'mekanlar': page_obj,
        'page_obj': page_obj,
        'sayfa_araligi': sayfa_araligi,
        'sehir_secenekleri': TUM_SEHIRLER,
        'kategori_secenekleri': Mekan.KATEGORI_SECIMLERI,
        'f': f,
        'aktif_filtre_sayisi': aktif_filtre_sayisi,
        'toplam_sonuc': paginator.count,
    })


@login_required(login_url='login')
def arama_api(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'sonuclar': []})
    mekanlar = Mekan.objects.filter(is_approved=True).filter(
        Q(ad__icontains=q) | Q(adres__icontains=q) | Q(kategori__icontains=q)
    ).values('id', 'ad', 'kategori', 'sehir')[:8]
    return JsonResponse({'sonuclar': list(mekanlar)})


@login_required(login_url='login')
def arama(request):
    q = request.GET.get('q', '').strip()
    mekanlar = Mekan.objects.filter(is_approved=True).annotate(ort_puan=Avg('yorumlar__puan'))
    if q:
        mekanlar = mekanlar.filter(
            Q(ad__icontains=q) | Q(adres__icontains=q) | Q(kategori__icontains=q)
        )
        baslik = f'"{q}" için {mekanlar.count()} sonuç'
    else:
        baslik = 'Tüm Mekanlar'

    paginator = Paginator(mekanlar, SAYFA_BOYUTU)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'venues/liste.html', {
        'mekanlar': page_obj,
        'page_obj': page_obj,
        'sayfa_araligi': paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1),
        'baslik': baslik,
        'q': q,
    })


@login_required(login_url='login')
def su_an_acik_olanlar(request):
    # acik_mi property'sini kullan: saati olan mekanlarda saate göre, olmayanlar su_an_acik ile
    mekanlar_qs = Mekan.objects.filter(is_approved=True).annotate(ort_puan=Avg('yorumlar__puan'))
    mekanlar = [m for m in mekanlar_qs if m.acik_mi]
    paginator = Paginator(mekanlar, SAYFA_BOYUTU)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'venues/liste.html', {
        'mekanlar': page_obj, 'page_obj': page_obj,
        'sayfa_araligi': paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1),
        'baslik': f'Şu An Açık Olan Mekanlar ({len(mekanlar)})',
    })


@login_required(login_url='login')
def calisma_alanlari(request):
    mekanlar = Mekan.objects.filter(
        is_approved=True
    ).filter(
        Q(kategori='KUTUPHANE') | Q(calisma_alani_var=True)
    ).annotate(ort_puan=Avg('yorumlar__puan'))
    paginator = Paginator(mekanlar, SAYFA_BOYUTU)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'venues/liste.html', {
        'mekanlar': page_obj, 'page_obj': page_obj,
        'sayfa_araligi': paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1),
        'baslik': 'Çalışma Alanları',
    })


@login_required(login_url='login')
def acil_ihtiyaclar(request):
    mekanlar = Mekan.objects.filter(kategori='ECZANE', is_approved=True).annotate(ort_puan=Avg('yorumlar__puan'))
    paginator = Paginator(mekanlar, SAYFA_BOYUTU)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'venues/liste.html', {
        'mekanlar': page_obj, 'page_obj': page_obj,
        'sayfa_araligi': paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1),
        'baslik': 'Nöbetçi/Açık Eczaneler',
    })


@login_required
def favori_islem(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id)
    if mekan.favorileyenler.filter(id=request.user.id).exists():
        mekan.favorileyenler.remove(request.user)
    else:
        mekan.favorileyenler.add(request.user)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def favorilerim(request):
    mekanlar = request.user.favori_mekanlar.all().annotate(ort_puan=Avg('yorumlar__puan'))
    paginator = Paginator(mekanlar, SAYFA_BOYUTU)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'venues/liste.html', {
        'mekanlar': page_obj, 'page_obj': page_obj,
        'sayfa_araligi': paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1),
        'baslik': 'Favori Mekanlarım',
    })


def mekan_detay(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id)
    yorumlar = mekan.yorumlar.all().order_by('-tarih')
    etkinlikler = mekan.aktif_etkinlikler()
    fotolar = mekan.fotolar.all()

    # Görüntülenme sayısını artır (giriş yapmış kullanıcılar için)
    if request.user.is_authenticated:
        Mekan.objects.filter(pk=mekan_id).update(goruntuleme_sayisi=F('goruntuleme_sayisi') + 1)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = YorumForm(request.POST, request.FILES)
        if form.is_valid():
            yeni_yorum = form.save(commit=False)
            yeni_yorum.mekan = mekan
            yeni_yorum.yazar = request.user
            yeni_yorum.save()
            # Çoklu fotoğraf kaydet
            for f in request.FILES.getlist('yorum_fotolar'):
                if f.content_type.startswith('image/'):
                    YorumFoto.objects.create(yorum=yeni_yorum, foto=f)
            return redirect('mekan_detay', mekan_id=mekan.id)
    else:
        form = YorumForm()

    # Kullanıcının hangi yorumları beğendiğini set olarak hazırla (template'de |map yok)
    kullanici_begenileri = set()
    if request.user.is_authenticated:
        kullanici_begenileri = set(
            YorumBegeni.objects.filter(
                kullanici=request.user,
                yorum__mekan=mekan
            ).values_list('yorum_id', flat=True)
        )

    takip_ediyor = False
    if request.user.is_authenticated and mekan.sahibi:
        takip_ediyor = Takip.objects.filter(
            takipci=request.user, takip_edilen=mekan.sahibi
        ).exists()

    from django.utils import timezone as tz
    now = tz.now()
    aktif_kampanyalar = [k for k in mekan.kampanyalar.all() if k.baslangic <= now <= k.bitis]

    return render(request, 'venues/mekan_detay.html', {
        'mekan': mekan,
        'yorumlar': yorumlar,
        'etkinlikler': etkinlikler,
        'fotolar': fotolar,
        'form': form,
        'bugun_no': tz.localtime().weekday(),
        'kullanici_begenileri': kullanici_begenileri,
        'takip_ediyor': takip_ediyor,
        'aktif_kampanyalar': aktif_kampanyalar,
    })


# ── Mekan Sahibi Paneli ────────────────────────────────────────────────────────

@owner_required
def mekan_sahibi_paneli(request):
    mekanlarim = request.user.mekanlari.prefetch_related('etkinlikler', 'rezervasyonlar', 'kampanyalar', 'calisma_gunleri').all()
    # Yorum puan dağılımı: {mekan_id: [p1, p2, p3, p4, p5]}
    puan_dagilim = {}
    for m in mekanlarim:
        ys = m.yorumlar.all()
        puan_dagilim[m.id] = [
            ys.filter(puan=i).count() for i in range(1, 6)
        ]
    return render(request, 'venues/owner_dashboard.html', {
        'mekanlar': mekanlarim,
        'puan_dagilim_json': json.dumps(puan_dagilim),
    })



@owner_required
def mekan_olustur(request):
    if not request.user.profile.is_verified:
        messages.error(request, "Mekan ekleyebilmek için önce 2FA doğrulama yapmanız gerekiyor. Lütfen QR kod doğrulama sayfasını ziyaret edin.")
        return redirect('qr_kod_olustur')
    if request.method == 'POST':
        form = MekanForm(request.POST, request.FILES)
        if form.is_valid():
            mekan = form.save(commit=False)
            mekan.sahibi = request.user
            mekan.save()
            messages.success(
                request,
                f'"{mekan.ad}" eklendi. Admin inceleyip onayladıktan sonra yayına alınacak.'
            )
            return redirect('owner_dashboard')
    else:
        form = MekanForm()
    return render(request, 'venues/mekan_form.html', {'form': form, 'baslik': 'Yeni Mekan Ekle', 'mod': 'olustur'})


@owner_required
def mekan_duzenle(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id, sahibi=request.user)
    if request.method == 'POST':
        form = MekanForm(request.POST, request.FILES, instance=mekan)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{mekan.ad}" bilgileri güncellendi.')
            return redirect('owner_dashboard')
    else:
        form = MekanForm(instance=mekan)
    return render(request, 'venues/mekan_form.html', {
        'form': form,
        'mekan': mekan,
        'baslik': f'"{mekan.ad}" Düzenle',
        'mod': 'duzenle',
    })


@owner_required
@require_POST
def mekan_sil(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id, sahibi=request.user)
    ad = mekan.ad
    mekan.delete()
    messages.success(request, f'"{ad}" silindi.')
    return redirect('owner_dashboard')


# ── Hesap Doğrulama ───────────────────────────────────────────────────────────

@owner_required
@require_POST
def hesap_dogrulama_yeniden_gonder(request):
    profile = request.user.profile
    if profile.email_verified:
        messages.info(request, 'E-postanız zaten doğrulanmış.')
        return redirect('owner_dashboard')
    if settings.DEBUG:
        profile.email_verified = True
        profile.save(update_fields=['email_verified'])
        messages.success(request, 'Geliştirme modunda e-posta doğrulaması atlandı.')
        return redirect('owner_dashboard')
    gonderildi = _hesap_dogrulama_emaili_gonder(request, request.user, profile)
    if gonderildi:
        messages.success(request, f'Doğrulama e-postası {request.user.email} adresine tekrar gönderildi.')
    else:
        messages.error(request, 'Hesabınızda kayıtlı e-posta adresi bulunamadı.')
    return redirect('owner_dashboard')


# ── Anlık Durum Güncelleme (AJAX) ─────────────────────────────────────────────

@login_required
@require_POST
def durum_guncelle(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id, sahibi=request.user)
    alan = request.POST.get('alan')
    deger = request.POST.get('deger')

    if alan == 'su_an_acik':
        mekan.su_an_acik = deger == 'true'
        mekan.save(update_fields=['su_an_acik'])
        return JsonResponse({'ok': True, 'deger': mekan.su_an_acik})

    if alan == 'doluluk_orani':
        try:
            mekan.doluluk_orani = max(0, min(100, int(deger)))
            mekan.save(update_fields=['doluluk_orani'])
            return JsonResponse({'ok': True, 'deger': mekan.doluluk_orani})
        except (ValueError, TypeError):
            return JsonResponse({'ok': False, 'hata': 'Geçersiz değer'}, status=400)

    if alan == 'anlik_duyuru':
        mekan.anlik_duyuru = deger
        mekan.save(update_fields=['anlik_duyuru'])
        return JsonResponse({'ok': True})

    return JsonResponse({'ok': False, 'hata': 'Bilinmeyen alan'}, status=400)


# ── Etkinlik CRUD ─────────────────────────────────────────────────────────────

@owner_required
def etkinlik_olustur(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id, sahibi=request.user)
    if request.method == 'POST':
        form = EtkinlikForm(request.POST, request.FILES)
        if form.is_valid():
            etkinlik = form.save(commit=False)
            etkinlik.mekan = mekan
            etkinlik.save()
            messages.success(request, 'Etkinlik oluşturuldu.')
            return redirect('owner_dashboard')
    else:
        form = EtkinlikForm()
    return render(request, 'venues/etkinlik_form.html', {
        'form': form,
        'mekan': mekan,
        'baslik': f'"{mekan.ad}" için Etkinlik Ekle',
        'mod': 'olustur',
    })


@owner_required
def etkinlik_duzenle(request, etkinlik_id):
    etkinlik = get_object_or_404(Etkinlik, id=etkinlik_id, mekan__sahibi=request.user)
    if request.method == 'POST':
        form = EtkinlikForm(request.POST, request.FILES, instance=etkinlik)
        if form.is_valid():
            form.save()
            messages.success(request, 'Etkinlik güncellendi.')
            return redirect('owner_dashboard')
    else:
        form = EtkinlikForm(instance=etkinlik)
    return render(request, 'venues/etkinlik_form.html', {
        'form': form,
        'mekan': etkinlik.mekan,
        'etkinlik': etkinlik,
        'baslik': 'Etkinliği Düzenle',
        'mod': 'duzenle',
    })


@owner_required
@require_POST
def etkinlik_sil(request, etkinlik_id):
    etkinlik = get_object_or_404(Etkinlik, id=etkinlik_id, mekan__sahibi=request.user)
    etkinlik.delete()
    messages.success(request, 'Etkinlik silindi.')
    return redirect('owner_dashboard')


# ── Yorum Düzenle / Sil ───────────────────────────────────────────────────────

@login_required
@require_POST
def yorum_sil(request, yorum_id):
    yorum = get_object_or_404(Yorum, id=yorum_id, yazar=request.user)
    mekan_id = yorum.mekan_id
    yorum.delete()
    messages.success(request, 'Yorum silindi.')
    return redirect('mekan_detay', mekan_id=mekan_id)


@login_required
def yorum_duzenle(request, yorum_id):
    yorum = get_object_or_404(Yorum, id=yorum_id, yazar=request.user)
    mekan = yorum.mekan
    if request.method == 'POST':
        form = YorumForm(request.POST, request.FILES, instance=yorum)
        if form.is_valid():
            form.save()
            # Yeni eklenen fotoğrafları kaydet
            for f in request.FILES.getlist('yorum_fotolar'):
                if f.content_type.startswith('image/'):
                    YorumFoto.objects.create(yorum=yorum, foto=f)
            messages.success(request, 'Yorum güncellendi.')
            return redirect('mekan_detay', mekan_id=mekan.id)
    else:
        form = YorumForm(instance=yorum)
    return render(request, 'venues/yorum_duzenle.html', {
        'form': form,
        'yorum': yorum,
        'mekan': mekan,
        'mevcut_fotolar': yorum.fotolar.all(),
    })


# ── Yorum Fotoğrafı Sil ───────────────────────────────────────────────────────

@login_required
@require_POST
def yorum_foto_sil(request, foto_id):
    foto = get_object_or_404(YorumFoto, id=foto_id, yorum__yazar=request.user)
    mekan_id = foto.yorum.mekan_id
    foto.foto.delete(save=False)
    foto.delete()
    return redirect('mekan_detay', mekan_id=mekan_id)


# ── Mekan Galerisi (Çoklu Fotoğraf) ──────────────────────────────────────────

@owner_required
@require_POST
def mekan_foto_yukle(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id, sahibi=request.user)
    fotolar = request.FILES.getlist('fotolar')
    yuklenen = 0
    for f in fotolar:
        if f.content_type.startswith('image/'):
            MekanFoto.objects.create(mekan=mekan, foto=f)
            yuklenen += 1
    if yuklenen:
        messages.success(request, f'{yuklenen} fotoğraf yüklendi.')
    return redirect('owner_dashboard')


@owner_required
@require_POST
def mekan_foto_sil(request, foto_id):
    foto = get_object_or_404(MekanFoto, id=foto_id, mekan__sahibi=request.user)
    foto.foto.delete(save=False)
    foto.delete()
    messages.success(request, 'Fotoğraf silindi.')
    return redirect('owner_dashboard')


# ── Eski duyuru_guncelle (geriye dönük uyumluluk) ─────────────────────────────

@login_required
def duyuru_guncelle(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id, sahibi=request.user)
    if request.method == 'POST':
        mekan.anlik_duyuru = request.POST.get('duyuru', '')
        mekan.save(update_fields=['anlik_duyuru'])
        messages.success(request, "Duyuru güncellendi!")
    return redirect('owner_dashboard')


# ── TOTP 2FA QR Kod Doğrulama ───────────────────────────────────────────────────

@login_required
def qr_kod_olustur(request):
    """
    Kullanıcıya özel TOTP QR kodu oluşturur ve gösterir.
    Google Authenticator ile taranabilir.
    """
    profile = request.user.profile
    
    # Eğer henüz gizli anahtar yoksa oluştur
    if not profile.totp_secret_key:
        profile.generate_totp_secret()
    
    # TOTP URI'sini al
    totp_uri = profile.get_totp_uri()
    
    # QR kod oluştur
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # QR kodunu base64 formatına dönüştür (HTML'de göstermek için)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'qr_code_base64': qr_code_base64,
        'secret_key': profile.totp_secret_key,
        'user_email': request.user.email,
    }
    
    return render(request, 'venues/qr_kod_olustur.html', context)


@login_required
@require_POST
def qr_kod_dogrula(request):
    """
    Kullanıcıdan gelen 6 haneli TOTP kodunu doğrular.
    Doğruysa is_verified=True yapılır.
    """
    profile = request.user.profile
    totp_code = request.POST.get('totp_code', '').strip()
    
    # Kod boş mu?
    if not totp_code:
        messages.error(request, "Doğrulama kodunu girin.")
        return redirect('qr_kod_olustur')
    
    # Kod 6 haneli mi?
    if not totp_code.isdigit() or len(totp_code) != 6:
        messages.error(request, "Doğrulama kodu 6 hane olmalıdır.")
        return redirect('qr_kod_olustur')
    
    # Kodu doğrula
    if profile.verify_totp(totp_code):
        profile.is_verified = True
        profile.save(update_fields=['is_verified'])
        messages.success(request, "✓ 2FA başarıyla doğrulandı! Mekan ekleyebilir ve yönetebilirsiniz.")
        if profile.rol == 'OWNER':
            return redirect('owner_dashboard')
        return redirect('dashboard')
    else:
        messages.error(request, "✗ Doğrulama kodu yanlış. Lütfen tekrar deneyin.")
        return redirect('qr_kod_olustur')


@login_required(login_url='login')
def profil(request):
    kullanici = request.user
    yorumlar = Yorum.objects.filter(yazar=kullanici).select_related('mekan').order_by('-tarih')
    favori_mekanlar = kullanici.favori_mekanlar.filter(is_approved=True).annotate(
        ort_puan=Avg('yorumlar__puan')
    )

    # Profil güncelleme
    if request.method == 'POST':
        islem = request.POST.get('islem', 'email')

        if islem == 'foto':
            # Profil fotoğrafı yükle/kaldır
            profil_obj = kullanici.profile
            if 'foto_sil' in request.POST:
                if profil_obj.foto:
                    profil_obj.foto.delete(save=False)
                    profil_obj.foto = None
                    profil_obj.save(update_fields=['foto'])
                    messages.success(request, 'Profil fotoğrafı kaldırıldı.')
            elif 'foto' in request.FILES:
                profil_obj.foto = request.FILES['foto']
                profil_obj.save(update_fields=['foto'])
                messages.success(request, 'Profil fotoğrafı güncellendi.')
        else:
            # E-posta güncelle
            yeni_email = request.POST.get('email', '').strip()
            if yeni_email and yeni_email != kullanici.email:
                kullanici.email = yeni_email
                kullanici.save(update_fields=['email'])
                messages.success(request, 'E-posta adresiniz güncellendi.')

        return redirect('profil')

    return render(request, 'venues/profil.html', {
        'profil_kullanici': kullanici,
        'yorumlar': yorumlar,
        'favori_mekanlar': favori_mekanlar,
        'yorum_sayisi': yorumlar.count(),
        'favori_sayisi': favori_mekanlar.count(),
    })


# ── OTP Şifre Sıfırlama ──────────────────────────────────────────────────────

def sifre_sifirla_talep(request):
    """
    1. Kullanıcı e-posta adresini girer.
    2. Eşleşen hesap varsa 6 haneli kod üretilir, mail gönderilir.
    3. Kullanıcı kod giriş sayfasına yönlendirilir.
    Mail içinde sadece kod vardır — URL yok, spam filtrelerinden geçer.
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user:
            # Eski kullanılmamış kodları iptal et
            SifreSifirlamaKodu.objects.filter(user=user, kullanildi=False).update(kullanildi=True)
            # Yeni 6 haneli kod oluştur
            kod = ''.join(random.choices(string.digits, k=6))
            SifreSifirlamaKodu.objects.create(user=user, kod=kod)
            # Sadece kodu içeren mail gönder (URL yok!)
            send_mail(
                subject='Anlık Mekan — Şifre Sıfırlama Kodu',
                message=(
                    f'Merhaba {user.username},\n\n'
                    f'Şifrenizi sıfırlamak için doğrulama kodunuz:\n\n'
                    f'  {kod}\n\n'
                    f'Bu kod 15 dakika geçerlidir.\n'
                    f'Eğer bu isteği siz yapmadıysanız bu mesajı yok sayın.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            # Kullanıcı adını session'a sakla (kod doğrulama sayfasında kullanmak için)
            request.session['sifre_sifirla_user_id'] = user.id
            messages.success(request, f'Doğrulama kodu {email} adresine gönderildi. Kodu girerek şifrenizi sıfırlayın.')
            return redirect('sifre_sifirla_kod')
        else:
            # Güvenlik: kullanıcıya hesap olmadığını söyleme, aynı mesajı göster
            messages.info(request, 'Girilen e-posta adresi kayıtlıysa kod gönderildi.')

    return render(request, 'venues/sifre_sifirla_talep.html')


def sifre_sifirla_kod(request):
    """
    Kullanıcı 6 haneli kodu ve yeni şifresini girer.
    Kod geçerliyse şifre güncellenir.
    """
    user_id = request.session.get('sifre_sifirla_user_id')
    if not user_id:
        messages.error(request, 'Geçersiz oturum. Lütfen şifre sıfırlama işlemini baştan başlatın.')
        return redirect('sifre_sifirla_talep')

    if request.method == 'POST':
        from django.contrib.auth.models import User
        kod = request.POST.get('kod', '').strip()
        sifre1 = request.POST.get('sifre1', '')
        sifre2 = request.POST.get('sifre2', '')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'Kullanıcı bulunamadı.')
            return redirect('sifre_sifirla_talep')

        if sifre1 != sifre2:
            messages.error(request, 'Şifreler eşleşmiyor.')
            return render(request, 'venues/sifre_sifirla_kod.html')

        if len(sifre1) < 8:
            messages.error(request, 'Şifre en az 8 karakter olmalıdır.')
            return render(request, 'venues/sifre_sifirla_kod.html')

        # En son geçerli kodu bul
        try:
            kayit = SifreSifirlamaKodu.objects.filter(
                user=user, kullanildi=False
            ).latest('olusturuldu')
        except SifreSifirlamaKodu.DoesNotExist:
            messages.error(request, 'Geçerli bir kod bulunamadı. Lütfen yeni kod isteyin.')
            return redirect('sifre_sifirla_talep')

        if not kayit.gecerli_mi():
            messages.error(request, 'Kodun süresi dolmuş. Lütfen yeni kod isteyin.')
            return redirect('sifre_sifirla_talep')

        if kayit.kod != kod:
            messages.error(request, 'Doğrulama kodu hatalı. Lütfen tekrar deneyin.')
            return render(request, 'venues/sifre_sifirla_kod.html')

        # Şifreyi güncelle
        user.set_password(sifre1)
        user.save()
        kayit.kullanildi = True
        kayit.save(update_fields=['kullanildi'])
        # Session'ı temizle
        del request.session['sifre_sifirla_user_id']
        messages.success(request, 'Şifreniz başarıyla sıfırlandı. Yeni şifrenizle giriş yapabilirsiniz.')
        return redirect('login')

    return render(request, 'venues/sifre_sifirla_kod.html')


# ── Harita Görünümü ───────────────────────────────────────────────────────────

@login_required(login_url='login')
def mekan_harita(request):
    """Split-screen harita sayfası — Leaflet.js ile tüm mekanları gösterir."""
    sehir    = request.GET.get('sehir', '')
    kategori = request.GET.get('kategori', '')
    acik     = request.GET.get('acik', '')
    wifi     = request.GET.get('wifi', '')
    priz     = request.GET.get('priz', '')
    bahce    = request.GET.get('bahce', '')
    pet      = request.GET.get('pet', '')
    engelli  = request.GET.get('engelli', '')
    muzik    = request.GET.get('muzik', '')
    sigara   = request.GET.get('sigara', '')

    mekanlar_qs = Mekan.objects.filter(is_approved=True).annotate(ort_puan=Avg('yorumlar__puan'))
    if sehir:    mekanlar_qs = mekanlar_qs.filter(sehir=sehir)
    if kategori: mekanlar_qs = mekanlar_qs.filter(kategori=kategori)
    if wifi:     mekanlar_qs = mekanlar_qs.filter(wifi_var=True)
    if priz:     mekanlar_qs = mekanlar_qs.filter(priz_var=True)
    if bahce:    mekanlar_qs = mekanlar_qs.filter(bahce_var=True)
    if pet:      mekanlar_qs = mekanlar_qs.filter(evcil_hayvan_izinli=True)
    if engelli:  mekanlar_qs = mekanlar_qs.filter(engelli_erisimi_var=True)
    if muzik:    mekanlar_qs = mekanlar_qs.filter(canli_muzik_var=True)
    if sigara:   mekanlar_qs = mekanlar_qs.filter(sigara_icin_uygun=True)

    # Sol liste için (tüm liste, haritayla senkron)
    mekanlar_liste = list(mekanlar_qs)

    # acik filtresi Python seviyesinde (acik_mi property DB'de hesaplanamaz)
    if acik:
        mekanlar_liste = [m for m in mekanlar_liste if m.acik_mi]

    # Harita için koordinatı olan mekanları JSON'a çevir
    harita_verisi = []
    for m in mekanlar_liste:
        if m.latitude and m.longitude:
            harita_verisi.append({
                'id': m.id,
                'ad': m.ad,
                'kategori': m.kategori,
                'kategori_display': m.get_kategori_display(),
                'adres': m.adres,
                'lat': float(m.latitude),
                'lng': float(m.longitude),
                'su_an_acik': m.acik_mi,
                'doluluk_orani': m.doluluk_orani,
                'ort_puan': float(m.ort_puan) if m.ort_puan else None,
                'yorum_sayisi': m.yorum_sayisi,
                'detay_url': reverse('mekan_detay', args=[m.id]),
                'img_url': m.img.url if m.img else None,
                'wifi_var': m.wifi_var,
                'priz_var': m.priz_var,
                'bahce_var': m.bahce_var,
                'evcil_hayvan_izinli': m.evcil_hayvan_izinli,
                'engelli_erisimi_var': m.engelli_erisimi_var,
                'canli_muzik_var': m.canli_muzik_var,
                'sigara_icin_uygun': m.sigara_icin_uygun,
            })

    return render(request, 'venues/mekan_harita.html', {
        'mekanlar': mekanlar_liste,
        'harita_verisi_json': json.dumps(harita_verisi, ensure_ascii=False),
        'aktif_sehir': sehir,
        'aktif_kategori': kategori,
        'aktif_acik': acik,
        'aktif_wifi': wifi,
        'aktif_priz': priz,
        'aktif_bahce': bahce,
        'aktif_pet': pet,
        'aktif_engelli': engelli,
        'aktif_muzik': muzik,
        'aktif_sigara': sigara,
        'sehir_secenekleri': TUM_SEHIRLER,
        'kategori_secenekleri': Mekan.KATEGORI_SECIMLERI,
        'toplam_mekan': len(mekanlar_liste),
        'haritada_mekan': len(harita_verisi),
    })


# ── Bildirimler ───────────────────────────────────────────────────────────────

@login_required
def bildirimler(request):
    bildirimleri = request.user.bildirimler.all()
    request.user.bildirimler.filter(okundu=False).update(okundu=True)
    return render(request, 'venues/bildirimler.html', {'bildirimler': bildirimleri})


@login_required
def bildirim_okundu_isle(request):
    """AJAX: bildirim sayısı badge için."""
    sayi = request.user.bildirimler.filter(okundu=False).count()
    return JsonResponse({'sayi': sayi})


# ── Yorum Beğeni ──────────────────────────────────────────────────────────────

@login_required
@require_POST
def yorum_begen(request, yorum_id):
    yorum = get_object_or_404(Yorum, id=yorum_id)
    obj, created = YorumBegeni.objects.get_or_create(yorum=yorum, kullanici=request.user)
    if not created:
        obj.delete()
        begendi = False
    else:
        begendi = True
        if yorum.yazar != request.user:
            bildirim_olustur(
                alici=yorum.yazar,
                tip='BEGENI',
                mesaj=f'{request.user.username} yorumunuzu beğendi.',
                link=f'/mekan/{yorum.mekan_id}/',
                gonderen=request.user,
            )
    sayi = yorum.begeniler.count()
    return JsonResponse({'begendi': begendi, 'sayi': sayi})


# ── Takip Sistemi ─────────────────────────────────────────────────────────────

@login_required
@require_POST
def mekan_takip(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id)
    if not mekan.sahibi:
        return JsonResponse({'hata': 'Bu mekanın sahibi yok'}, status=400)
    if mekan.sahibi == request.user:
        return JsonResponse({'hata': 'Kendi mekanınızı takip edemezsiniz'}, status=400)
    obj, created = Takip.objects.get_or_create(takipci=request.user, takip_edilen=mekan.sahibi)
    if not created:
        obj.delete()
        takip_ediyor = False
    else:
        takip_ediyor = True
        bildirim_olustur(
            alici=mekan.sahibi,
            tip='TAKIP',
            mesaj=f'{request.user.username} mekanınızı takip etmeye başladı.',
            link=f'/mekan/{mekan.id}/',
            gonderen=request.user,
        )
    takipci_sayisi = mekan.sahibi.takipcileri.count()
    return JsonResponse({'takip_ediyor': takip_ediyor, 'takipci_sayisi': takipci_sayisi})


@login_required
@require_POST
def kullanici_takip(request, kullanici_id):
    from django.contrib.auth.models import User as DjangoUser
    hedef = get_object_or_404(DjangoUser, id=kullanici_id)
    if hedef == request.user:
        return JsonResponse({'hata': 'Kendinizi takip edemezsiniz'}, status=400)
    obj, created = Takip.objects.get_or_create(takipci=request.user, takip_edilen=hedef)
    if not created:
        obj.delete()
        takip_ediyor = False
    else:
        takip_ediyor = True
        bildirim_olustur(
            alici=hedef,
            tip='TAKIP',
            mesaj=f'{request.user.username} sizi takip etmeye başladı.',
            link=f'/kullanici/{request.user.id}/',
            gonderen=request.user,
        )
    takipci_sayisi = hedef.takipcileri.count()
    return JsonResponse({'takip_ediyor': takip_ediyor, 'takipci_sayisi': takipci_sayisi})


@login_required
def kullanici_profil(request, kullanici_id):
    from django.contrib.auth.models import User as DjangoUser
    hedef = get_object_or_404(DjangoUser, id=kullanici_id)
    yorumlar = Yorum.objects.filter(yazar=hedef).select_related('mekan').order_by('-tarih')
    listeler = MekanListesi.objects.filter(olusturan=hedef, herkese_acik=True)
    takip_ediyor = False
    if request.user.is_authenticated:
        takip_ediyor = Takip.objects.filter(takipci=request.user, takip_edilen=hedef).exists()
    takipci_sayisi = hedef.takipcileri.count()
    takip_sayisi = hedef.takip_ettikleri.count()
    return render(request, 'venues/kullanici_profil.html', {
        'hedef': hedef,
        'yorumlar': yorumlar,
        'listeler': listeler,
        'takip_ediyor': takip_ediyor,
        'takipci_sayisi': takipci_sayisi,
        'takip_sayisi': takip_sayisi,
    })


# ── Mekan Listeleri ───────────────────────────────────────────────────────────

@login_required
def listelerim(request):
    listeler = MekanListesi.objects.filter(olusturan=request.user).prefetch_related('mekanlar')
    form = MekanListesiForm()
    if request.method == 'POST':
        form = MekanListesiForm(request.POST)
        if form.is_valid():
            liste = form.save(commit=False)
            liste.olusturan = request.user
            liste.save()
            messages.success(request, f'"{liste.ad}" listesi oluşturuldu.')
            return redirect('listelerim')
    return render(request, 'venues/listelerim.html', {'listeler': listeler, 'form': form})


@login_required
def liste_detay(request, liste_id):
    liste = get_object_or_404(MekanListesi, id=liste_id)
    if not liste.herkese_acik and liste.olusturan != request.user:
        messages.error(request, 'Bu liste gizli.')
        return redirect('dashboard')
    return render(request, 'venues/liste_detay.html', {'liste': liste})


@login_required
@require_POST
def liste_mekan_ekle(request, liste_id, mekan_id):
    liste = get_object_or_404(MekanListesi, id=liste_id, olusturan=request.user)
    mekan = get_object_or_404(Mekan, id=mekan_id)
    liste.mekanlar.add(mekan)
    return JsonResponse({'ok': True, 'mesaj': f'"{mekan.ad}" listeye eklendi.'})


@login_required
@require_POST
def liste_mekan_cikar(request, liste_id, mekan_id):
    liste = get_object_or_404(MekanListesi, id=liste_id, olusturan=request.user)
    mekan = get_object_or_404(Mekan, id=mekan_id)
    liste.mekanlar.remove(mekan)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def liste_sil(request, liste_id):
    liste = get_object_or_404(MekanListesi, id=liste_id, olusturan=request.user)
    ad = liste.ad
    liste.delete()
    messages.success(request, f'"{ad}" listesi silindi.')
    return redirect('listelerim')


# ── Yorum Yanıtı (Sahip) ─────────────────────────────────────────────────────

@login_required
def yorum_yanit(request, yorum_id):
    yorum = get_object_or_404(Yorum, id=yorum_id)
    if yorum.mekan.sahibi != request.user:
        messages.error(request, 'Sadece mekan sahibi yanıt verebilir.')
        return redirect('mekan_detay', mekan_id=yorum.mekan_id)
    if request.method == 'POST':
        form = YorumYanitForm(request.POST)
        if hasattr(yorum, 'yanit'):
            form = YorumYanitForm(request.POST, instance=yorum.yanit)
        if form.is_valid():
            yanit = form.save(commit=False)
            yanit.yorum = yorum
            yanit.yazan = request.user
            yanit.save()
            bildirim_olustur(
                alici=yorum.yazar,
                tip='YANIT',
                mesaj=f'{request.user.username} yorumunuza yanıt verdi.',
                link=f'/mekan/{yorum.mekan_id}/',
                gonderen=request.user,
            )
            messages.success(request, 'Yanıtınız kaydedildi.')
    return redirect('mekan_detay', mekan_id=yorum.mekan_id)


# ── Rezervasyon ───────────────────────────────────────────────────────────────

@login_required
@require_POST
def rezervasyon_olustur(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id, is_approved=True)
    if not mekan.rezervasyon_aktif:
        messages.error(request, 'Bu mekan şu an rezervasyon kabul etmiyor.')
        return redirect('mekan_detay', mekan_id=mekan_id)
    form = RezervasyonForm(request.POST)
    if form.is_valid():
        rez = form.save(commit=False)
        from django.utils import timezone as tz
        if rez.tarih < tz.localdate():
            messages.error(request, 'Geçmiş bir tarihe rezervasyon yapamazsınız.')
            return redirect('mekan_detay', mekan_id=mekan_id)
        rez.mekan = mekan
        rez.kullanici = request.user
        rez.save()
        if mekan.sahibi:
            bildirim_olustur(
                alici=mekan.sahibi,
                tip='REZERVASYON',
                mesaj=f'{request.user.username} rezervasyon talebi gönderdi — {rez.tarih} {rez.saat}',
                link=f'/owner-dashboard/',
                gonderen=request.user,
            )
        messages.success(request, 'Rezervasyon talebiniz gönderildi! Mekan sahibi onaylayacaktır.')
    else:
        for err in form.errors.values():
            messages.error(request, err[0])
    return redirect('mekan_detay', mekan_id=mekan_id)


@login_required
def rezervasyonlarim(request):
    rezervasyonlar = request.user.rezervasyonlarim.select_related('mekan').all()
    return render(request, 'venues/rezervasyonlarim.html', {'rezervasyonlar': rezervasyonlar})


@login_required
@require_POST
def rezervasyon_iptal(request, rezervasyon_id):
    rez = get_object_or_404(Rezervasyon, id=rezervasyon_id, kullanici=request.user)
    if rez.durum != 'BEKLIYOR':
        messages.error(request, 'Sadece bekleyen rezervasyonlar iptal edilebilir.')
        return redirect('rezervasyonlarim')
    rez.durum = 'IPTAL'
    rez.save(update_fields=['durum'])
    if rez.mekan.sahibi:
        bildirim_olustur(
            alici=rez.mekan.sahibi,
            tip='REZERVASYON',
            mesaj=f'{request.user.username} rezervasyonunu iptal etti — {rez.tarih} {rez.saat}',
            link='/owner-dashboard/',
        )
    messages.success(request, 'Rezervasyonunuz iptal edildi.')
    return redirect('rezervasyonlarim')


@owner_required
@require_POST
def rezervasyon_guncelle(request, rezervasyon_id):
    rez = get_object_or_404(Rezervasyon, id=rezervasyon_id, mekan__sahibi=request.user)
    durum = request.POST.get('durum')
    if durum in ['ONAYLANDI', 'REDDEDILDI']:
        rez.durum = durum
        rez.save(update_fields=['durum'])
        mesaj = 'onaylandı' if durum == 'ONAYLANDI' else 'reddedildi'
        bildirim_olustur(
            alici=rez.kullanici,
            tip='REZERVASYON',
            mesaj=f'{rez.mekan.ad} rezervasyonunuz {mesaj}.',
            link=f'/rezervasyonlarim/',
        )
        messages.success(request, f'Rezervasyon {mesaj}.')
    return redirect('owner_dashboard')


# ── Kampanyalar ───────────────────────────────────────────────────────────────

@owner_required
def kampanya_olustur(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id, sahibi=request.user)
    if request.method == 'POST':
        form = KampanyaForm(request.POST, request.FILES)
        if form.is_valid():
            kampanya = form.save(commit=False)
            kampanya.mekan = mekan
            kampanya.save()
            for takipci in mekan.sahibi.takipcileri.select_related('takipci').all():
                bildirim_olustur(
                    alici=takipci.takipci,
                    tip='KAMPANYA',
                    mesaj=f'{mekan.ad} yeni kampanya başlattı: {kampanya.baslik}',
                    link=f'/mekan/{mekan.id}/',
                )
            messages.success(request, 'Kampanya oluşturuldu.')
            return redirect('owner_dashboard')
    else:
        form = KampanyaForm()
    return render(request, 'venues/kampanya_form.html', {'form': form, 'mekan': mekan})


@owner_required
@require_POST
def kampanya_sil(request, kampanya_id):
    kampanya = get_object_or_404(Kampanya, id=kampanya_id, mekan__sahibi=request.user)
    kampanya.delete()
    messages.success(request, 'Kampanya silindi.')
    return redirect('owner_dashboard')


# ── Menü Yönetimi ─────────────────────────────────────────────────────────────

@owner_required
def menu_yukle(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id, sahibi=request.user)
    if request.method == 'POST':
        form = MenuForm(request.POST, request.FILES, instance=mekan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menü güncellendi.')
        return redirect('owner_dashboard')
    return redirect('owner_dashboard')


# ── Çalışma Saatleri (Günlük) ─────────────────────────────────────────────────

@owner_required
def calisma_saatleri_duzenle(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id, sahibi=request.user)
    gun_adlari   = dict(CalismaGunu.GUN_SECENEKLERI)
    gun_kisaltma = {0:'Pzt', 1:'Sal', 2:'Çar', 3:'Per', 4:'Cum', 5:'Cmt', 6:'Paz'}
    gun_emoji    = {0:'📅', 1:'📅', 2:'📅', 3:'📅', 4:'🎯', 5:'🎉', 6:'😴'}

    if request.method == 'POST':
        ilk_acilis = None
        ilk_kapanis = None
        for gun_no in range(7):
            acik    = request.POST.get(f'gun_{gun_no}_acik') == 'on'
            acilis  = request.POST.get(f'gun_{gun_no}_acilis') or None
            kapanis = request.POST.get(f'gun_{gun_no}_kapanis') or None
            CalismaGunu.objects.update_or_create(
                mekan=mekan, gun=gun_no,
                defaults={'acik': acik, 'acilis': acilis, 'kapanis': kapanis}
            )
            if acik and acilis and ilk_acilis is None:
                ilk_acilis = acilis
                ilk_kapanis = kapanis
        mekan.acilis_saati = ilk_acilis
        mekan.kapanis_saati = ilk_kapanis
        mekan.save(update_fields=['acilis_saati', 'kapanis_saati'])
        messages.success(request, 'Çalışma saatleri güncellendi.')
        return redirect('owner_dashboard')

    gunler = {g.gun: g for g in mekan.calisma_gunleri.all()}
    gun_listesi = []
    for i in range(7):
        gun_listesi.append({
            'no':     i,
            'ad':     gun_adlari[i],
            'kisalt': gun_kisaltma[i],
            'emoji':  gun_emoji[i],
            'obj':    gunler.get(i),
        })
    return render(request, 'venues/calisma_saatleri.html', {
        'mekan': mekan,
        'gun_listesi': gun_listesi,
    })


# ── Anlık Duyuru (Takipçilere) ────────────────────────────────────────────────

@owner_required
@require_POST
def duyuru_yayinla(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id, sahibi=request.user)
    duyuru = request.POST.get('duyuru', '').strip()
    if duyuru:
        mekan.anlik_duyuru = duyuru
        mekan.save(update_fields=['anlik_duyuru'])
        for t in mekan.sahibi.takipcileri.select_related('takipci').all():
            bildirim_olustur(
                alici=t.takipci,
                tip='DUYURU',
                mesaj=f'{mekan.ad}: {duyuru[:80]}',
                link=f'/mekan/{mekan.id}/',
            )
        messages.success(request, f'Duyuru yayınlandı ve {mekan.sahibi.takipcileri.count()} takipçiye bildirildi.')
    return redirect('owner_dashboard')


# ── Popüler Mekanlar (Algoritma) ──────────────────────────────────────────────

@login_required
def populer_mekanlar(request):
    from django.db.models import Count as DCount
    mekanlar = Mekan.objects.filter(is_approved=True).annotate(
        ort_puan=Avg('yorumlar__puan'),
        yorum_c=DCount('yorumlar'),
        favori_c=DCount('favorileyenler'),
    )

    def skor(m):
        return (
            (m.goruntuleme_sayisi or 0) * 0.1 +
            (m.yorum_c or 0) * 30 +
            (float(m.ort_puan) if m.ort_puan else 0) * 20 +
            (m.favori_c or 0) * 40 +
            (m.doluluk_orani or 0) * 0.1
        )

    sirali = sorted(mekanlar, key=skor, reverse=True)[:20]
    return render(request, 'venues/liste.html', {
        'mekanlar': sirali,
        'baslik': 'Şu An Popüler',
        'page_obj': None,
        'sayfa_araligi': [],
    })


# ── Etkinlik Takvimi ──────────────────────────────────────────────────────────

@login_required
def etkinlik_takvimi(request):
    import json as _json
    from django.utils import timezone as tz

    filtre = request.GET.get('filtre', 'tumu')  # tumu | takip | favori

    etkinlikler = Etkinlik.objects.filter(bitis__gte=tz.now()).select_related('mekan').order_by('baslangic')

    if filtre == 'takip':
        # Takip edilen kullanıcıların sahip olduğu mekanlardaki etkinlikler
        takip_edilen_ids = request.user.takip_ettikleri.values_list('takip_edilen_id', flat=True)
        etkinlikler = etkinlikler.filter(mekan__sahibi_id__in=takip_edilen_ids)
    elif filtre == 'favori':
        # Kullanıcının favori mekanlarındaki etkinlikler
        favori_mekan_ids = request.user.favori_mekanlar.values_list('id', flat=True)
        etkinlikler = etkinlikler.filter(mekan_id__in=favori_mekan_ids)

    renk_map = {'tumu': '#2563eb', 'takip': '#7c3aed', 'favori': '#dc2626'}
    renk = renk_map.get(filtre, '#2563eb')

    events = []
    for e in etkinlikler:
        events.append({
            'id': e.id,
            'title': f"{e.baslik} @ {e.mekan.ad}",
            'start': e.baslangic.isoformat(),
            'end': e.bitis.isoformat(),
            'url': f'/mekan/{e.mekan_id}/',
            'color': renk,
        })
    return render(request, 'venues/etkinlik_takvimi.html', {
        'events_json': _json.dumps(events, ensure_ascii=False),
        'etkinlikler': etkinlikler,
        'aktif_filtre': filtre,
    })
