from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# Register your models here.
from .models import Categoria, Produto, Bairro, Cliente, Pedido, ItemPedido, ConfiguracaoLoja

class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ordem', 'cor', 'icone_bootstrap')
    list_editable = ('ordem', 'cor', 'icone_bootstrap')

# Garanta que o Categoria está registrado com o CategoriaAdmin
admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Bairro)
admin.site.register(Cliente)
admin.site.register(Pedido)
admin.site.register(ItemPedido) 
admin.site.register(ConfiguracaoLoja)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'whatsapp', 'pontos', 'is_admin', 'is_active')
    
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco', 'disponivel', 'estoque')
    list_editable = ('preco', 'disponivel', 'estoque') # Permite editar na lista
    list_filter = ('categoria', 'disponivel')
    search_fields = ('nome', 'descricao')

# Garanta que o Produto está registrado com o ProdutoAdmin
# Se já houver um admin.site.register(Produto), remova-o
try:
    admin.site.unregister(Produto)
except admin.sites.NotRegistered:
    pass
admin.site.register(Produto, ProdutoAdmin)

