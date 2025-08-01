from django.shortcuts import render, redirect
from .models import Categoria, Produto, Cliente,Pedido, ItemPedido
from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
import json
from django.contrib.auth.decorators import login_required

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
    categorias = Categoria.objects.all()
    produtos = Produto.objects.all()
    return render(request, 'home.html', {'categorias': categorias, 'produtos': produtos, 'cliente': cliente,})




def add_carrinho(request, produto_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        
        produto = get_object_or_404(Produto, id=produto_id)
        sacola = request.session.get('carrinho', {})
        produto_id_str = str(produto_id)

        if action == 'add':
            if produto_id_str in sacola:
                sacola[produto_id_str]['quantidade'] += 1
            else:
                sacola[produto_id_str] = {
                    'quantidade': 1,
                    'preco': str(produto.preco),
                    'nome': produto.nome
                }
        elif action == 'remove':
            if produto_id_str in sacola:
                sacola[produto_id_str]['quantidade'] -= 1
                if sacola[produto_id_str]['quantidade'] <= 0:
                    del sacola[produto_id_str]

        request.session['carrinho'] = sacola
        return JsonResponse({'status': 'ok', 'carrinho': sacola})
    
    return JsonResponse({'status': 'falha'}, status=400)

@login_required
def finalizar_pedido(request):
    carrinho = request.session.get('carrinho', {})

    if not carrinho:
        return redirect('home')

    pedido = Pedido.objects.create(cliente=request.user)

    for produto_id, item in carrinho.items():
        produto = Produto.objects.get(id=produto_id)
        ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=item['quantidade'],
            preco_unitario=produto.preco
        )

    # limpa a sacola
    request.session['carrinho'] = {}
    
    return render(request, 'pedido_finalizado.html', {'pedido': pedido})