import requests
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.http import HttpResponse
import io
import csv
import xlsxwriter
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from .models import Product, Category, StockMovement

logger = logging.getLogger(__name__)


class AIReportGenerator:
    """Gerador de relatórios usando IA"""
    
    def __init__(self, api_key: str = None, provider: str = "openai"):
        """
        Inicializa o gerador de relatórios
        
        Args:
            api_key: Chave da API de IA
            provider: Provedor de IA (openai, anthropic, etc.)
        """
        self.api_key = api_key or getattr(settings, 'AI_API_KEY', None)
        self.provider = provider
        self.base_url = self._get_api_url()
    
    def _get_api_url(self) -> str:
        """Retorna a URL base da API baseada no provedor"""
        if self.provider == "openai":
            return "https://api.openai.com/v1/chat/completions"
        elif self.provider == "anthropic":
            return "https://api.anthropic.com/v1/messages"
        else:
            raise ValueError(f"Provedor de IA não suportado: {self.provider}")
    
    def check_openai_status(self) -> Dict[str, Any]:
        """Verifica o status da conta OpenAI"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Tentar uma requisição simples para verificar o status
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [{'role': 'user', 'content': 'test'}],
                'max_tokens': 5
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                return {
                    'status': 'ok',
                    'message': 'API funcionando normalmente'
                }
            elif response.status_code == 429:
                error_response = response.json()
                error_message = error_response.get('error', {}).get('message', '')
                
                if 'quota' in error_message.lower():
                    return {
                        'status': 'quota_exceeded',
                        'message': 'Quota mensal excedida. Faça upgrade do plano.',
                        'solutions': [
                            'Upgrade para Pay as you go ($5 inicial)',
                            'Aguardar reset mensal',
                            'Usar Anthropic como alternativa'
                        ]
                    }
                else:
                    return {
                        'status': 'rate_limited',
                        'message': 'Rate limit atingido. Aguarde alguns minutos.',
                        'solutions': [
                            'Aguardar 1-2 minutos',
                            'Reduzir frequência de requisições'
                        ]
                    }
            else:
                return {
                    'status': 'error',
                    'message': f'Erro {response.status_code}: {response.text}',
                    'solutions': [
                        'Verificar chave da API',
                        'Verificar status da conta'
                    ]
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erro ao verificar status: {str(e)}',
                'solutions': [
                    'Verificar conexão com internet',
                    'Verificar chave da API'
                ]
            }
    
    def _prepare_stock_data(self, start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Prepara dados de estoque para análise
        
        Args:
            start_date: Data inicial para filtro
            end_date: Data final para filtro
            
        Returns:
            Dict com dados estruturados
        """
        # Buscar produtos
        products = Product.objects.all().select_related('category')
        
        # Buscar movimentações
        movements_query = StockMovement.objects.all().select_related('product', 'created_by')
        if start_date:
            movements_query = movements_query.filter(created_at__gte=start_date)
        if end_date:
            movements_query = movements_query.filter(created_at__lte=end_date)
        
        movements = list(movements_query)
        
        # Estruturar dados
        stock_data = {
            'summary': {
                'total_products': products.count(),
                'total_categories': Category.objects.count(),
                'low_stock_products': len([p for p in products if p.low_stock and p.stock > 0]),
                'out_of_stock_products': len([p for p in products if p.stock == 0]),
                'total_movements': len(movements)
            },
            'products': [
                {
                    'id': p.id,
                    'name': p.name,
                    'category': p.category.name if p.category else 'Sem categoria',
                    'stock': p.stock,
                    'min_stock': p.min_stock,
                    'price': float(p.price),
                    'status': p.stock_status,
                    'created_at': p.created_at.isoformat()
                }
                for p in products
            ],
            'movements': [
                {
                    'product_name': m.product.name,
                    'type': m.get_movement_type_display(),
                    'quantity': m.quantity,
                    'previous_stock': m.previous_stock,
                    'new_stock': m.new_stock,
                    'reason': m.reason,
                    'created_at': m.created_at.isoformat(),
                    'created_by': m.created_by.username if m.created_by else 'Sistema'
                }
                for m in movements
            ],
            'categories': [
                {
                    'name': c.name,
                    'product_count': c.products.count(),
                    'low_stock_count': c.get_low_stock_count(),
                    'out_of_stock_count': c.get_out_of_stock_count()
                }
                for c in Category.objects.all()
            ]
        }
        
        return stock_data
    
    def generate_ai_insights(self, data: Dict[str, Any]) -> str:
        """
        Gera insights usando IA
        
        Args:
            data: Dados de estoque estruturados
            
        Returns:
            String com insights gerados pela IA
        """
        logger.info(f"Tentando gerar insights com IA. Provider: {self.provider}")
        logger.info(f"API Key configurada: {'Sim' if self.api_key else 'Não'}")
        
        if not self.api_key:
            logger.warning("API Key não configurada. Usando fallback.")
            return self._generate_fallback_insights(data)
        
        try:
            logger.info("Criando prompt para IA...")
            prompt = self._create_analysis_prompt(data)
            
            if self.provider == "openai":
                logger.info("Chamando API do OpenAI...")
                result = self._call_openai_api(prompt)
                logger.info("Resposta da OpenAI recebida com sucesso!")
                return result
            elif self.provider == "anthropic":
                logger.info("Chamando API do Anthropic...")
                result = self._call_anthropic_api(prompt)
                logger.info("Resposta do Anthropic recebida com sucesso!")
                return result
            else:
                logger.warning(f"Provedor não suportado: {self.provider}. Usando fallback.")
                return self._generate_fallback_insights(data)
                
        except Exception as e:
            logger.error(f"Erro ao gerar insights com IA: {e}")
            logger.error(f"Tipo do erro: {type(e).__name__}")
            return self._generate_fallback_insights(data)
    
    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Cria prompt para análise de IA"""
        summary = data['summary']
        
        prompt = f"""
        Analise os dados de estoque abaixo e gere um relatório executivo em português com:
        
        1. Resumo executivo dos principais indicadores
        2. Análise de tendências e padrões nas movimentações
        3. Identificação de produtos que precisam de atenção
        4. Recomendações para otimização do estoque
        5. Alertas importantes
        
        Dados do sistema:
        - Total de produtos: {summary['total_products']}
        - Total de categorias: {summary['total_categories']}
        - Produtos com estoque baixo: {summary['low_stock_products']}
        - Produtos sem estoque: {summary['out_of_stock_products']}
        - Total de movimentações: {summary['total_movements']}
        
        Produtos com estoque baixo:
        {[p['name'] for p in data['products'] if p['status'] == 'Estoque baixo']}
        
        Produtos sem estoque:
        {[p['name'] for p in data['products'] if p['status'] == 'Sem estoque']}
        
        Movimentações recentes:
        {data['movements'][:10]}
        
        Gere um relatório profissional e acionável.
        """
        
        return prompt
    
    def _call_openai_api(self, prompt: str) -> str:
        """Chama a API do OpenAI"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': 'Você é um analista de estoque. Seja conciso e direto. Resposta em português.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 500,  # Reduzido ainda mais para economizar tokens
            'temperature': 0.7
        }
        
        logger.info(f"Enviando requisição para OpenAI: {self.base_url}")
        logger.info(f"Modelo: {data['model']}")
        logger.info(f"Max tokens: {data['max_tokens']}")
        
        # Tentar até 3 vezes com backoff exponencial
        for attempt in range(3):
            try:
                logger.info(f"Tentativa {attempt + 1} de 3")
                response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
                
                if response.status_code != 200:
                    logger.error(f"Erro na API do OpenAI: {response.status_code}")
                    logger.error(f"Resposta: {response.text}")
                    
                    if response.status_code == 429 and attempt < 2:
                        # Rate limit - usar backoff exponencial
                        import time
                        
                        # Verificar se é rate limit permanente (plano gratuito)
                        error_response = response.json() if response.text else {}
                        error_type = error_response.get('error', {}).get('type', '')
                        error_message = error_response.get('error', {}).get('message', '')
                        
                        # Detectar diferentes tipos de erro 429
                        if 'quota' in error_message.lower() or 'billing' in error_message.lower():
                            logger.error("=== QUOTA EXCEDIDA ===")
                            logger.error("Você atingiu o limite mensal de uso da OpenAI.")
                            logger.error("Soluções:")
                            logger.error("1. Upgrade para plano pago (Pay as you go - $5 inicial)")
                            logger.error("2. Aguardar reset mensal da quota gratuita")
                            logger.error("3. Usar Anthropic como alternativa")
                            raise requests.exceptions.HTTPError("Quota mensal excedida - upgrade do plano necessário")
                        
                        elif 'quota' in error_type.lower() or 'billing' in error_type.lower():
                            logger.error("Rate limit permanente detectado. Considere fazer upgrade do plano OpenAI.")
                            logger.error("Para contas gratuitas, o limite é muito baixo. Upgrade recomendado.")
                            raise requests.exceptions.HTTPError("Rate limit permanente - upgrade do plano necessário")
                        
                        # Verificar headers de rate limit se disponíveis
                        retry_after = response.headers.get('Retry-After')
                        if retry_after:
                            wait_time = int(retry_after)
                            logger.warning(f"Rate limit - aguardando {wait_time}s conforme header Retry-After...")
                        else:
                            # Backoff exponencial: 30s, 60s, 120s
                            wait_time = 30 * (2 ** attempt)
                            logger.warning(f"Rate limit atingido. Aguardando {wait_time}s (backoff exponencial)...")
                        
                        time.sleep(wait_time)
                        continue
                    else:
                        raise requests.exceptions.HTTPError(f"Erro {response.status_code}: {response.text}")
                
                result = response.json()
                logger.info("Resposta da OpenAI recebida com sucesso")
                
                # Verificar estrutura da resposta
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    logger.info(f"Conteúdo gerado: {len(content)} caracteres")
                    return content
                else:
                    logger.error(f"Estrutura de resposta inesperada: {result}")
                    raise ValueError("Estrutura de resposta inesperada da API do OpenAI")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Erro na requisição para OpenAI (tentativa {attempt + 1}): {e}")
                if attempt == 2:  # Última tentativa
                    raise
                continue
        
        # Se chegou aqui, todas as tentativas falharam
        logger.error("=== TODAS AS TENTATIVAS FALHARAM ===")
        logger.error("Possíveis soluções:")
        logger.error("1. Verificar se a chave da API está correta")
        logger.error("2. Verificar se a conta tem créditos disponíveis")
        logger.error("3. Fazer upgrade do plano OpenAI")
        logger.error("4. Usar Anthropic como alternativa (configure AI_PROVIDER=anthropic)")
        raise Exception("Todas as tentativas de conexão com OpenAI falharam")
    
    def _call_anthropic_api(self, prompt: str) -> str:
        """Chama a API do Anthropic (Claude)"""
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        data = {
            'model': 'claude-3-haiku-20240307',  # modelo mais garantido para contas gratuitas
            'max_tokens': 1500,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        try:
            logger.info(f"Enviando requisição para Anthropic: {self.base_url}")
            logger.info(f"Headers: {headers}")
            logger.info(f"Data: {data}")
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            if response.status_code != 200:
                logger.error(f"Erro na API do Anthropic: {response.status_code}")
                logger.error(f"Resposta: {response.text}")
                raise requests.exceptions.HTTPError(f"Erro {response.status_code}: {response.text}")
            result = response.json()
            logger.info("Resposta da Anthropic recebida com sucesso")
            # Verificar estrutura da resposta
            if 'content' in result and len(result['content']) > 0:
                return result['content'][0]['text']
            else:
                logger.error(f"Estrutura de resposta inesperada: {result}")
                raise ValueError("Estrutura de resposta inesperada da API do Anthropic")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para Anthropic: {e}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"Erro ao processar resposta da Anthropic: {e}")
            raise ValueError(f"Erro ao processar resposta: {e}")
    
    def _generate_fallback_insights(self, data: Dict[str, Any]) -> str:
        """Gera insights básicos quando IA não está disponível"""
        summary = data['summary']
        
        insights = f"""
        # Relatório de Estoque - Análise Executiva
        
        ## Resumo Executivo
        
        O sistema de estoque possui {summary['total_products']} produtos distribuídos em {summary['total_categories']} categorias.
        
        ## Indicadores Críticos
        
        - **Produtos com estoque baixo**: {summary['low_stock_products']}
        - **Produtos sem estoque**: {summary['out_of_stock_products']}
        - **Total de movimentações**: {summary['total_movements']}
        
        ## Produtos que Precisam de Atenção
        
        """
        
        # Adicionar produtos com estoque baixo
        low_stock_products = [p for p in data['products'] if p['status'] == 'Estoque baixo']
        if low_stock_products:
            insights += "\n### Produtos com Estoque Baixo:\n"
            for product in low_stock_products:
                insights += f"- {product['name']} (Estoque: {product['stock']}, Mínimo: {product['min_stock']})\n"
        
        # Adicionar produtos sem estoque
        out_of_stock_products = [p for p in data['products'] if p['status'] == 'Sem estoque']
        if out_of_stock_products:
            insights += "\n### Produtos Sem Estoque:\n"
            for product in out_of_stock_products:
                insights += f"- {product['name']}\n"
        
        insights += """
        
        ## Recomendações
        
        1. **Reabastecimento Urgente**: Produtos sem estoque devem ser reabastecidos imediatamente
        2. **Monitoramento**: Produtos com estoque baixo devem ser monitorados de perto
        3. **Análise de Tendências**: Analisar padrões de movimentação para otimizar estoques
        4. **Revisão de Estoque Mínimo**: Avaliar se os níveis mínimos estão adequados
        
        ## Próximos Passos
        
        - Implementar alertas automáticos para estoque baixo
        - Estabelecer processos de reabastecimento
        - Revisar políticas de estoque mínimo
        - Implementar análise preditiva de demanda
        """
        
        return insights


