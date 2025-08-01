from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, whatsapp, nome, password=None):
        if not whatsapp:
            raise ValueError("O campo WhatsApp é obrigatório")
        if not nome:
            raise ValueError("O campo Nome é obrigatório")

        user = self.model(nome=nome, whatsapp=whatsapp)
        user.save(using=self._db)
        return user

    def create_superuser(self, whatsapp, nome, password):
        user = self.create_user(whatsapp, nome, password)
        user.is_admin = True
        user.set_password(password)
        user.save(using=self._db)
        return user

class Cliente(AbstractBaseUser):
    whatsapp = models.CharField(max_length=15, unique=True)
    nome = models.CharField(max_length=100)
    username = None
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    pontos = models.IntegerField(default=0)
    ultimo_endereco = models.TextField(null=True, blank=True)

    USERNAME_FIELD = 'whatsapp'  # Campo usado para login
    REQUIRED_FIELDS = ['nome']   # Campos obrigatórios ao criar o usuário

    objects = CustomUserManager()

    def __str__(self):
        return self.nome

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    icone = models.ImageField(upload_to='icones/', blank=True, null=True)
    ordem = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.nome

class Produto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    disponivel = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class Bairro(models.Model):
    nome = models.CharField(max_length=100)
    valor_frete = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_preparo', 'Em preparo'),
        ('pronto', 'Pronto para retirada'),
        ('a_caminho', 'A caminho'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    pago = models.BooleanField(default=False)
    bairro = models.ForeignKey(Bairro, null=True, blank=True, on_delete=models.SET_NULL)
    endereco= models.TextField(blank=True, null=True)
    tipo_entrega = models.CharField(
        max_length=20,
        choices=[
            ('entrega', 'Entrega'),
            ('retirada', 'Retirada'),
            ('local', 'Consumir no Local'),
        ]
    )
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='pendente')
    endereco_entrega = models.TextField(blank=True, null=True)
    forma_pagamento = models.CharField(max_length=20, default='dinheiro_pix')
    troco = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    def __str__(self):
        return f"Pedido #{self.id} de {self.cliente.nome} - {self.criado_em.strftime('%d/%m %H:%M')}"
    
class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"
   