from typing import Dict, Any, Optional
from .models import Product, Category, StockObserver, LowStockNotifier, OutOfStockNotifier
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


class ProductFactory:
    """Factory para criação de produtos usando o padrão Factory Method"""
    
    @staticmethod
    def create_product(
        name: str,
        description: Optional[str],
        price: float,
        stock: int = 0,
        min_stock: int = 0,
        category: Optional[Category] = None,
        product_type: str = "regular",
        **kwargs
    ) -> Product:
        """
        Cria um produto usando o padrão Factory Method
        
        Args:
            name: Nome do produto
            description: Descrição do produto
            price: Preço do produto
            stock: Quantidade em estoque
            min_stock: Estoque mínimo
            category: Categoria do produto
            product_type: Tipo do produto ('regular', 'perishable', 'digital')
            **kwargs: Argumentos adicionais
            
        Returns:
            Product: Produto criado
        """
        try:
            # Validações básicas
            if not name or price <= 0:
                raise ValueError("Dados inválidos para criação do produto")
            
            # Criar o produto base
            product_data = {
                'name': name,
                'description': description or '',
                'price': price,
                'stock': stock,
                'min_stock': min_stock,
                'category': category,
                **kwargs
            }
            
            # Aplicar lógica específica baseada no tipo
            if product_type == "perishable":
                product = ProductFactory._create_perishable_product(product_data)
            elif product_type == "digital":
                product = ProductFactory._create_digital_product(product_data)
            else:
                product = ProductFactory._create_regular_product(product_data)
            
            # Configurar observadores padrão
            ProductFactory._setup_default_observers(product)
            
            logger.info(f"Produto '{name}' criado com sucesso (tipo: {product_type})")
            return product
            
        except Exception as e:
            logger.error(f"Erro ao criar produto '{name}': {e}")
            raise
    
    @staticmethod
    def _create_regular_product(product_data: Dict[str, Any]) -> Product:
        """Cria um produto regular"""
        product = Product.objects.create(**product_data)
        return product
    
    @staticmethod
    def _create_perishable_product(product_data: Dict[str, Any]) -> Product:
        """Cria um produto perecível com configurações específicas"""
        # Para produtos perecíveis, definir estoque mínimo padrão se não especificado
        if product_data.get('min_stock', 0) == 0:
            product_data['min_stock'] = 5
        
        product = Product.objects.create(**product_data)
        return product
    
    @staticmethod
    def _create_digital_product(product_data: Dict[str, Any]) -> Product:
        """Cria um produto digital com configurações específicas"""
        # Produtos digitais não precisam de estoque físico
        product_data['stock'] = 999999
        product_data['min_stock'] = 0
        
        product = Product.objects.create(**product_data)
        return product
    
    @staticmethod
    def _setup_default_observers(product: Product) -> None:
        """Configura observadores padrão para o produto"""
        try:
            # Adicionar observadores padrão
            low_stock_observer = LowStockNotifier()
            out_of_stock_observer = OutOfStockNotifier()
            
            product.add_observer(low_stock_observer)
            product.add_observer(out_of_stock_observer)
            
            logger.debug(f"Observadores configurados para o produto '{product.name}'")
            
        except Exception as e:
            logger.error(f"Erro ao configurar observadores para '{product.name}': {e}")


class CategoryFactory:
    """Factory para criação de categorias"""
    
    @staticmethod
    def create_category(
        name: str,
        description: str = "",
        **kwargs
    ) -> Category:
        """
        Cria uma categoria
        
        Args:
            name: Nome da categoria
            description: Descrição da categoria
            **kwargs: Argumentos adicionais
            
        Returns:
            Category: Categoria criada
        """
        try:
            if not name:
                raise ValueError("Nome da categoria é obrigatório")
            
            category = Category.objects.create(
                name=name,
                description=description,
                **kwargs
            )
            
            logger.info(f"Categoria '{name}' criada com sucesso")
            return category
            
        except Exception as e:
            logger.error(f"Erro ao criar categoria '{name}': {e}")
            raise


class StockMovementFactory:
    """Factory para criação de movimentações de estoque"""
    
    @staticmethod
    def create_movement(
        product: Product,
        movement_type: str,
        quantity: int,
        reason: str = "",
        user: Optional[User] = None
    ) -> bool:
        """
        Cria uma movimentação de estoque
        
        Args:
            product: Produto a ser movimentado
            movement_type: Tipo de movimento ('IN', 'OUT', 'ADJUSTMENT')
            quantity: Quantidade a ser movimentada
            reason: Motivo da movimentação
            user: Usuário que realizou a operação
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        try:
            return product.update_stock(
                quantity=quantity,
                movement_type=movement_type,
                reason=reason,
                user=user
            )
            
        except Exception as e:
            logger.error(f"Erro ao criar movimentação para '{product.name}': {e}")
            return False 