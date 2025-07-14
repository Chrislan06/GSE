# GSE - Sistema de Gerenciamento de Estoque

## Descrição

O GSE é um sistema web para gerenciamento de estoque, desenvolvido com Django, que permite o controle completo de produtos, categorias, movimentações de estoque e geração de relatórios. O sistema feito para pequenas empresas que desejam otimizar o controle de seus estoques.

## Funcionalidades

- **Gestão de Produtos** 
- **Gestão de Categorias**
- **Movimentação de Estoque**
- **Alertas de Estoque**
- **Relatórios** 
- **Dashboard** 
- **Login**
## Tecnologias e Bibliotecas Utilizadas

- **Backend:** Python 3, Django 4.2.7
- **Banco de Dados:** PostgreSQL
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap (via templates)
- **Geração de Relatórios:** 
  - `reportlab` (PDF)
  - `xlsxwriter` (Excel)
- **IA e Insights:** Integração com provedores de IA (ex: OpenAI) para geração de análises automáticas
- **Outras Bibliotecas:**
  - `requests` (requisições HTTP)
  - `python-decouple` (gestão de variáveis de ambiente)
  - `Pillow` (manipulação de imagens)

## Instalação

1. **Clone o repositório:**
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd projeto
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure o banco de dados:**
   - Edite o arquivo `.env` ou configure as variáveis de ambiente conforme necessário (veja o exemplo no `gse/settings.py`).
   - Certifique-se de que o PostgreSQL está rodando e que o banco de dados está criado.

5. **Aplique as migrações:**
   ```bash
   python manage.py migrate
   ```

6. **Crie um superusuário para acessar o admin:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver
   ```

8. **Acesse o sistema:**
   - Frontend: [http://localhost:8000/](http://localhost:8000/)
   - Admin: [http://localhost:8000/admin/](http://localhost:8000/admin/)

## Observações

- Para utilizar a geração de relatórios com IA, configure a chave de API do provedor desejado nas variáveis de ambiente.
- O sistema já possui autenticação de usuários integrada, permitindo o controle de acesso às funcionalidades.
- Os arquivos estáticos (CSS, JS, imagens) estão na pasta `static/`.
