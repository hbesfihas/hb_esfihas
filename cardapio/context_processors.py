# Arquivo: cardapio/context_processors.py

from .models import ConfiguracaoLoja

def configuracao_loja(request):
    # Tenta buscar a configuração. Se não existir, cria a primeira.
    config, created = ConfiguracaoLoja.objects.get_or_create(pk=1)
    return {'configuracao_loja': config}