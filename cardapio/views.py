from decimal import Decimal
from django.shortcuts import render, redirect ,get_object_or_404
from .models import Categoria, Produto, Cliente,Pedido, ItemPedido, Bairro, ConfiguracaoLoja, WebPushSubscription
from django.contrib.auth import login, logout
from django.http import JsonResponse, HttpResponseBadRequest
import json
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from pixqrcodegen import Payload
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.template.loader import render_to_string
import io
import sys
from django.utils import timezone
from django.db.models import Sum, Q, Count, Prefetch
from django.db.models.functions import Trunc
from datetime import timedelta
from django.db import transaction
from webpush import send_user_notification

def service_worker(request):
    return render(request, 'serviceworker.js', content_type='application/javascript')

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

def logout_cliente(request):
    logout(request)
    return redirect('login_cliente')  # redireciona para a página de login

def home(request):
    if request.user.is_authenticated:
        cliente = request.user
        produtos_ordenados = Produto.objects.filter(disponivel=True).order_by('ordem')
        categorias = Categoria.objects.prefetch_related(
            Prefetch('produto_set', queryset=produtos_ordenados, to_attr='produtos_ordenados')
        ).order_by('ordem')
        produtos = Produto.objects.all()
        return render(request, 'home.html', {'categorias': categorias, 'produtos': produtos, 'cliente': cliente,})
    else:
        return render(request, 'login_cliente.html')