class ReportExporter:
    """Exportador de relatórios em diferentes formatos"""
    
    @staticmethod
    def export_to_pdf(data: Dict[str, Any], insights: str, filename: str = "relatorio_estoque.pdf") -> HttpResponse:
        """Exporta relatório para PDF"""
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Criar documento PDF
        doc = SimpleDocTemplate(response, pagesize=A4)
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centralizado
        )
        
        # Título
        story.append(Paragraph("Relatório de Estoque - Análise Executiva", title_style))
        story.append(Spacer(1, 20))
        
        # Data do relatório
        story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Resumo
        summary = data['summary']
        summary_data = [
            ['Indicador', 'Valor'],
            ['Total de Produtos', str(summary['total_products'])],
            ['Total de Categorias', str(summary['total_categories'])],
            ['Produtos com Estoque Baixo', str(summary['low_stock_products'])],
            ['Produtos Sem Estoque', str(summary['out_of_stock_products'])],
            ['Total de Movimentações', str(summary['total_movements'])]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Resumo Executivo", styles['Heading2']))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Insights da IA
        story.append(Paragraph("Análise e Insights", styles['Heading2']))
        insights_paragraphs = insights.split('\n\n')
        for paragraph in insights_paragraphs:
            if paragraph.strip():
                if paragraph.startswith('#'):
                    # É um título
                    level = paragraph.count('#')
                    if level == 1:
                        story.append(Paragraph(paragraph.replace('#', '').strip(), title_style))
                    elif level == 2:
                        story.append(Paragraph(paragraph.replace('##', '').strip(), styles['Heading2']))
                    elif level == 3:
                        story.append(Paragraph(paragraph.replace('###', '').strip(), styles['Heading3']))
                else:
                    story.append(Paragraph(paragraph, styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Construir PDF
        doc.build(story)
        return response
    
    @staticmethod
    def export_to_excel(data: Dict[str, Any], insights: str, filename: str = "relatorio_estoque.xlsx") -> HttpResponse:
        """Exporta relatório para Excel"""
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Criar workbook Excel
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Formatos
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1
        })
        
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center'
        })
        
        # Planilha de Resumo
        summary_sheet = workbook.add_worksheet('Resumo')
        summary_sheet.write(0, 0, 'Relatório de Estoque - Análise Executiva', title_format)
        summary_sheet.write(2, 0, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        
        # Dados do resumo
        summary = data['summary']
        summary_data = [
            ['Indicador', 'Valor'],
            ['Total de Produtos', summary['total_products']],
            ['Total de Categorias', summary['total_categories']],
            ['Produtos com Estoque Baixo', summary['low_stock_products']],
            ['Produtos Sem Estoque', summary['out_of_stock_products']],
            ['Total de Movimentações', summary['total_movements']]
        ]
        
        for row, (indicator, value) in enumerate(summary_data, start=4):
            summary_sheet.write(row, 0, indicator, header_format if row == 4 else None)
            summary_sheet.write(row, 1, value)
        
        # Planilha de Produtos
        products_sheet = workbook.add_worksheet('Produtos')
        products_headers = ['ID', 'Nome', 'Categoria', 'Estoque', 'Estoque Mínimo', 'Preço', 'Status']
        
        for col, header in enumerate(products_headers):
            products_sheet.write(0, col, header, header_format)
        
        for row, product in enumerate(data['products'], start=1):
            products_sheet.write(row, 0, product['id'])
            products_sheet.write(row, 1, product['name'])
            products_sheet.write(row, 2, product['category'])
            products_sheet.write(row, 3, product['stock'])
            products_sheet.write(row, 4, product['min_stock'])
            products_sheet.write(row, 5, product['price'])
            products_sheet.write(row, 6, product['status'])
        
        # Planilha de Movimentações
        movements_sheet = workbook.add_worksheet('Movimentações')
        movements_headers = ['Produto', 'Tipo', 'Quantidade', 'Estoque Anterior', 'Novo Estoque', 'Motivo', 'Data', 'Usuário']
        
        for col, header in enumerate(movements_headers):
            movements_sheet.write(0, col, header, header_format)
        
        for row, movement in enumerate(data['movements'], start=1):
            movements_sheet.write(row, 0, movement['product_name'])
            movements_sheet.write(row, 1, movement['type'])
            movements_sheet.write(row, 2, movement['quantity'])
            movements_sheet.write(row, 3, movement['previous_stock'])
            movements_sheet.write(row, 4, movement['new_stock'])
            movements_sheet.write(row, 5, movement['reason'])
            movements_sheet.write(row, 6, movement['created_at'][:10])
            movements_sheet.write(row, 7, movement['created_by'])
        
        # Planilha de Insights
        insights_sheet = workbook.add_worksheet('Análise IA')
        insights_sheet.write(0, 0, 'Análise e Insights Gerados por IA', title_format)
        insights_sheet.write(2, 0, insights)
        
        workbook.close()
        output.seek(0)
        response.write(output.getvalue())
        return response
    
    @staticmethod
    def export_to_csv(data: Dict[str, Any], filename: str = "relatorio_estoque.csv") -> HttpResponse:
        """Exporta relatório para CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Escrever cabeçalho
        writer.writerow(['Relatório de Estoque'])
        writer.writerow([f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}'])
        writer.writerow([])
        
        # Resumo
        summary = data['summary']
        writer.writerow(['RESUMO EXECUTIVO'])
        writer.writerow(['Indicador', 'Valor'])
        writer.writerow(['Total de Produtos', summary['total_products']])
        writer.writerow(['Total de Categorias', summary['total_categories']])
        writer.writerow(['Produtos com Estoque Baixo', summary['low_stock_products']])
        writer.writerow(['Produtos Sem Estoque', summary['out_of_stock_products']])
        writer.writerow(['Total de Movimentações', summary['total_movements']])
        writer.writerow([])
        
        # Produtos
        writer.writerow(['PRODUTOS'])
        writer.writerow(['ID', 'Nome', 'Categoria', 'Estoque', 'Estoque Mínimo', 'Preço', 'Status'])
        for product in data['products']:
            writer.writerow([
                product['id'],
                product['name'],
                product['category'],
                product['stock'],
                product['min_stock'],
                product['price'],
                product['status']
            ])
        writer.writerow([])
        
        # Movimentações
        writer.writerow(['MOVIMENTAÇÕES'])
        writer.writerow(['Produto', 'Tipo', 'Quantidade', 'Estoque Anterior', 'Novo Estoque', 'Motivo', 'Data', 'Usuário'])
        for movement in data['movements']:
            writer.writerow([
                movement['product_name'],
                movement['type'],
                movement['quantity'],
                movement['previous_stock'],
                movement['new_stock'],
                movement['reason'],
                movement['created_at'][:10],
                movement['created_by']
            ])
        
        return response


class AIReportService:
    """Serviço principal para geração de relatórios com IA"""
    
    def __init__(self, api_key: str = None, provider: str = "openai"):
        self.ai_generator = AIReportGenerator(api_key, provider)
        self.exporter = ReportExporter()
    
    def generate_comprehensive_report(self, 
                                    format: str = "xlsx",
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None,
                                    filename: str = None) -> HttpResponse:
        """
        Gera relatório completo com IA
        
        Args:
            format: Formato do relatório (pdf, xlsx, csv)
            start_date: Data inicial para filtro
            end_date: Data final para filtro
            filename: Nome do arquivo
            
        Returns:
            HttpResponse com o arquivo do relatório
        """
        try:
            # Preparar dados
            data = self.ai_generator._prepare_stock_data(start_date, end_date)
            
            # Gerar insights com IA
            insights = self.ai_generator.generate_ai_insights(data)
            
            # Gerar nome do arquivo
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"relatorio_estoque_{timestamp}.{format}"
            
            # Exportar no formato solicitado
            if format.lower() == "pdf":
                return self.exporter.export_to_pdf(data, insights, filename)
            elif format.lower() in ["xlsx", "excel"]:
                return self.exporter.export_to_excel(data, insights, filename)
            elif format.lower() == "csv":
                return self.exporter.export_to_csv(data, filename)
            else:
                raise ValueError(f"Formato não suportado: {format}")
                
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            raise
    
    def get_available_formats(self) -> List[str]:
        """Retorna formatos disponíveis"""
        return ["pdf", "xlsx", "csv"]
    
    def get_ai_providers(self) -> List[str]:
        """Retorna provedores de IA disponíveis"""
        return ["openai", "anthropic"] 