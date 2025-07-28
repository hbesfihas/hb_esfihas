from django.contrib import admin

# Register your models here.
from .models import Categoria, Produto, Bairro

admin.site.register(Categoria)
admin.site.register(Produto)
admin.site.register(Bairro)