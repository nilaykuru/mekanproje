from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Mekan, Yorum, Profile, Etkinlik
from .forms import YorumForm, MekanForm, EtkinlikForm


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


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            secilen_rol = request.POST.get('rol', 'USER')
            Profile.objects.create(user=user, rol=secilen_rol)
            messages.success(request, "Hesabınız oluşturuldu! Lütfen giriş yapın.")
            return redirect('login')
    else:
        form = UserCreationForm()
    default_rol = request.GET.get('rol', 'USER')
    return render(request, 'venues/register.html', {'form': form, 'default_rol': default_rol})


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
    mekanlar = Mekan.objects.all()
    return render(request, 'venues/index.html', {'mekanlar': mekanlar})


@login_required(login_url='login')
def arama(request):
    q = request.GET.get('q', '').strip()
    if q:
        mekanlar = Mekan.objects.filter(
            Q(ad__icontains=q) | Q(adres__icontains=q) | Q(kategori__icontains=q)
        )
        baslik = f'"{q}" için {mekanlar.count()} sonuç'
    else:
        mekanlar = Mekan.objects.all()
        baslik = 'Tüm Mekanlar'
    return render(request, 'venues/liste.html', {'mekanlar': mekanlar, 'baslik': baslik, 'q': q})


def su_an_acik_olanlar(request):
    mekanlar = Mekan.objects.filter(su_an_acik=True)
    return render(request, 'venues/liste.html', {'mekanlar': mekanlar, 'baslik': 'Şu An Açık Olan Mekanlar'})


def calisma_alanlari(request):
    mekanlar = Mekan.objects.filter(priz_var=True, kategori__in=['KUTUPHANE'])
    return render(request, 'venues/liste.html', {'mekanlar': mekanlar, 'baslik': 'Çalışma Alanları'})


def acil_ihtiyaclar(request):
    mekanlar = Mekan.objects.filter(kategori='ECZANE')
    return render(request, 'venues/liste.html', {'mekanlar': mekanlar, 'baslik': 'Nöbetçi/Açık Eczaneler'})


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
    mekanlar = request.user.favori_mekanlar.all()
    return render(request, 'venues/liste.html', {'mekanlar': mekanlar, 'baslik': 'Favori Mekanlarım'})


def mekan_detay(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id)
    yorumlar = mekan.yorumlar.all().order_by('-tarih')
    etkinlikler = mekan.aktif_etkinlikler()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = YorumForm(request.POST, request.FILES)
        if form.is_valid():
            yeni_yorum = form.save(commit=False)
            yeni_yorum.mekan = mekan
            yeni_yorum.yazar = request.user
            yeni_yorum.save()
            return redirect('mekan_detay', mekan_id=mekan.id)
    else:
        form = YorumForm()

    return render(request, 'venues/mekan_detay.html', {
        'mekan': mekan,
        'yorumlar': yorumlar,
        'etkinlikler': etkinlikler,
        'form': form,
    })


# ── Mekan Sahibi Paneli ────────────────────────────────────────────────────────

@owner_required
def mekan_sahibi_paneli(request):
    mekanlarim = request.user.mekanlari.prefetch_related('etkinlikler').all()
    return render(request, 'venues/owner_dashboard.html', {'mekanlar': mekanlarim})


@owner_required
def mekan_olustur(request):
    if request.method == 'POST':
        form = MekanForm(request.POST, request.FILES)
        if form.is_valid():
            mekan = form.save(commit=False)
            mekan.sahibi = request.user
            mekan.save()
            messages.success(request, f'"{mekan.ad}" başarıyla oluşturuldu! Admin onayından sonra yayınlanacak.')
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


# ── Eski duyuru_guncelle (geriye dönük uyumluluk) ─────────────────────────────

@login_required
def duyuru_guncelle(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id, sahibi=request.user)
    if request.method == 'POST':
        mekan.anlik_duyuru = request.POST.get('duyuru', '')
        mekan.save(update_fields=['anlik_duyuru'])
        messages.success(request, "Duyuru güncellendi!")
    return redirect('owner_dashboard')
