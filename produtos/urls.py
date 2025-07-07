from django.urls import path
from . import views

app_name = 'produtos'

urlpatterns = [
    # URLs de Produtos
    path('', views.product_list, name='lista_produtos'),
    path('produto/novo/', views.product_create, name='criar_produto'),
    path('produto/<int:pk>/', views.product_detail, name='detalhe_produto'),
    path('produto/<int:pk>/editar/', views.product_update, name='editar_produto'),
    path('produto/<int:pk>/excluir/', views.product_delete, name='excluir_produto'),
    
    # URLs de Categorias
    path('categorias/', views.category_list, name='lista_categorias'),
    path('categoria/nova/', views.category_create, name='criar_categoria'),
    path('categoria/<int:pk>/', views.category_detail, name='detalhe_categoria'),
    path('categoria/<int:pk>/editar/', views.category_update, name='editar_categoria'),
    path('categoria/<int:pk>/excluir/', views.category_delete, name='excluir_categoria'),
    
    # URLs de Estoque
    path('produto/<int:pk>/estoque/', views.stock_movement, name='movimentacao_estoque'),
    
    # URLs de Relatórios
    path('relatorios/', views.reports, name='relatorios'),
    path('relatorios/ia/', views.ai_report_generator, name='relatorios_ia'),
    path('relatorios/ia/gerar/', views.generate_ai_report, name='gerar_relatorio_ia'),
    path('relatorios/ia/preview/', views.preview_ai_insights, name='preview_insights_ia'),
    path('alertas-estoque/', views.low_stock_alert, name='alertas_estoque'),
    
    # URLs AJAX
    path('api/produto/<int:pk>/', views.get_product_data, name='api_produto'),
    path('api/ai/status/', views.check_ai_status, name='check_ai_status'),
]