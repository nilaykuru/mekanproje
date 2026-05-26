from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Yorum, Mekan, Etkinlik


class YorumForm(forms.ModelForm):
    class Meta:
        model = Yorum
        fields = ['icerik', 'fotoğraf']
        widgets = {
            'icerik': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Mekan hakkında ne düşünüyorsun?',
                'rows': 3,
                'style': 'width: 100%; border-radius: 8px; padding: 10px; border: 1px solid #ddd;'
            }),
        }


INPUT_STYLE = 'width: 100%; padding: 10px 14px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; box-sizing: border-box;'


class KayitFormu(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'style': INPUT_STYLE,
            'placeholder': 'ornek@email.com',
        }),
        label='E-posta',
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
CHECKBOX_STYLE = 'width: 18px; height: 18px; margin-right: 8px; accent-color: #0056b3;'


class MekanForm(forms.ModelForm):
    class Meta:
        model = Mekan
        fields = [
            'ad', 'kategori', 'sehir', 'adres', 'telefon', 'website',
            'img', 'ruhsat_belgesi', 'acilis_saati', 'kapanis_saati',
            'su_an_acik', 'doluluk_orani', 'anlik_duyuru',
            'latitude', 'longitude',
            'wifi_var', 'priz_var', 'otopark_var', 'sigara_icin_uygun',
            'bahce_var', 'engelli_erisimi_var', 'canli_muzik_var',
            'evcil_hayvan_izinli', 'cocuk_oyun_alani_var',
        ]
        widgets = {
            'ad': forms.TextInput(attrs={'style': INPUT_STYLE, 'placeholder': 'Mekan adı'}),
            'kategori': forms.Select(attrs={'style': INPUT_STYLE}),
            'sehir': forms.Select(attrs={'style': INPUT_STYLE}),
            'adres': forms.Textarea(attrs={'style': INPUT_STYLE, 'rows': 2, 'placeholder': 'Tam adres'}),
            'telefon': forms.TextInput(attrs={'style': INPUT_STYLE, 'placeholder': '0212 000 00 00'}),
            'website': forms.URLInput(attrs={'style': INPUT_STYLE, 'placeholder': 'https://...'}),
            'acilis_saati': forms.TimeInput(attrs={'style': INPUT_STYLE, 'type': 'time'}),
            'kapanis_saati': forms.TimeInput(attrs={'style': INPUT_STYLE, 'type': 'time'}),
            'doluluk_orani': forms.NumberInput(attrs={'style': INPUT_STYLE, 'min': 0, 'max': 100}),
            'anlik_duyuru': forms.TextInput(attrs={'style': INPUT_STYLE, 'placeholder': 'Bugün mekanda neler var?'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'wifi_var': forms.CheckboxInput(attrs={'style': CHECKBOX_STYLE}),
            'priz_var': forms.CheckboxInput(attrs={'style': CHECKBOX_STYLE}),
            'otopark_var': forms.CheckboxInput(attrs={'style': CHECKBOX_STYLE}),
            'sigara_icin_uygun': forms.CheckboxInput(attrs={'style': CHECKBOX_STYLE}),
            'bahce_var': forms.CheckboxInput(attrs={'style': CHECKBOX_STYLE}),
            'engelli_erisimi_var': forms.CheckboxInput(attrs={'style': CHECKBOX_STYLE}),
            'canli_muzik_var': forms.CheckboxInput(attrs={'style': CHECKBOX_STYLE}),
            'evcil_hayvan_izinli': forms.CheckboxInput(attrs={'style': CHECKBOX_STYLE}),
            'cocuk_oyun_alani_var': forms.CheckboxInput(attrs={'style': CHECKBOX_STYLE}),
            'su_an_acik': forms.CheckboxInput(attrs={'style': CHECKBOX_STYLE}),
        }
        # Ruhsat belgesi dosya alanı
        ruhsat_belgesi = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'style': 'width:100%;'}))


class EtkinlikForm(forms.ModelForm):
    class Meta:
        model = Etkinlik
        fields = ['baslik', 'aciklama', 'baslangic', 'bitis', 'foto']
        widgets = {
            'baslik': forms.TextInput(attrs={'style': INPUT_STYLE, 'placeholder': 'Etkinlik başlığı'}),
            'aciklama': forms.Textarea(attrs={'style': INPUT_STYLE, 'rows': 3, 'placeholder': 'Etkinlik detayları...'}),
            'baslangic': forms.DateTimeInput(attrs={'style': INPUT_STYLE, 'type': 'datetime-local'}),
            'bitis': forms.DateTimeInput(attrs={'style': INPUT_STYLE, 'type': 'datetime-local'}),
        }
