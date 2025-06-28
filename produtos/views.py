from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from typing import Dict, Any
import logging

from .models import Product, Category, StockMovement
from .forms import ProductForm, CategoryForm, StockMovementForm
from .services import ProductService, CategoryService, StockService, ReportService

logger = logging.getLogger(__name__)


# ============================================================================
# VIEWS DE PRODUTOS
# ============================================================================

@login_required
def product_list(request) -> Any:
    """
    Lista todos os produtos
    
    Args:
        request: Requisição HTTP
        
    Returns:
        HttpResponse: Template com lista de produtos
    """
    try:
        # Buscar produtos com filtros
        search = request.GET.get('search', '')
        category_id = request.GET.get('category', '')
        stock_status = request.GET.get('stock_status', '')
        
        products = ProductService.get_all_products()
        
        # Aplicar filtros
        if search:
            products = products.filter(name__icontains=search)
        
        if category_id:
            products = products.filter(category_id=category_id)
        
        if stock_status:
            if stock_status == 'low':
                products = [p for p in products if p.low_stock and p.stock > 0]
            elif stock_status == 'out':
                products = [p for p in products if p.stock == 0]
            elif stock_status == 'normal':
                products = [p for p in products if not p.low_stock and p.stock > 0]
        
        # Buscar categorias para o filtro
        categories = Category.objects.all()
        
        # Calcular estatísticas
        low_stock_count = len([p for p in Product.objects.all() if p.low_stock and p.stock > 0])
        out_of_stock_count = len([p for p in Product.objects.all() if p.stock == 0])
        
        context = {
            'products': products,
            'categories': categories,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count
        }
        
        return render(request, 'produtos/product_list.html', context)
        
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {e}")
        messages.error(request, "Erro ao carregar lista de produtos.")
        return render(request, 'produtos/product_list.html', {
            'products': [],
            'categories': [],
            'low_stock_count': 0,
            'out_of_stock_count': 0
        })


@login_required
def product_create(request) -> Any:
    """
    Cria um novo produto
    
    Args:
        request: Requisição HTTP
        
    Returns:
        HttpResponse: Template de criação ou redirecionamento
    """
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            try:
                # Usar o serviço para criar o produto
                product = ProductService.create_product(
                    name=form.cleaned_data['name'],
                    description=form.cleaned_data['description'],
                    price=form.cleaned_data['price'],
                    stock=form.cleaned_data['stock'],
                    min_stock=form.cleaned_data.get('min_stock', 0),
                    category=form.cleaned_data.get('category'),
                    user=request.user
                )
                
                if product:
                    messages.success(request, f"Produto '{product.name}' criado com sucesso!")
                    return redirect('produtos:lista_produtos')
                else:
                    messages.error(request, "Erro ao criar produto.")
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Erro ao criar produto: {e}")
                messages.error(request, "Erro interno ao criar produto.")
    else:
        form = ProductForm()
    
    return render(request, 'produtos/product_form.html', {'form': form})


@login_required
def product_update(request, pk: int) -> Any:
    """
    Atualiza um produto existente
    
    Args:
        request: Requisição HTTP
        pk: ID do produto
        
    Returns:
        HttpResponse: Template de edição ou redirecionamento
    """
    product = ProductService.get_product_by_id(pk)
    if not product:
        messages.error(request, "Produto não encontrado.")
        return redirect('produtos:lista_produtos')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            try:
                success = ProductService.update_product(
                    product_id=pk,
                    name=form.cleaned_data['name'],
                    description=form.cleaned_data.get('description', ''),
                    price=form.cleaned_data['price'],
                    min_stock=form.cleaned_data['min_stock'],
                    category_id=form.cleaned_data.get('category')
                )
                
                if success:
                    messages.success(request, f"Produto '{product.name}' atualizado com sucesso!")
                    return redirect('produtos:lista_produtos')
                else:
                    messages.error(request, "Erro ao atualizar produto.")
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Erro ao atualizar produto {pk}: {e}")
                messages.error(request, "Erro interno ao atualizar produto.")
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'produtos/product_form.html', {'form': form, 'product': product})


@login_required
def product_delete(request, pk: int) -> Any:
    """
    Remove um produto
    
    Args:
        request: Requisição HTTP
        pk: ID do produto
        
    Returns:
        HttpResponse: Template de confirmação ou redirecionamento
    """
    product = ProductService.get_product_by_id(pk)
    if not product:
        messages.error(request, "Produto não encontrado.")
        return redirect('produtos:lista_produtos')
    
    if request.method == 'POST':
        try:
            success = ProductService.delete_product(pk)
            if success:
                messages.success(request, f"Produto '{product.name}' removido com sucesso!")
                return redirect('produtos:lista_produtos')
            else:
                messages.error(request, "Erro ao remover produto.")
                
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Erro ao remover produto {pk}: {e}")
            messages.error(request, "Erro interno ao remover produto.")
    
    return render(request, 'produtos/product_confirm_delete.html', {'product': product})


