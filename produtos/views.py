from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Category
from .forms import ProductForm, CategoryForm


# Produtos
@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'produtos/product_list.html', {'products': products})

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_produtos')
    else:
        form = ProductForm()
    return render(request, 'produtos/product_form.html', {'form': form})

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('lista_produtos')
    else:
        form = ProductForm(instance=product)
    return render(request, 'produtos/product_form.html', {'form': form})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('lista_produtos')
    return render(request, 'produtos/product_confirm_delete.html', {'product': product})

# Categorias
@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'produtos/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_categorias')
    else:
        form = CategoryForm()
    return render(request, 'produtos/category_form.html', {'form': form})

@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('lista_categorias')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'produtos/category_form.html', {'form': form})

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('lista_categorias')
    return render(request, 'produtos/category_confirm_delete.html', {'category': category})


# Relatorios
@login_required
def reports(request):
    # Placeholder for reports view
    products_count = Product.objects.count()
    categories_count = Category.objects.count()
    return render(request, 'produtos/reports.html', {
        'products_count': products_count,
        'categories_count': categories_count
    })


