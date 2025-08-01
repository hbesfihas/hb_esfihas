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
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    data = models.DateTimeField(auto_now_add=True)
    pago = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pendente', 'Pendente'),
            ('preparando', 'Preparando'),
            ('pronto', 'Pronto'),
            ('entregue', 'Entregue'),
            ('cancelado', 'Cancelado'),
        ],
        default='pendente'
    )

    def total(self):
        return sum(item.subtotal() for item in self.itens.all())

    def __str__(self):
        return f"Pedido #{self.id} de {self.cliente.nome} - {self.data.strftime('%d/%m %H:%M')}"

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=6, decimal_places=2)

    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"
   