@login_required
def resumo_pedido(request):
    bairros = Bairro.objects.all().order_by('nome')
    taxa_cartao = settings.TAXA_CARTAO_PERCENTUAL  # Percentual fixo de taxa para cartão de crédito
    context = {
        'bairros': bairros,
        'taxa_cartao_percentual': taxa_cartao,
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
    pontos_ganhos = int(pedido.total // 10)

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
        'pix_payload': pix_payload,  # Esta variável agora sempre terá um valor
        'pontos_ganhos': pontos_ganhos,
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
        # transaction.atomic garante que ou tudo funciona, ou nada é salvo.
        with transaction.atomic():
            # 1. PEGAR TODOS OS DADOS DA REQUISIÇÃO
            dados_sacola = json.loads(request.POST.get('sacola', '{}'))
            tipo_entrega = request.POST.get('tipo_entrega')
            bairro_id = request.POST.get('bairro')
            endereco = request.POST.get('endereco', '').strip()
            forma_pagamento = request.POST.get('forma_pagamento')
            troco_para = request.POST.get('troco_para', None)
            if not dados_sacola or not tipo_entrega:
                return HttpResponseBadRequest("Dados do pedido estão incompletos.")

            # 2. BUSCAR PRODUTOS E VALIDAR ESTOQUE EM UMA ÚNICA PASSAGEM
            ids_produtos = [int(pid) for pid in dados_sacola.keys()]
            produtos_no_db = {p.id: p for p in Produto.objects.filter(id__in=ids_produtos)}

            subtotal_pedido = Decimal("0.00")
            for produto_id_str, item_sacola in dados_sacola.items():
                produto_id = int(produto_id_str)
                produto_db = produtos_no_db.get(produto_id)
                quantidade_pedida = item_sacola['quantidade']

                # Validação de segurança e estoque
                if not produto_db or produto_db.estoque < quantidade_pedida:
                    nome_produto = produto_db.nome if produto_db else f"ID {produto_id}"
                    return HttpResponseBadRequest(f"Desculpe, o produto '{nome_produto}' não tem estoque suficiente.")

                # Recalcula o subtotal com o preço do banco de dados (segurança)
                subtotal_pedido += produto_db.preco * quantidade_pedida

            # 3. CALCULAR FRETE E TAXAS
            valor_frete = Decimal("0.00")
            bairro = None
            if tipo_entrega == 'entrega' and bairro_id:
                bairro = get_object_or_404(Bairro, id=bairro_id)
                valor_frete = bairro.valor_frete

            taxa_cartao = Decimal("0.00")
            if forma_pagamento == 'cartao_credito':
                taxa_percentual = Decimal(str(settings.TAXA_CARTAO_PERCENTUAL))
                taxa_cartao = (subtotal_pedido + valor_frete) * (taxa_percentual / 100)

            total_final = subtotal_pedido + valor_frete + taxa_cartao



            # 4. CRIAR O PEDIDO
            pedido = Pedido.objects.create(
                cliente=request.user,
                tipo_entrega=tipo_entrega,
                total=total_final.quantize(Decimal("0.01")),
                bairro=bairro,
                endereco_entrega=endereco if tipo_entrega == 'entrega' else '',
                forma_pagamento=forma_pagamento,
                troco_para=Decimal(troco_para).quantize(Decimal("0.01")) if troco_para else None,
            )

            # 5. CRIAR ITENS DO PEDIDO E DAR BAIXA NO ESTOQUE
            for produto_id_str, item_sacola in dados_sacola.items():
                produto_db = produtos_no_db[int(produto_id_str)]
                quantidade = int(item_sacola['quantidade'])

                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=produto_db,
                    quantidade=quantidade,
                    subtotal=(produto_db.preco * quantidade).quantize(Decimal("0.01"))
                )

                # A LÓGICA CORRIGIDA E ADICIONADA:
                produto_db.estoque -= quantidade
                produto_db.save(update_fields=['estoque'])

            # 6. ATRIBUIR PONTOS
            cliente = request.user
            pontos_ganhos = int(total_final // 10)
            if pontos_ganhos > 0:
                cliente.pontos += pontos_ganhos
                cliente.save(update_fields=['pontos'])

            # --- LÓGICA PARA SALVAR O ÚLTIMO ENDEREÇO ---
            if tipo_entrega == 'entrega':
                cliente = request.user
                cliente.ultimo_endereco = endereco
                cliente.ultimo_bairro = bairro
                cliente.save(update_fields=['ultimo_endereco', 'ultimo_bairro'])
            # --- FIM DA LÓGICA ---

            # 7. NOTIFICAR GERENTES VIA WEBSOCKET
            html_pedido = render_to_string(
                'partials/card_pedido_gerente.html',
                {'pedido': pedido, 'request': request}
            )
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'gerentes',
                {'type': 'novo_pedido', 'pedido_html': html_pedido}
            )
            # --- ENVIO DA PUSH NOTIFICATION (MÉTODO CORRETO E FINAL) ---
            print("\n--- [DEBUG PUSH] A iniciar envio de notificação push ---")
            try:
                # 1. Encontra todos os utilizadores que são gerentes
                gerentes = Cliente.objects.filter(is_admin=True)
                print(f"[DEBUG PUSH] Gerentes encontrados: {[user.nome for user in gerentes]}")

                if gerentes.exists():
                    payload = {
                        "head": f"Novo Pedido! #{pedido.id}",
                        "body": f"Cliente: {pedido.cliente.nome}\nTotal: R$ {pedido.total}",
                        "icon": request.build_absolute_uri('/static/img/favicon.ico'),
                        "url": "/painel-gerente/"
                    }
                    print("[DEBUG PUSH] Payload da notificação:", payload)

                    # 2. Envia a notificação para cada gerente individualmente.
                    #    A função send_user_notification sabe como encontrar as subscrições do utilizador.
                    for gerente in gerentes:
                        send_user_notification(user=gerente, payload=payload, ttl=1000)

                    print(f"✅ [DEBUG PUSH] Notificação enviada para {gerentes.count()} gerente(s).")
                else:
                    print("⚠️ [DEBUG PUSH] Nenhum gerente encontrado para enviar notificação push.")

            except Exception as e:
                print(f"❌ [DEBUG PUSH] ERRO AO ENVIAR NOTIFICAÇÃO PUSH: {e}")
            # --- FIM DO BLOCO DE ENVIO ---


        # Se a transação foi um sucesso, redireciona
        return redirect('pedido_sucesso', pedido_id=pedido.id)

    except Exception as e:
        # Se qualquer erro ocorrer dentro do 'with', a transação é desfeita
        return HttpResponseBadRequest(f"Erro ao criar pedido: {str(e)}")

@login_required
def meus_pedidos(request):
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-criado_em')
    return render(request, 'meus_pedidos.html', {'pedidos': pedidos})


@staff_member_required
def painel_gerente(request):
    # Pega os valores dos filtros. Usamos '' (string vazia) como padrão.
    data_filtro = request.GET.get('data', '')
    cliente_filtro_id = request.GET.get('cliente', '')
    pago_filtro = request.GET.get('pago', '')

    # Começa com todos os pedidos
    pedidos = Pedido.objects.exclude(status='cancelado').select_related('cliente', 'bairro').order_by('-criado_em')

    # Aplica os filtros apenas se um valor foi fornecido
    if cliente_filtro_id:
        pedidos = pedidos.filter(cliente_id=cliente_filtro_id)

    if data_filtro:
        pedidos = pedidos.filter(criado_em__date=data_filtro)

    if pago_filtro == 'sim':
        pedidos = pedidos.filter(pago=True)
    elif pago_filtro == 'nao':
        pedidos = pedidos.filter(pago=False)

    # Comportamento padrão: se a página for carregada sem NENHUM filtro, mostra os de hoje.
    if not request.GET:
        pedidos = pedidos.filter(criado_em__date=timezone.localdate())
        data_selecionada = timezone.localdate().strftime('%Y-%m-%d')
    else:
        data_selecionada = data_filtro

    todos_clientes = Cliente.objects.filter(is_admin=False).order_by('nome')

    context = {
        'pedidos': pedidos,
        'todos_clientes': todos_clientes,
        'data_selecionada': data_selecionada,
        'cliente_selecionado_id': int(cliente_filtro_id) if cliente_filtro_id else None,
        'pago_selecionado': pago_filtro,
    }
    return render(request, 'painel_gerente.html', context)

@staff_member_required
def atualizar_status_pedido(request, pedido_id, novo_status):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, pk=pedido_id)
        pedido.status = novo_status
        pedido.save()

        STATUS_CORES = {
            'pendente': 'bg-light',
            'preparando': 'bg-warning text-dark bg-opacity-50',
            'pronto': 'bg-info text-dark bg-opacity-50',
            'entregue': 'bg-success text-white bg-opacity-75',
            'cancelado': 'bg-secondary text-white bg-opacity-75'
        }

        # A mensagem agora tem sempre o mesmo formato
        message_data = {
            'type': 'status_update', # Sempre envia 'status_update'
            'message': {
                'pedido_id': pedido_id,
                'novo_status': pedido.get_status_display(), # 'Cancelado', 'Pronto', etc.
                'nova_cor_classe': STATUS_CORES.get(novo_status, 'bg-light')
            }
        }
        channel_layer = get_channel_layer()
        # 1. Envia para o grupo dos gerentes
        async_to_sync(channel_layer.group_send)('gerentes', message_data)


        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'erro'}, status=405)


