# Em cardapio/admin.py

from django.contrib import admin
from .models import (
    Categoria, Produto, Bairro, Cliente, Pedido, ItemPedido, 
    ConfiguracaoLoja, Insumo, ItemReceita
)

# Admin para Insumos
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'unidade_medida', 'estoque_atual', 'custo_unidade')
    list_editable = ('estoque_atual', 'custo_unidade')
    search_fields = ('nome',)

# Inline para montar a receita diretamente na página do Produto
class ItemReceitaInline(admin.TabularInline):
    model = ItemReceita
    extra = 1  # Começa com 1 campo extra para adicionar insumo

# Atualiza o Admin de Produto para incluir a receita
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco','estoque','categoria',  'custo_de_producao', 'disponivel' )
    list_editable = ('preco', 'disponivel', 'estoque')
    list_filter = ('categoria', 'disponivel')
    search_fields = ('nome', 'descricao')
    readonly_fields = ('custo_de_producao',) # Mostra o custo, mas não permite editar
    inlines = [ItemReceitaInline] # A MÁGICA ACONTECE AQUI

# Admin para Categoria
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ordem', 'cor', 'icone_bootstrap')
    list_editable = ('ordem', 'cor', 'icone_bootstrap')

# Registros
admin.site.register(Insumo, InsumoAdmin)
admin.site.register(ConfiguracaoLoja)
admin.site.register(Bairro)
admin.site.register(Cliente) # Considere criar um ClienteAdmin se precisar
admin.site.register(Pedido) # Considere criar um PedidoAdmin se precisar

# Garante que os modelos antigos estão usando os novos Admins
try:
    admin.site.unregister(Produto)
    admin.site.unregister(Categoria)
except admin.sites.NotRegistered:
    pass
admin.site.register(Produto, ProdutoAdmin)
admin.site.register(Categoria, CategoriaAdmin)