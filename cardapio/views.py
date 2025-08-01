from decimal import Decimal
from django.shortcuts import render, redirect
from .models import Categoria, Produto, Cliente,Pedido, ItemPedido, Bairro
from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
import json
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from pixqrcodegen import Payload
import io 
import sys

def login_cliente(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        whatsapp = ''.join(filter(str.isdigit, request.POST.get('whatsapp', '')))
        if whatsapp:
            cliente, _ = Cliente.objects.get_or_create(whatsapp=whatsapp, defaults={'nome': nome})
            cliente.nome = nome
            cliente.save()
            login(request, cliente, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('home')  # redireciona de volta para a home


def home(request):
    cliente = request.user
    categorias = Categoria.objects.prefetch_related('produto_set').order_by('ordem')
    produtos = Produto.objects.all()
    return render(request, 'home.html', {'categorias': categorias, 'produtos': produtos, 'cliente': cliente,})


@login_required
def resumo_pedido(request):
    bairros = Bairro.objects.all().order_by('nome')
    taxa_cartao = settings.TAXA_CARTAO_PERCENTUAL  # Percentual fixo de taxa para cartão de crédito
    context = {
        'bairros': bairros,
        'taxa_cartao': taxa_cartao,
    }
    return render(request, 'resumo.html', context)

@login_required
def pedido_sucesso(request, pedido_id):
    # 1. Busca o pedido no banco de dados
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=request.user)
    
    # 2. GERA O PAYLOAD DO PIX 
    # Removemos a verificação 'if forma_pagamento == pix'
    payload = Payload(
        nome=settings.NOME_LOJA,
        cidade=settings.CIDADE_LOJA,
        chavepix=settings.CHAVE_PIX,
        valor=f"{pedido.total:.2f}",
        txtId=f"PEDIDO{pedido.id:04}"
    )
    
    # --- Bloco para capturar a saída do console ---
    
    # Guarda o "console" original em uma variável temporária
    old_stdout = sys.stdout
    # Redireciona a saída do sistema para um "buffer" de texto na memória
    redirected_output = sys.stdout = io.StringIO()
    
    # Executa a função. Em vez de imprimir no seu terminal,
    # ela agora vai imprimir no nosso "buffer" de texto.
    payload.gerarPayload()
    
    # Restaura o "console" original. É muito importante fazer isso!
    sys.stdout = old_stdout
    
    # Pega o que foi "impresso" no buffer e guarda na nossa variável
    pix_payload = redirected_output.getvalue().strip()
    
    # --- Fim do bloco de captura ---
   
    context = {
        'pedido': pedido,
        'pix_payload': pix_payload  # Esta variável agora sempre terá um valor
    }
    return render(request, 'pedido_sucesso.html', context)

@login_required
def pagina_finalizar_pedido(request):
    bairros = Bairro.objects.all().order_by('nome')
    taxa_cartao = settings.TAXA_CARTAO_PERCENTUAL

    context = {
        'bairros': bairros,
        'taxa_cartao': taxa_cartao,
    }
    return render(request, 'finalizar_pedido.html', context)

@login_required
def criar_pedido(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Método não permitido")

    try:
        # 1. Obter dados do formulário
        dados_sacola = json.loads(request.POST.get('sacola', '{}'))
        tipo_entrega = request.POST.get('tipo_entrega')
        bairro_id = request.POST.get('bairro')
        endereco = request.POST.get('endereco', '').strip()
        forma_pagamento = request.POST.get('forma_pagamento') # Adicionado para taxa

        if not dados_sacola or not tipo_entrega:
            return HttpResponseBadRequest("Dados incompletos.")

        # 2. Buscar todos os produtos do DB de uma vez (Mais eficiente)
        ids_produtos = list(dados_sacola.keys())
        produtos_no_db = Produto.objects.in_bulk([int(pid) for pid in ids_produtos])

        # 3. Recalcular totais no SERVIDOR (Passo de segurança essencial)
        subtotal_pedido = Decimal("0.00")
        for produto_id, item_sacola in dados_sacola.items():
            produto_db = produtos_no_db.get(int(produto_id))
            if produto_db:
                # Usa o preço do BANCO DE DADOS, não o do cliente!
                subtotal_pedido += produto_db.preco * int(item_sacola['quantidade'])
            else:
                return HttpResponseBadRequest(f"Produto com ID {produto_id} não encontrado.")

        # 4. Calcular frete e taxas
        valor_frete = Decimal("0.00")
        bairro = None
        if tipo_entrega == 'entrega' and bairro_id:
            bairro = get_object_or_404(Bairro, id=bairro_id)
            valor_frete = bairro.valor_frete # CORRIGIDO: usando 'valor_frete'

        taxa_cartao = Decimal("0.00")
        if forma_pagamento == 'cartao_credito':
            taxa_percentual = Decimal(str(settings.TAXA_CARTAO_PERCENTUAL))
            taxa_cartao = (subtotal_pedido + valor_frete) * (taxa_percentual / 100)

        total_final = subtotal_pedido + valor_frete + taxa_cartao
        
        # 5. Criar o Pedido no banco de dados
        pedido = Pedido.objects.create(
            cliente=request.user,
            tipo_entrega=tipo_entrega,
            total=total_final.quantize(Decimal("0.01")),
            bairro=bairro, # Para isso funcionar, veja o Passo 3
            endereco_entrega=endereco if tipo_entrega == 'entrega' else '',
            forma_pagamento=forma_pagamento,
        )

        # 6. Criar os Itens do Pedido
        for produto_id, item_sacola in dados_sacola.items():
            produto_db = produtos_no_db.get(int(produto_id))
            quantidade = int(item_sacola['quantidade'])
            
            ItemPedido.objects.create(
                pedido=pedido,
                produto=produto_db,
                quantidade=quantidade,
                subtotal=(produto_db.preco * quantidade).quantize(Decimal("0.01"))
            )

        # 7. Redirecionar para a página de sucesso
        return redirect('pedido_sucesso', pedido_id=pedido.id)

    except Exception as e:
        return HttpResponseBadRequest(f"Erro ao criar pedido: {str(e)}")

@login_required
def meus_pedidos(request):
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-criado_em')
    return render(request, 'meus_pedidos.html', {'pedidos': pedidos})


@staff_member_required
def painel_gerente(request):
    pedidos = Pedido.objects.all().order_by('-criado_em')
    return render(request, 'painel_gerente.html', {'pedidos': pedidos})

@staff_member_required
def atualizar_status_pedido(request, pedido_id, novo_status):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    pedido.status = novo_status
    pedido.save()
    return redirect('painel_gerente')