# Em cardapio/views.py
from django.views.decorators.clickjacking import xframe_options_sameorigin

@xframe_options_sameorigin
@staff_member_required
def imprimir_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    taxa_cartao = Decimal("0.00")
    if pedido.forma_pagamento == 'cartao_credito':
        taxa_percentual = Decimal(str(settings.TAXA_CARTAO_PERCENTUAL))
        taxa_cartao = pedido.total * (taxa_percentual / 100)
        taxa_cartao = taxa_cartao.quantize(Decimal("0.01"))
    pedido.taxa_cartao = taxa_cartao
    context = {
        'pedido': pedido,
    }
    return render(request, 'imprimir_pedido.html', context)

@staff_member_required
def toggle_loja_status_api(request):
    if request.method == 'POST':
        config = ConfiguracaoLoja.objects.get(pk=1)
        config.loja_aberta = not config.loja_aberta
        config.save()

        # --- AVISO VIA WEBSOCKET PARA TODOS OS GERENTES ---
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'gerentes',
            {
                'type': 'store_status_update', # Novo tipo de mensagem
                'message': {
                    'loja_aberta': config.loja_aberta
                }
            }
        )
        # --- FIM DO AVISO ---

        return JsonResponse({'status': 'ok', 'loja_aberta': config.loja_aberta})
    return JsonResponse({'status': 'erro'}, status=405)

@staff_member_required
def toggle_pago_status_api(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=pedido_id)
        # Inverte o status atual (se era False, vira True, e vice-versa)
        pedido.pago = not pedido.pago
        pedido.save()
        return JsonResponse({'status': 'ok', 'pago': pedido.pago})
    return JsonResponse({'status': 'erro'}, status=405)

@staff_member_required
def dashboard_vendas(request):
    # --- 1. CÁLCULO DE CLIENTES DEVEDORES (continua o mesmo) ---
    clientes_devedores = Cliente.objects.filter(
        pedido__pago=False, is_admin=False
    ).annotate(
        total_nao_pago=Sum('pedido__total', filter=Q(pedido__pago=False))
    ).order_by('-total_nao_pago')

    # --- 2. CÁLCULO PARA O GRÁFICO (COM NOVOS PERÍODOS) ---
    periodo = request.GET.get('periodo', 'semana') # Padrão: semana
    hoje = timezone.localdate()

    # Base da queryset: apenas pedidos pagos
    queryset = Pedido.objects.filter(pago=True)

    # Mapeamento de meses para abreviações em português
    meses_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

    if periodo == 'hoje':
        queryset = queryset.filter(criado_em__date=hoje)
        chart_data = queryset.annotate(agrupador=Trunc('criado_em', 'hour')).values('agrupador').annotate(faturamento=Sum('total')).order_by('agrupador')
        labels = [item['agrupador'].strftime('%H:00') for item in chart_data]
    elif periodo == 'semana':
        data_inicio_semana = hoje - timedelta(days=hoje.weekday())
        queryset = queryset.filter(criado_em__date__gte=data_inicio_semana)
        chart_data = queryset.annotate(agrupador=Trunc('criado_em', 'day')).values('agrupador').annotate(faturamento=Sum('total')).order_by('agrupador')
        labels = [item['agrupador'].strftime('%d/%m') for item in chart_data]
    elif periodo == 'mes':
        queryset = queryset.filter(criado_em__year=hoje.year, criado_em__month=hoje.month)
        chart_data = queryset.annotate(agrupador=Trunc('criado_em', 'day')).values('agrupador').annotate(faturamento=Sum('total')).order_by('agrupador')
        labels = [item['agrupador'].strftime('%d/%m') for item in chart_data]
    elif periodo == 'trimestre':
        queryset = queryset.filter(criado_em__year=hoje.year)
        chart_data = queryset.annotate(agrupador=Trunc('criado_em', 'quarter')).values('agrupador').annotate(faturamento=Sum('total')).order_by('agrupador')
        labels = [f"{ (item['agrupador'].month-1)//3 + 1 }º Trim" for item in chart_data]
    elif periodo == 'ano':
        queryset = queryset.filter(criado_em__year=hoje.year)
        chart_data = queryset.annotate(agrupador=Trunc('criado_em', 'month')).values('agrupador').annotate(faturamento=Sum('total')).order_by('agrupador')
        labels = [meses_pt.get(item['agrupador'].month, '') for item in chart_data]
    else: # Fallback para semana
        data_inicio_semana = hoje - timedelta(days=hoje.weekday())
        queryset = queryset.filter(criado_em__date__gte=data_inicio_semana)
        chart_data = queryset.annotate(agrupador=Trunc('criado_em', 'day')).values('agrupador').annotate(faturamento=Sum('total')).order_by('agrupador')
        labels = [item['agrupador'].strftime('%d/%m') for item in chart_data]

    data = [float(item['faturamento']) for item in chart_data]

   # --- 3. NOVOS KPIs RÁPIDOS ---
    pedidos_pagos = Pedido.objects.filter(pago=True)
    faturamento_total_geral = pedidos_pagos.aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
    total_pedidos_pagos = pedidos_pagos.count()
    ticket_medio = faturamento_total_geral / total_pedidos_pagos if total_pedidos_pagos > 0 else Decimal('0.00')

    # --- 4. TOP 5 PRODUTOS MAIS VENDIDOS ---
    top_produtos = ItemPedido.objects.values('produto__nome').annotate(
        quantidade_vendida=Sum('quantidade')
    ).order_by('-quantidade_vendida')[:5]

    # --- 5. TOP 5 CLIENTES (POR VALOR GASTO) ---
    top_clientes = Cliente.objects.filter(is_admin=False, pedido__pago=True).annotate(
        total_gasto=Sum('pedido__total')
    ).order_by('-total_gasto')[:5]

    # --- 6. DADOS PARA O GRÁFICO DE PIZZA (TIPO DE ENTREGA) ---
    pedidos_por_tipo = Pedido.objects.values('tipo_entrega').annotate(
        total=Count('id')
    ).order_by('tipo_entrega')

    pie_chart_labels = [dict(Pedido.tipo_entrega.field.choices).get(item['tipo_entrega']) for item in pedidos_por_tipo]
    pie_chart_data = [item['total'] for item in pedidos_por_tipo]

    context = {
        'clientes_devedores': clientes_devedores,
        'chart_labels': json.dumps(labels),
        'chart_data': json.dumps(data),
        'periodo_selecionado': periodo,
        # Adicionando os novos dados ao contexto
        'faturamento_total_geral': faturamento_total_geral,
        'total_pedidos_pagos': total_pedidos_pagos,
        'ticket_medio': ticket_medio,
        'top_produtos': top_produtos,
        'top_clientes': top_clientes,
        'pie_chart_labels': json.dumps(pie_chart_labels),
        'pie_chart_data': json.dumps(pie_chart_data),
    }
    return render(request, 'dashboard.html', context)



