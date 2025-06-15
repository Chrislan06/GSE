from django import forms
from .models import Product, Category, StockMovement

class ProductForm(forms.ModelForm):
    """Formulário para criação e edição de produtos"""
    
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'min_stock', 'category']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do produto'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do produto'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'min_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'name': 'Nome',
            'description': 'Descrição',
            'price': 'Preço (R$)',
            'stock': 'Estoque Atual',
            'min_stock': 'Estoque Mínimo',
            'category': 'Categoria'
        }
        help_texts = {
            'min_stock': 'Quantidade mínima em estoque antes de gerar alerta',
            'stock': 'Quantidade atual em estoque'
        }

    def clean(self):
        """Validação personalizada do formulário"""
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        stock = cleaned_data.get('stock')
        min_stock = cleaned_data.get('min_stock')
        
        if price is not None and price <= 0:
            raise forms.ValidationError('O preço deve ser maior que zero.')
        
        if stock is not None and stock < 0:
            raise forms.ValidationError('O estoque não pode ser negativo.')
        
        if min_stock is not None and min_stock < 0:
            raise forms.ValidationError('O estoque mínimo não pode ser negativo.')
        
        return cleaned_data


class CategoryForm(forms.ModelForm):
    """Formulário para criação e edição de categorias"""
    
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da categoria'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição da categoria (opcional)'
            }),
        }
        labels = {
            'name': 'Nome',
            'description': 'Descrição'
        }

    def clean_name(self):
        """Validação personalizada do nome da categoria"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if not name:
                raise forms.ValidationError('O nome da categoria não pode estar vazio.')
        return name


class StockMovementForm(forms.Form):
    """Formulário para movimentações de estoque"""
    
    MOVEMENT_TYPES = [
        ('IN', 'Entrada de Estoque'),
        ('OUT', 'Saída de Estoque'),
        ('ADJUSTMENT', 'Ajuste de Estoque'),
    ]
    
    movement_type = forms.ChoiceField(
        choices=MOVEMENT_TYPES,
        label='Tipo de Movimento',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'movement_type'
        })
    )
    
    quantity = forms.IntegerField(
        label='Quantidade',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'placeholder': 'Quantidade'
        })
    )
    
    reason = forms.CharField(
        label='Motivo',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Motivo da movimentação (opcional)'
        })
    )

    def __init__(self, *args, **kwargs):
        """Inicialização do formulário com contexto do produto"""
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        if self.product:
            # Ajustar labels baseado no tipo de movimento
            self.fields['movement_type'].widget.attrs.update({
                'onchange': 'updateQuantityLabel(this.value)'
            })

    def clean(self):
        """Validação personalizada do formulário"""
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        quantity = cleaned_data.get('quantity')
        
        if movement_type == 'OUT' and self.product:
            # Verificar se há estoque suficiente para saída
            if quantity > self.product.stock:
                raise forms.ValidationError(
                    f'Estoque insuficiente. Estoque atual: {self.product.stock}'
                )
        
        return cleaned_data


class ProductSearchForm(forms.Form):
    """Formulário para busca de produtos"""
    
    SEARCH_FIELDS = [
        ('name', 'Nome'),
        ('description', 'Descrição'),
        ('category', 'Categoria'),
    ]
    
    search_term = forms.CharField(
        label='Termo de Busca',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite para buscar...'
        })
    )
    
    search_field = forms.ChoiceField(
        choices=SEARCH_FIELDS,
        label='Campo de Busca',
        initial='name',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    category_filter = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label='Filtrar por Categoria',
        required=False,
        empty_label='Todas as categorias',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    stock_status = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('normal', 'Estoque Normal'),
            ('low', 'Estoque Baixo'),
            ('out', 'Sem Estoque'),
        ],
        label='Status do Estoque',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )


class StockReportForm(forms.Form):
    """Formulário para relatórios de estoque"""
    
    REPORT_TYPES = [
        ('all', 'Todos os Produtos'),
        ('low_stock', 'Produtos com Estoque Baixo'),
        ('out_of_stock', 'Produtos Sem Estoque'),
        ('by_category', 'Por Categoria'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        label='Tipo de Relatório',
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label='Categoria',
        required=False,
        empty_label='Todas as categorias',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    include_movements = forms.BooleanField(
        label='Incluir Movimentações',
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    date_from = forms.DateField(
        label='Data Inicial',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        label='Data Final',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )