from django.contrib import admin
from .models import Mekan
from .models import Yorum

admin.site.register(Mekan)
@admin.register(Yorum)
class YorumAdmin(admin.ModelAdmin):
    list_display = ('yazar', 'mekan', 'tarih')
    list_filter = ('tarih', 'mekan')
    search_fields = ('icerik', 'yazar__username')