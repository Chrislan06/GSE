from typing import List, Optional, Dict, Any
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib import messages
import logging

from .models import Product, Category, StockMovement
from .factories import ProductFactory, CategoryFactory, StockMovementFactory

logger = logging.getLogger(__name__)


class ProductService:
    """Serviço para operações relacionadas a produtos"""
    
    @staticmethod
    def get_all_products() -> List[Product]:
        """
        Retorna todos os produtos
        
        Returns:
            List[Product]: Lista de todos os produtos
        """
        try:
            return Product.objects.all().select_related('category')
        except Exception as e:
            logger.error(f"Erro ao buscar produtos: {e}")
            return []
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        """
        Busca um produto por ID
        
        Args:
            product_id: ID do produto
            
        Returns:
            Optional[Product]: Produto encontrado ou None
        """
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            logger.warning(f"Produto com ID {product_id} não encontrado")
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar produto {product_id}: {e}")
            return None
    
    @staticmethod
    def create_product(
        name: str,
        description: str,
        price: float,
        stock: int = 0,
        min_stock: int = 0,
        category: Optional[Category] = None,
        product_type: str = "regular",
        user: Optional[User] = None
    ) -> Optional[Product]:
        """
        Cria um novo produto
        
        Args:
            name: Nome do produto
            description: Descrição do produto
            price: Preço do produto
            stock: Quantidade em estoque
            min_stock: Estoque mínimo
            category: Categoria do produto
            product_type: Tipo do produto
            user: Usuário que está criando
            
        Returns:
            Optional[Product]: Produto criado ou None em caso de erro
        """
        try:
            with transaction.atomic():
                product = ProductFactory.create_product(
                    name=name,
                    description=description,
                    price=price,
                    stock=stock,
                    min_stock=min_stock,
                    category=category,
                    product_type=product_type
                )
                
                logger.info(f"Produto '{name}' criado com sucesso por {user}")
                return product
                
        except Exception as e:
            logger.error(f"Erro ao criar produto '{name}': {e}")
            return None
    
    @staticmethod
    def update_product(
        product_id: int,
        **kwargs
    ) -> bool:
        """
        Atualiza um produto
        
        Args:
            product_id: ID do produto
            **kwargs: Campos a serem atualizados
            
        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            with transaction.atomic():
                product = ProductService.get_product_by_id(product_id)
                if not product:
                    return False
                
                for field, value in kwargs.items():
                    if hasattr(product, field):
                        setattr(product, field, value)
                
                product.full_clean()
                product.save()
                
                logger.info(f"Produto '{product.name}' atualizado com sucesso")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao atualizar produto {product_id}: {e}")
            return False
    
    @staticmethod
    def delete_product(product_id: int) -> bool:
        """
        Remove um produto
        
        Args:
            product_id: ID do produto
            
        Returns:
            bool: True se removido com sucesso
        """
        try:
            with transaction.atomic():
                product = ProductService.get_product_by_id(product_id)
                if not product:
                    return False
                
                product_name = product.name
                product.delete()
                
                logger.info(f"Produto '{product_name}' removido com sucesso")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao remover produto {product_id}: {e}")
            return False
    
    @staticmethod
    def get_products_by_category(category_id: int) -> List[Product]:
        """
        Busca produtos por categoria
        
        Args:
            category_id: ID da categoria
            
        Returns:
            List[Product]: Lista de produtos da categoria
        """
        try:
            return Product.objects.filter(category_id=category_id)
        except Exception as e:
            logger.error(f"Erro ao buscar produtos da categoria {category_id}: {e}")
            return []
    
    @staticmethod
    def get_low_stock_products() -> List[Product]:
        """
        Retorna produtos com estoque baixo
        
        Returns:
            List[Product]: Lista de produtos com estoque baixo
        """
        try:
            return [product for product in Product.objects.all() if product.low_stock]
        except Exception as e:
            logger.error(f"Erro ao buscar produtos com estoque baixo: {e}")
            return []


class CategoryService:
    """Serviço para operações relacionadas a categorias"""
    
    @staticmethod
    def get_all_categories() -> List[Category]:
        """
        Retorna todas as categorias
        
        Returns:
            List[Category]: Lista de todas as categorias
        """
        try:
            return Category.objects.all()
        except Exception as e:
            logger.error(f"Erro ao buscar categorias: {e}")
            return []
    
    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[Category]:
        """
        Busca uma categoria por ID
        
        Args:
            category_id: ID da categoria
            
        Returns:
            Optional[Category]: Categoria encontrada ou None
        """
        try:
            return Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            logger.warning(f"Categoria com ID {category_id} não encontrada")
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar categoria {category_id}: {e}")
            return None
    
    @staticmethod
    def create_category(
        name: str,
        description: str = "",
        user: Optional[User] = None
    ) -> Optional[Category]:
        """
        Cria uma nova categoria
        
        Args:
            name: Nome da categoria
            description: Descrição da categoria
            user: Usuário que está criando
            
        Returns:
            Optional[Category]: Categoria criada ou None em caso de erro
        """
        try:
            with transaction.atomic():
                category = CategoryFactory.create_category(
                    name=name,
                    description=description
                )
                
                logger.info(f"Categoria '{name}' criada com sucesso por {user}")
                return category
                
        except Exception as e:
            logger.error(f"Erro ao criar categoria '{name}': {e}")
            return None
    
    @staticmethod
    def update_category(
        category_id: int,
        **kwargs
    ) -> bool:
        """
        Atualiza uma categoria
        
        Args:
            category_id: ID da categoria
            **kwargs: Campos a serem atualizados
            
        Returns:
            bool: True se atualizada com sucesso
        """
        try:
            with transaction.atomic():
                category = CategoryService.get_category_by_id(category_id)
                if not category:
                    return False
                
                for field, value in kwargs.items():
                    if hasattr(category, field):
                        setattr(category, field, value)
                
                category.full_clean()
                category.save()
                
                logger.info(f"Categoria '{category.name}' atualizada com sucesso")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao atualizar categoria {category_id}: {e}")
            return False
    
    @staticmethod
    def delete_category(category_id: int) -> bool:
        """
        Remove uma categoria
        
        Args:
            category_id: ID da categoria
            
        Returns:
            bool: True se removida com sucesso
        """
        try:
            with transaction.atomic():
                category = CategoryService.get_category_by_id(category_id)
                if not category:
                    return False
                
                # Verificar se há produtos associados
                if category.products.exists():
                    raise ValidationError("Não é possível remover uma categoria que possui produtos associados")
                
                category_name = category.name
                category.delete()
                
                logger.info(f"Categoria '{category_name}' removida com sucesso")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao remover categoria {category_id}: {e}")
            return False


class StockService:
    """Serviço para operações relacionadas ao estoque"""
    
    @staticmethod
    def add_stock(
        product_id: int,
        quantity: int,
        reason: str = "",
        user: Optional[User] = None
    ) -> bool:
        """
        Adiciona estoque a um produto
        
        Args:
            product_id: ID do produto
            quantity: Quantidade a ser adicionada
            reason: Motivo da adição
            user: Usuário que realizou a operação
            
        Returns:
            bool: True se operação foi bem-sucedida
        """
        try:
            product = ProductService.get_product_by_id(product_id)
            if not product:
                return False
            
            success = StockMovementFactory.create_movement(
                product=product,
                movement_type='IN',
                quantity=quantity,
                reason=reason,
                user=user
            )
            
            if success:
                logger.info(f"Estoque adicionado ao produto '{product.name}': +{quantity}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao adicionar estoque ao produto {product_id}: {e}")
            return False
    
    @staticmethod
    def remove_stock(
        product_id: int,
        quantity: int,
        reason: str = "",
        user: Optional[User] = None
    ) -> bool:
        """
        Remove estoque de um produto
        
        Args:
            product_id: ID do produto
            quantity: Quantidade a ser removida
            reason: Motivo da remoção
            user: Usuário que realizou a operação
            
        Returns:
            bool: True se operação foi bem-sucedida
        """
        try:
            product = ProductService.get_product_by_id(product_id)
            if not product:
                return False
            
            success = StockMovementFactory.create_movement(
                product=product,
                movement_type='OUT',
                quantity=quantity,
                reason=reason,
                user=user
            )
            
            if success:
                logger.info(f"Estoque removido do produto '{product.name}': -{quantity}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao remover estoque do produto {product_id}: {e}")
            return False
    
    @staticmethod
    def adjust_stock(
        product_id: int,
        new_quantity: int,
        reason: str = "",
        user: Optional[User] = None
    ) -> bool:
        """
        Ajusta o estoque de um produto para uma quantidade específica
        
        Args:
            product_id: ID do produto
            new_quantity: Nova quantidade de estoque
            reason: Motivo do ajuste
            user: Usuário que realizou a operação
            
        Returns:
            bool: True se operação foi bem-sucedida
        """
        try:
            product = ProductService.get_product_by_id(product_id)
            if not product:
                return False
            
            success = StockMovementFactory.create_movement(
                product=product,
                movement_type='ADJUSTMENT',
                quantity=new_quantity,
                reason=reason,
                user=user
            )
            
            if success:
                logger.info(f"Estoque ajustado para o produto '{product.name}': {new_quantity}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao ajustar estoque do produto {product_id}: {e}")
            return False
    
    @staticmethod
    def get_stock_movements(product_id: int) -> List[StockMovement]:
        """
        Retorna as movimentações de estoque de um produto
        
        Args:
            product_id: ID do produto
            
        Returns:
            List[StockMovement]: Lista de movimentações
        """
        try:
            return StockMovement.objects.filter(product_id=product_id).select_related('created_by')
        except Exception as e:
            logger.error(f"Erro ao buscar movimentações do produto {product_id}: {e}")
            return []


class ReportService:
    """Serviço para geração de relatórios"""
    
    @staticmethod
    def get_dashboard_data() -> Dict[str, Any]:
        """
        Retorna dados para o dashboard
        
        Returns:
            Dict[str, Any]: Dados do dashboard
        """
        try:
            total_products = Product.objects.count()
            total_categories = Category.objects.count()
            low_stock_products = ProductService.get_low_stock_products()
            out_of_stock_products = [p for p in Product.objects.all() if p.stock == 0]
            
            return {
                'total_products': total_products,
                'total_categories': total_categories,
                'low_stock_count': len(low_stock_products),
                'out_of_stock_count': len(out_of_stock_products),
                'low_stock_products': low_stock_products,
                'out_of_stock_products': out_of_stock_products
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar dados do dashboard: {e}")
            return {}
    
    @staticmethod
    def get_stock_report() -> Dict[str, Any]:
        """
        Retorna relatório de estoque
        
        Returns:
            Dict[str, Any]: Relatório de estoque
        """
        try:
            products = Product.objects.all().select_related('category')
            
            stock_data = {
                'normal_stock': [],
                'low_stock': [],
                'out_of_stock': []
            }
            
            for product in products:
                if product.stock == 0:
                    stock_data['out_of_stock'].append(product)
                elif product.low_stock:
                    stock_data['low_stock'].append(product)
                else:
                    stock_data['normal_stock'].append(product)
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de estoque: {e}")
            return {}