@login_required
def product_detail(request, pk: int) -> Any:
    """
    Exibe detalhes de um produto
    
    Args:
        request: Requisição HTTP
        pk: ID do produto
        
    Returns:
        HttpResponse: Template com detalhes do produto
    """
    product = ProductService.get_product_by_id(pk)
    if not product:
        messages.error(request, "Produto não encontrado.")
        return redirect('produtos:lista_produtos')
    
    # Buscar movimentações de estoque
    stock_movements = StockService.get_stock_movements(pk)
    
    context = {
        'product': product,
        'stock_movements': stock_movements
    }
    
    return render(request, 'produtos/product_detail.html', context)


# ============================================================================
# VIEWS DE CATEGORIAS
# ============================================================================

@login_required
def category_list(request) -> Any:
    """
    Lista todas as categorias
    
    Args:
        request: Requisição HTTP
        
    Returns:
        HttpResponse: Template com lista de categorias
    """
    try:
        # Buscar categorias com filtros
        search = request.GET.get('search', '')
        categories = CategoryService.get_all_categories()
        
        # Aplicar filtro de busca
        if search:
            categories = categories.filter(name__icontains=search)
        
        # Calcular estatísticas
        total_products = Product.objects.count()
        total_low_stock = len([p for p in Product.objects.all() if p.low_stock and p.stock > 0])
        total_out_of_stock = len([p for p in Product.objects.all() if p.stock == 0])
        
        context = {
            'categories': categories,
            'total_products': total_products,
            'total_low_stock': total_low_stock,
            'total_out_of_stock': total_out_of_stock
        }
        
        return render(request, 'produtos/category_list.html', context)
        
    except Exception as e:
        logger.error(f"Erro ao listar categorias: {e}")
        messages.error(request, "Erro ao carregar lista de categorias.")
        return render(request, 'produtos/category_list.html', {
            'categories': [],
            'total_products': 0,
            'total_low_stock': 0,
            'total_out_of_stock': 0
        })


@login_required
def category_create(request) -> Any:
    """
    Cria uma nova categoria
    
    Args:
        request: Requisição HTTP
        
    Returns:
        HttpResponse: Template de criação ou redirecionamento
    """
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            try:
                category = CategoryService.create_category(
                    name=form.cleaned_data['name'],
                    description=form.cleaned_data.get('description', ''),
                    user=request.user
                )
                
                if category:
                    messages.success(request, f"Categoria '{category.name}' criada com sucesso!")
                    return redirect('produtos:lista_categorias')
                else:
                    messages.error(request, "Erro ao criar categoria.")
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Erro ao criar categoria: {e}")
                messages.error(request, "Erro interno ao criar categoria.")
    else:
        form = CategoryForm()
    
    return render(request, 'produtos/category_form.html', {'form': form})


@login_required
def category_update(request, pk: int) -> Any:
    """
    Atualiza uma categoria existente
    
    Args:
        request: Requisição HTTP
        pk: ID da categoria
        
    Returns:
        HttpResponse: Template de edição ou redirecionamento
    """
    category = CategoryService.get_category_by_id(pk)
    if not category:
        messages.error(request, "Categoria não encontrada.")
        return redirect('produtos:lista_categorias')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            try:
                success = CategoryService.update_category(
                    category_id=pk,
                    name=form.cleaned_data['name'],
                    description=form.cleaned_data.get('description', '')
                )
                
                if success:
                    messages.success(request, f"Categoria '{category.name}' atualizada com sucesso!")
                    return redirect('produtos:lista_categorias')
                else:
                    messages.error(request, "Erro ao atualizar categoria.")
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Erro ao atualizar categoria {pk}: {e}")
                messages.error(request, "Erro interno ao atualizar categoria.")
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'produtos/category_form.html', {'form': form, 'category': category})


@login_required
def category_delete(request, pk: int) -> Any:
    """
    Remove uma categoria
    
    Args:
        request: Requisição HTTP
        pk: ID da categoria
        
    Returns:
        HttpResponse: Template de confirmação ou redirecionamento
    """
    category = CategoryService.get_category_by_id(pk)
    if not category:
        messages.error(request, "Categoria não encontrada.")
        return redirect('produtos:lista_categorias')
    
    if request.method == 'POST':
        try:
            success = CategoryService.delete_category(pk)
            if success:
                messages.success(request, f"Categoria '{category.name}' removida com sucesso!")
                return redirect('produtos:lista_categorias')
            else:
                messages.error(request, "Erro ao remover categoria.")
                
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Erro ao remover categoria {pk}: {e}")
            messages.error(request, "Erro interno ao remover categoria.")
    
    return render(request, 'produtos/category_confirm_delete.html', {'category': category})


@login_required
def category_detail(request, pk: int) -> Any:
    """
    Exibe detalhes de uma categoria
    
    Args:
        request: Requisição HTTP
        pk: ID da categoria
        
    Returns:
        HttpResponse: Template com detalhes da categoria
    """
    category = CategoryService.get_category_by_id(pk)
    if not category:
        messages.error(request, "Categoria não encontrada.")
        return redirect('produtos:lista_categorias')
    
    # Buscar produtos da categoria
    products = category.products.all()
    low_stock_products = [p for p in products if p.low_stock and p.stock > 0]
    out_of_stock_products = [p for p in products if p.stock == 0]
    normal_stock_products = [p for p in products if not p.low_stock and p.stock > 0]
    
    context = {
        'category': category,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'normal_stock_products': normal_stock_products,
        'low_stock_count': len(low_stock_products),
        'out_of_stock_count': len(out_of_stock_products),
        'normal_stock_count': len(normal_stock_products)
    }
    
    return render(request, 'produtos/category_detail.html', context)


