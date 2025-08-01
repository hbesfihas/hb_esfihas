from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from cardapio.views import home, criar_pedido, login_cliente, resumo_pedido, pedido_sucesso, meus_pedidos, atualizar_status_pedido, painel_gerente

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('login/', login_cliente, name='login_cliente'),
    path('finalizar/', resumo_pedido, name='resumo_pedido'),
    path('criar_pedido/', criar_pedido, name='criar_pedido'),
    path('pedido/sucesso/<int:pedido_id>', pedido_sucesso, name='pedido_sucesso'),
    path('meus-pedidos/', meus_pedidos, name='meus_pedidos'),
    path('painel-gerente/', painel_gerente, name='painel_gerente'),
    path('atualizar-status/<int:pedido_id>/<str:novo_status>/', atualizar_status_pedido, name='atualizar_status_pedido'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

