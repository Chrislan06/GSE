from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Product, Category, StockMovement, StockObserver, LowStockNotifier, OutOfStockNotifier


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin para o modelo Category"""
    list_display = ['name', 'description', 'products_count', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'description')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def products_count(self, obj):
        """Retorna o número de produtos na categoria"""
        return obj.products.count()
    products_count.short_description = 'Produtos'
    
    def get_queryset(self, request):
        """Otimiza a consulta incluindo contagem de produtos"""
        return super().get_queryset(request).prefetch_related('products')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin para o modelo Product"""
    list_display = [
        'name', 'category', 'price', 'stock', 'min_stock', 
        'stock_status_display', 'low_stock_warning', 'created_at'
    ]
    list_filter = [
        'category', 'created_at', 'updated_at'
    ]
    search_fields = ['name', 'description', 'category__name']
    ordering = ['name']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'description', 'category')
        }),
        ('Preços e Estoque', {
            'fields': ('price', 'stock', 'min_stock')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['add_stock', 'remove_stock', 'adjust_stock', 'setup_observers']
    
    def stock_status_display(self, obj):
        """Exibe o status do estoque com cores"""
        if obj.stock == 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>',
                obj.stock_status
            )
        elif obj.low_stock:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{}</span>',
                obj.stock_status
            )
        else:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                obj.stock_status
            )
    stock_status_display.short_description = 'Status do Estoque'
    
    def low_stock_warning(self, obj):
        """Exibe aviso de estoque baixo"""
        if obj.low_stock:
            return format_html(
                '<span style="color: red;">⚠️ Estoque Baixo</span>'
            )
        return '-'
    low_stock_warning.short_description = 'Aviso'
    
    def add_stock(self, request, queryset):
        """Ação para adicionar estoque"""
        for product in queryset:
            product.update_stock(10, 'IN', 'Adição via admin', request.user)
        self.message_user(request, f"Estoque adicionado para {queryset.count()} produtos.")
    add_stock.short_description = "Adicionar 10 unidades ao estoque"
    
    def remove_stock(self, request, queryset):
        """Ação para remover estoque"""
        for product in queryset:
            if product.stock >= 5:
                product.update_stock(5, 'OUT', 'Remoção via admin', request.user)
        self.message_user(request, f"Estoque removido para {queryset.count()} produtos.")
    remove_stock.short_description = "Remover 5 unidades do estoque"
    
    def adjust_stock(self, request, queryset):
        """Ação para ajustar estoque"""
        for product in queryset:
            if product.stock < product.min_stock:
                product.update_stock(
                    product.min_stock + 10, 
                    'ADJUSTMENT', 
                    'Ajuste via admin', 
                    request.user
                )
        self.message_user(request, f"Estoque ajustado para {queryset.count()} produtos.")
    adjust_stock.short_description = "Ajustar estoque para mínimo + 10"
    
    def setup_observers(self, request, queryset):
        """Ação para configurar observadores"""
        for product in queryset:
            # Adicionar observadores padrão
            low_stock_observer = LowStockNotifier()
            out_of_stock_observer = OutOfStockNotifier()
            
            product.add_observer(low_stock_observer)
            product.add_observer(out_of_stock_observer)
        
        self.message_user(request, f"Observadores configurados para {queryset.count()} produtos.")
    setup_observers.short_description = "Configurar observadores de estoque"
    
    def get_queryset(self, request):
        """Otimiza a consulta incluindo categoria"""
        return super().get_queryset(request).select_related('category')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Admin para o modelo StockMovement"""
    list_display = [
        'product', 'movement_type', 'quantity', 'previous_stock', 
        'new_stock', 'reason', 'created_by', 'created_at'
    ]
    list_filter = [
        'movement_type', 'created_at', 'created_by', 'product__category'
    ]
    search_fields = ['product__name', 'reason', 'created_by__username']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Movimentação', {
            'fields': ('product', 'movement_type', 'quantity', 'reason')
        }),
        ('Estoque', {
            'fields': ('previous_stock', 'new_stock')
        }),
        ('Responsável', {
            'fields': ('created_by', 'created_at')
        }),
    )
    
    readonly_fields = ['previous_stock', 'new_stock', 'created_by', 'created_at']
    
    def save_model(self, request, obj, form, change):
        """Salva o modelo e registra o usuário"""
        if not change:  # Apenas na criação
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Otimiza a consulta incluindo relacionamentos"""
        return super().get_queryset(request).select_related('product', 'created_by')


# Registro dos observadores (opcional, para referência)
class StockObserverAdmin(admin.ModelAdmin):
    """Admin para observadores de estoque (apenas para referência)"""
    list_display = ['__str__', 'get_type']
    
    def get_type(self, obj):
        """Retorna o tipo do observador"""
        if isinstance(obj, LowStockNotifier):
            return 'Notificador de Estoque Baixo'
        elif isinstance(obj, OutOfStockNotifier):
            return 'Notificador de Estoque Zero'
        return 'Observador Genérico'
    get_type.short_description = 'Tipo'


# Configurações personalizadas do admin
admin.site.site_header = "GSE - Sistema de Gerenciamento de Estoque"
admin.site.site_title = "GSE Admin"
admin.site.index_title = "Painel de Controle"

# Adicionar links úteis no admin
class GSEAdminSite(admin.AdminSite):
    """Site admin personalizado para GSE"""
    
    def get_app_list(self, request):
        """Adiciona links úteis ao admin"""
        app_list = super().get_app_list(request)
        
        # Adicionar seção de relatórios
        if request.user.is_staff:
            app_list.append({
                'name': 'Relatórios',
                'app_label': 'relatorios',
                'models': [
                    {
                        'name': 'Dashboard',
                        'object_name': 'dashboard',
                        'admin_url': '/admin/dashboard/',
                        'view_only': True,
                    },
                    {
                        'name': 'Relatório de Estoque',
                        'object_name': 'stock_report',
                        'admin_url': '/admin/stock-report/',
                        'view_only': True,
                    },
                ]
            })
        
        return app_list