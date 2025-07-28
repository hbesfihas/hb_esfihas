from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from cardapio.views import home, finalizar_pedido, login_cliente

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('finalizar/', finalizar_pedido, name='finalizar_pedido'),
    path('login/', login_cliente, name='login_cliente'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

