from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
class Bairro(models.Model):
    nome = models.CharField(max_length=100)
    valor_frete = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.nome

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
    ultimo_bairro = models.ForeignKey(Bairro, on_delete=models.SET_NULL, null=True, blank=True)

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

    cor = models.CharField(max_length=7, default='#FFFFFF', help_text='Cor em formato hexadecimal, ex: #FF5733')
    icone_bootstrap = models.CharField(max_length=50, blank=True, null=True, help_text='Nome do ícone Bootstrap, ex: bi bi-pizza')
    def __str__(self):
        return self.nome

class Insumo(models.Model):
    UNIDADE_CHOICES = [
        ('g', 'Gramas'),
        ('kg', 'Quilogramas'),
        ('un', 'Unidades'),
        ('ml', 'Mililitros'),
        ('l', 'Litros'),
    ]
    nome = models.CharField(max_length=100, unique=True)
    unidade_medida = models.CharField(max_length=2, choices=UNIDADE_CHOICES)
    estoque_atual = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)
    custo_unidade = models.DecimalField(max_digits=10, decimal_places=4, help_text="Custo por grama, unidade, ml, etc.")

    def __str__(self):
        return f"{self.nome} ({self.get_unidade_medida_display()})"

class ItemReceita(models.Model):
    produto = models.ForeignKey('Produto', on_delete=models.CASCADE, related_name='receita')
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f"{self.quantidade} {self.insumo.get_unidade_medida_display()} de {self.insumo.nome} para {self.produto.nome}"


class Produto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    disponivel = models.BooleanField(default=True)
    estoque = models.PositiveIntegerField(default=0)  # Quantidade em estoque
    insumos = models.ManyToManyField(Insumo, through=ItemReceita)
    ordem = models.PositiveIntegerField(default=0, help_text="Use 0, 1, 2... para definir a ordem de exibição")

    # Nova função para calcular o custo do produto
    def custo_de_producao(self):
        custo_total = Decimal(0)
        for item in self.receita.all():
            custo_total += item.insumo.custo_unidade * item.quantidade
        return custo_total.quantize(Decimal("0.01"))

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
    forma_pagamento = models.CharField(max_length=20, default='dinheiro')
    troco_para = models.DecimalField(max_digits=8, decimal_places=0, null=True, blank=True)
    def __str__(self):
        return f"Pedido #{self.id} de {self.cliente.nome} - {self.criado_em.strftime('%d/%m %H:%M')}"

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"


class ConfiguracaoLoja(models.Model):
    loja_aberta = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super(ConfiguracaoLoja, self).save(*args, **kwargs)
    def __str__(self):
        return "Configuração da Loja"



class WebPushSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="webpush_subscriptions")
    subscription_info = models.JSONField()

    def __str__(self):
        return self.user.nome
