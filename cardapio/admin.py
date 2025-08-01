from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# Register your models here.
from .models import Categoria, Produto, Bairro, Cliente, Pedido, ItemPedido

admin.site.register(Categoria)
admin.site.register(Produto)
admin.site.register(Bairro)
admin.site.register(Cliente)
admin.site.register(Pedido)
admin.site.register(ItemPedido) 
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'whatsapp', 'pontos', 'is_admin', 'is_active')