@login_required
def validar_estoque_api(request):
    if request.method == 'POST':
        try:
            dados_sacola = json.loads(request.body)
            if not dados_sacola:
                return JsonResponse({'status': 'erro', 'message': 'Sua sacola está vazia.'}, status=400)

            for produto_id_str, item_sacola in dados_sacola.items():
                produto = Produto.objects.get(id=int(produto_id_str))
                quantidade_pedida = item_sacola.get('quantidade', 0)

                if produto.estoque < quantidade_pedida:
                    # Se um item não tiver estoque, retorna um erro imediatamente
                    mensagem = f"Desculpe, o produto '{produto.nome}' não tem estoque suficiente. Temos apenas {produto.estoque} unidade(s)."
                    return JsonResponse({'status': 'erro', 'message': mensagem}, status=400)

            # Se o loop terminar sem erros, o estoque está OK
            return JsonResponse({'status': 'ok'})

        except Produto.DoesNotExist:
            return JsonResponse({'status': 'erro', 'message': 'Um produto na sua sacola não foi encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'erro', 'message': str(e)}, status=500)


@staff_member_required
def save_webpush_subscription(request):
    if request.method == 'POST':
        try:
            # Pega os dados da subscrição enviados pelo JavaScript
            subscription_data = json.loads(request.body)
            # Evita duplicados
            WebPushSubscription.objects.get_or_create(
                user=request.user,
                subscription_info=subscription_data
            )
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'erro', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'erro'}, status=405)