# ============================================================================
# VIEWS DE ESTOQUE
# ============================================================================

@login_required
def stock_movement(request, pk: int) -> Any:
    """
    Gerencia movimentações de estoque de um produto
    
    Args:
        request: Requisição HTTP
        pk: ID do produto
        
    Returns:
        HttpResponse: Template de movimentação ou redirecionamento
    """
    product = ProductService.get_product_by_id(pk)
    if not product:
        messages.error(request, "Produto não encontrado.")
        return redirect('produtos:lista_produtos')
    
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            try:
                movement_type = form.cleaned_data['movement_type']
                quantity = form.cleaned_data['quantity']
                reason = form.cleaned_data.get('reason', '')
                
                if movement_type == 'IN':
                    success = StockService.add_stock(pk, quantity, reason, request.user)
                elif movement_type == 'OUT':
                    success = StockService.remove_stock(pk, quantity, reason, request.user)
                else:  # ADJUSTMENT
                    success = StockService.adjust_stock(pk, quantity, reason, request.user)
                
                if success:
                    messages.success(request, f"Movimentação de estoque realizada com sucesso!")
                    return redirect('produtos:detalhe_produto', pk=pk)
                else:
                    messages.error(request, "Erro ao realizar movimentação de estoque.")
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Erro ao realizar movimentação de estoque: {e}")
                messages.error(request, "Erro interno ao realizar movimentação.")
    else:
        form = StockMovementForm()
    
    # Buscar movimentações recentes
    recent_movements = StockService.get_stock_movements(pk)[:5]
    
    context = {
        'product': product,
        'form': form,
        'recent_movements': recent_movements
    }
    
    return render(request, 'produtos/stock_movement.html', context)


# ============================================================================
# VIEWS DE RELATÓRIOS
# ============================================================================

@login_required
def reports(request) -> Any:
    """
    Exibe relatórios do sistema
    
    Args:
        request: Requisição HTTP
        
    Returns:
        HttpResponse: Template com relatórios
    """
    try:
        dashboard_data = ReportService.get_dashboard_data()
        stock_report = ReportService.get_stock_report()
        
        # Buscar produtos para alertas
        low_stock_products = ProductService.get_low_stock_products()
        out_of_stock_products = [p for p in Product.objects.all() if p.stock == 0]
        
        context = {
            **dashboard_data,
            'stock_report': stock_report,
            'low_stock_products': low_stock_products,
            'out_of_stock_products': out_of_stock_products
        }
        
        return render(request, 'produtos/reports.html', context)
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatórios: {e}")
        messages.error(request, "Erro ao carregar relatórios.")
        return render(request, 'produtos/reports.html', {
            'total_products': 0,
            'total_categories': 0,
            'low_stock_count': 0,
            'out_of_stock_count': 0,
            'stock_report': {
                'normal_stock': [],
                'low_stock': [],
                'out_of_stock': []
            },
            'low_stock_products': [],
            'out_of_stock_products': []
        })


@login_required
def low_stock_alert(request) -> Any:
    """
    Exibe alertas de estoque baixo
    
    Args:
        request: Requisição HTTP
        
    Returns:
        HttpResponse: Template com alertas
    """
    try:
        low_stock_products = ProductService.get_low_stock_products()
        out_of_stock_products = [p for p in Product.objects.all() if p.stock == 0]
        
        context = {
            'low_stock_products': low_stock_products,
            'out_of_stock_products': out_of_stock_products
        }
        
        return render(request, 'produtos/low_stock_alert.html', context)
        
    except Exception as e:
        logger.error(f"Erro ao carregar alertas de estoque: {e}")
        messages.error(request, "Erro ao carregar alertas de estoque.")
        return render(request, 'produtos/low_stock_alert.html', {})


# ============================================================================
# VIEWS AJAX
# ============================================================================

@login_required
def get_product_data(request, pk: int) -> JsonResponse:
    """
    Retorna dados de um produto em formato JSON
    
    Args:
        request: Requisição HTTP
        pk: ID do produto
        
    Returns:
        JsonResponse: Dados do produto
    """
    try:
        product = ProductService.get_product_by_id(pk)
        if not product:
            return JsonResponse({'error': 'Produto não encontrado'}, status=404)
        
        data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': str(product.price),
            'stock': product.stock,
            'min_stock': product.min_stock,
            'stock_status': product.stock_status,
            'category': product.category.name if product.category else None,
            'created_at': product.created_at.isoformat(),
            'updated_at': product.updated_at.isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados do produto {pk}: {e}")
        return JsonResponse({'error': 'Erro interno'}, status=500)


