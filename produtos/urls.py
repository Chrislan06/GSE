from django.urls import path
from . import views
urlpatterns = [
    # Produtos
    path('', views.product_list, name='lista_produtos'),
    path('produtos/novo/', views.product_create, name='novo_produto'),
    path('produtos/editar/<int:pk>/', views.product_update, name='editar_produto'),
    path('produtos/excluir/<int:pk>/', views.product_delete, name='excluir_produto'),

    # Categorias
    path('categorias/', views.category_list, name='lista_categorias'),
    path('categorias/novo/', views.category_create, name='nova_categoria'),
    path('categorias/editar/<int:pk>/', views.category_update, name='editar_categoria'),
    path('categorias/excluir/<int:pk>/', views.category_delete, name='excluir_categoria'),

    # Relatorios
    path('produtos/relatorios/', views.reports, name='relatorios'),
]