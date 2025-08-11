# Arquivo: hb_esfihas/urls.py

from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.urls import re_path
from django.views.static import serve
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Importe apenas as views que você realmente usa
from cardapio.views import (
    home, criar_pedido,
    login_cliente, resumo_pedido,
    pedido_sucesso, meus_pedidos,
    atualizar_status_pedido,
    painel_gerente, imprimir_pedido,
    toggle_loja_status_api, toggle_pago_status_api,
    logout_cliente, dashboard_vendas, validar_estoque_api, save_webpush_subscription, service_worker
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('login/', login_cliente, name='login_cliente'),
    path('logout/', logout_cliente, name='logout_cliente'),
    path('finalizar/', resumo_pedido, name='resumo_pedido'),
    path('criar_pedido/', criar_pedido, name='criar_pedido'),
    path('pedido/sucesso/<int:pedido_id>/', pedido_sucesso, name='pedido_sucesso'),
    path('meus-pedidos/', meus_pedidos, name='meus_pedidos'),
    path('painel-gerente/', painel_gerente, name='painel_gerente'),
    path('atualizar-status/<int:pedido_id>/<str:novo_status>/', atualizar_status_pedido, name='atualizar_status_pedido'),
    path('api/toggle-loja-status/', toggle_loja_status_api, name='toggle_loja_status_api'),
    path('imprimir-pedido/<int:pedido_id>/', imprimir_pedido , name= 'imprimir_pedido'),  # Exemplo de URL para imprimir pedido
    path('api/toggle-pago-status/<int:pedido_id>/', toggle_pago_status_api, name='toggle_pago_status_api'),  # Nova URL para alternar status pago
    path('dashboard/', dashboard_vendas, name='dashboard_vendas'),
    path('api/validar-estoque/', validar_estoque_api, name='validar_estoque_api'),  # Nova URL para validar estoque
    path('api/save-subscription/', save_webpush_subscription, name='save_webpush_subscription'),
    path('serviceworker.js', service_worker, name='service_worker'),

]

# --- CONFIGURAÇÃO CORRETA E ROBUSTA PARA FICHEIROS ESTÁTICOS E DE MÍDIA ---
# Esta linha serve os seus ficheiros estáticos (CSS, JS) através do WhiteNoise
urlpatterns += staticfiles_urlpatterns()
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]