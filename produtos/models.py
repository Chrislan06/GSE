from django.db import models
from django.core.exceptions import ValidationError
from django.contrib import messages
from typing import List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome')
    description = models.TextField(verbose_name='Descrição', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    def __str__(self):
        return self.name

    def clean(self):
        """Validação de regras de negócio para categoria"""
        if not self.name.strip():
            raise ValidationError('O nome da categoria não pode estar vazio.')
        
        # Verificar se já existe uma categoria com o mesmo nome
        if Category.objects.filter(name__iexact=self.name.strip()).exclude(pk=self.pk).exists():
            raise ValidationError('Já existe uma categoria com este nome.')

    def get_low_stock_count(self) -> int:
        """Retorna o número de produtos com estoque baixo nesta categoria"""
        return self.products.filter(stock__lte=models.F('min_stock')).exclude(stock=0).count()

    def get_out_of_stock_count(self) -> int:
        """Retorna o número de produtos sem estoque nesta categoria"""
        return self.products.filter(stock=0).count()

    def get_normal_stock_count(self) -> int:
        """Retorna o número de produtos com estoque normal nesta categoria"""
        return self.products.filter(stock__gt=models.F('min_stock')).count()

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']


class StockMovement(models.Model):
    """Modelo para rastrear movimentações de estoque"""
    MOVEMENT_TYPES = [
        ('IN', 'Entrada'),
        ('OUT', 'Saída'),
        ('ADJUSTMENT', 'Ajuste'),
    ]
    
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name='Produto', related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, verbose_name='Tipo de Movimento')
    quantity = models.IntegerField(verbose_name='Quantidade')
    previous_stock = models.IntegerField(verbose_name='Estoque Anterior')
    new_stock = models.IntegerField(verbose_name='Novo Estoque')
    reason = models.CharField(max_length=200, verbose_name='Motivo', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, verbose_name='Criado por')

    class Meta:
        verbose_name = 'Movimentação de Estoque'
        verbose_name_plural = 'Movimentações de Estoque'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()} ({self.quantity})"


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome')
    description = models.TextField(verbose_name='Descrição')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço')
    stock = models.IntegerField(verbose_name='Estoque', default=0)
    min_stock = models.IntegerField(verbose_name='Estoque Mínimo', default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Categoria', related_name='products', null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    # Lista de observadores para o padrão Observer
    _observers: List['StockObserver'] = []

    def __str__(self):
        return self.name

    def clean(self):
        """Validação de regras de negócio para produto"""
        if not self.name.strip():
            raise ValidationError('O nome do produto não pode estar vazio.')
        
        if self.price <= 0:
            raise ValidationError('O preço deve ser maior que zero.')
        
        if self.stock < 0:
            raise ValidationError('O estoque não pode ser negativo.')
        
        if self.min_stock < 0:
            raise ValidationError('O estoque mínimo não pode ser negativo.')
        
        # Verificar se já existe um produto com o mesmo nome na mesma categoria
        if Product.objects.filter(name__iexact=self.name.strip(), category=self.category).exclude(pk=self.pk).exists():
            raise ValidationError('Já existe um produto com este nome nesta categoria.')

    @property
    def low_stock(self) -> bool:
        """Verifica se o estoque está baixo"""
        return self.stock <= self.min_stock

    @property
    def stock_status(self) -> str:
        """Retorna o status do estoque"""
        if self.stock == 0:
            return 'Sem estoque'
        elif self.low_stock:
            return 'Estoque baixo'
        else:
            return 'Estoque normal'

    def add_observer(self, observer: 'StockObserver') -> None:
        """Adiciona um observador para notificações de estoque"""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: 'StockObserver') -> None:
        """Remove um observador"""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self) -> None:
        """Notifica todos os observadores sobre mudanças no estoque"""
        for observer in self._observers:
            try:
                observer.update(self)
            except Exception as e:
                logger.error(f"Erro ao notificar observador {observer}: {e}")

    def update_stock(self, quantity: int, movement_type: str, reason: str = "", user=None) -> bool:
        """
        Atualiza o estoque e registra a movimentação
        
        Args:
            quantity: Quantidade a ser movimentada (positiva para entrada, negativa para saída)
            movement_type: Tipo de movimento ('IN', 'OUT', 'ADJUSTMENT')
            reason: Motivo da movimentação
            user: Usuário que realizou a operação
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            previous_stock = self.stock
            
            if movement_type == 'IN':
                self.stock += quantity
            elif movement_type == 'OUT':
                if self.stock - quantity < 0:
                    raise ValidationError('Estoque insuficiente para esta operação.')
                self.stock -= quantity
            elif movement_type == 'ADJUSTMENT':
                self.stock = quantity
            else:
                raise ValidationError('Tipo de movimento inválido.')
            
            # Salvar o produto
            self.save()
            
            # Registrar a movimentação
            StockMovement.objects.create(
                product=self,
                movement_type=movement_type,
                quantity=abs(quantity),
                previous_stock=previous_stock,
                new_stock=self.stock,
                reason=reason,
                created_by=user
            )
            
            # Notificar observadores
            self.notify_observers()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar estoque do produto {self.name}: {e}")
            return False

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['name']


class StockObserver:
    """Classe base para observadores de estoque"""
    
    def update(self, product: Product) -> None:
        """
        Método chamado quando há mudanças no estoque de um produto
        
        Args:
            product: Produto que teve mudança no estoque
        """
        raise NotImplementedError("Subclasses devem implementar este método")


class LowStockNotifier(StockObserver):
    """Observador para notificar sobre estoque baixo"""
    
    def update(self, product: Product) -> None:
        """
        Notifica quando o estoque está baixo
        
        Args:
            product: Produto com estoque baixo
        """
        if product.low_stock:
            logger.warning(f"Estoque baixo detectado: {product.name} (Estoque: {product.stock}, Mínimo: {product.min_stock})")
            # Aqui você pode implementar notificações por email, SMS, etc.
            self._send_notification(product)
    
    def _send_notification(self, product: Product) -> None:
        """
        Envia notificação sobre estoque baixo
        
        Args:
            product: Produto com estoque baixo
        """
        # Implementar lógica de notificação (email, SMS, etc.)
        message = f"ALERTA: Estoque baixo para o produto '{product.name}'. Estoque atual: {product.stock}, Estoque mínimo: {product.min_stock}"
        logger.info(f"Notificação enviada: {message}")


class OutOfStockNotifier(StockObserver):
    """Observador para notificar sobre produtos sem estoque"""
    
    def update(self, product: Product) -> None:
        """
        Notifica quando o produto fica sem estoque
        
        Args:
            product: Produto sem estoque
        """
        if product.stock == 0:
            logger.error(f"Produto sem estoque: {product.name}")
            self._send_notification(product)
    
    def _send_notification(self, product: Product) -> None:
        """
        Envia notificação sobre produto sem estoque
        
        Args:
            product: Produto sem estoque
        """
        message = f"URGENTE: Produto '{product.name}' está sem estoque!"
        logger.info(f"Notificação de estoque zero enviada: {message}")