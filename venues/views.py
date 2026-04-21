from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required 
from .models import Mekan

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