# venues/forms.py
from django import forms
from .models import Yorum

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