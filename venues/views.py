from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required 
from .models import Mekan
from django.shortcuts import get_object_or_404
from django.shortcuts import render, get_object_or_404, redirect
from .models import Mekan, Yorum
from .forms import YorumForm

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'venues/landing.html')

@login_required(login_url='login') 
def dashboard(request):
    mekanlar = Mekan.objects.all()
    return render(request, 'venues/index.html', {'mekanlar': mekanlar})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Hesabınız oluşturuldu! Lütfen giriş yapın.")
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'venues/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard') 
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı!")
    else:
        form = AuthenticationForm()
    return render(request, 'venues/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('landing') 

def su_an_acik_olanlar(request):
    mekanlar = Mekan.objects.filter(su_an_acik=True)
    return render(request, 'venues/liste.html', {'mekanlar': mekanlar, 'baslik': 'Şu An Açık Olan Mekanlar'})

def calisma_alanlari(request):
    # Hem prizi olan hem de Kütüphane olanları getir
    mekanlar = Mekan.objects.filter(priz_var=True, kategori__in=['KUTUPHANE'])
    return render(request, 'venues/liste.html', {'mekanlar': mekanlar, 'baslik': 'Çalışma Alanları'})

def acil_ihtiyaclar(request):
    mekanlar = Mekan.objects.filter(kategori='ECZANE')
    return render(request, 'venues/liste.html', {'mekanlar': mekanlar, 'baslik': 'Nöbetçi/Açık Eczaneler'})

@login_required
def favori_islem(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id)
    # Eğer kullanıcı zaten favorilemişse listeden çıkar, yoksa ekle
    if mekan.favorileyenler.filter(id=request.user.id).exists():
        mekan.favorileyenler.remove(request.user)
    else:
        mekan.favorileyenler.add(request.user)
    
    # Kullanıcıyı geldiği sayfaya geri gönder
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def favorilerim(request):
    # Giriş yapan kullanıcının favorilediği tüm mekanları getir
    mekanlar = request.user.favori_mekanlar.all()
    return render(request, 'venues/liste.html', {'mekanlar': mekanlar, 'baslik': 'Favori Mekanlarım'})

def mekan_detay(request, mekan_id):
    mekan = get_object_or_404(Mekan, id=mekan_id)
    yorumlar = mekan.yorumlar.all().order_by('-tarih') # En yeni yorum en üstte
    
    if request.method == 'POST':
        form = YorumForm(request.POST, request.FILES) # Fotoğraf için request.FILES şart!
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
        'form': form
    })

