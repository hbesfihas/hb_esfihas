from django.shortcuts import render, redirect
from .models import Categoria, Produto, User
from django.contrib.auth import login

def login_cliente(request):
    if request.method == 'POST':
        nome = request.Post.get('nome')
        whatsapp = request.Post.get('whatsapp')
        if whatsapp:
            user, _ = User.objects.get_or_create(whatsapp=whatsapp, defaults={'nome': nome})
            user.nome = nome
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
        
        
def home(request):
    categorias = Categoria.objects.all()
    produtos = Produto.objects.all()
    return render(request, 'home.html', {'categorias': categorias, 'produtos': produtos})

def finalizar_pedido(request):
    return render(request, 'finalizar_pedido.html')