# Meatz Burger - Sistema de Gerenciamento de Hamburguerias

## Overview

Meatz Burger é um sistema completo de gerenciamento para hamburguerias, projetado para otimizar a operação e a experiência do cliente. Ele oferece uma interface moderna, inspirada no site oficial do Meatz Burger, e atende a clientes, funcionários e administradores. O sistema abrange desde a navegação do cardápio e realização de pedidos por clientes, até o gerenciamento de mesas, PDV, cozinha e caixa por funcionários, e controle administrativo completo de produtos, categorias, pedidos, mesas e usuários.

## User Preferences

Linguagem preferida: Português (Brasil)
Estilo de comunicação: Linguagem simples e cotidiana

## System Architecture

### Application Structure

O aplicativo segue uma arquitetura modular baseada em Blueprints do Flask, organizando as funcionalidades em componentes como rotas principais para o cliente, autenticação, módulo administrativo, sistema PDV/POS e um módulo de chatbot.

### Data Architecture

O sistema utiliza SQLite3 puro (sem ORM) para armazenamento de dados localmente em `data/meatz.db`. A camada de acesso a dados (`app/database.py`, `app/db_operations.py` e `app/db_operations_extended.py`) gerencia as operações CRUD para mais de 30 tabelas, incluindo:

**Tabelas Core**: `user`, `category`, `product`, `table`, `order`, `order_item`, `payment`, `settings`

**Módulo de Modificadores**: `product_modifier_group`, `product_modifier_option`, `order_item_modifier`

**Gestão de Mesas**: `table_grouping`, `table_merge_history`

**Operações de Atendimento**: `order_transfer`, `service_message`, `service_message_receipt`, `order_template`

**Sistema Financeiro**: `service_charge_policy`, `order_service_charge`, `payment_split`, `cash_operation`, `cashier_session`

**Delivery**: `delivery_driver`, `delivery_order`, `delivery_route_event`

**Reservas**: `reservation`, `waitlist_entry`

**Estoque Avançado**: `inventory`, `product_ingredient`, `inventory_batch`, `inventory_transaction`

**Sistema de Auditoria**: `audit_log`

**Recursos Adicionais**: `customer`, `loyalty_transaction`, `product_suggestion`, `order_split`, `order_split_item`, `shift_assignment`, `print_job`, `report_export`, `notification_subscription`

O relacionamento entre as tabelas é mantido via Foreign Keys para garantir a integridade dos dados. O sistema implementa migrações idempotentes para adicionar novas colunas às tabelas existentes sem perder dados.

### Frontend Architecture

A interface utiliza Jinja2 para templating e Bootstrap 5 para design responsivo. O Design System é alinhado com a identidade visual do Meatz Burger oficial, empregando uma paleta de cores específica (#E99856, #F28D34, #6A1C0B, #FEF2E9, #FFFFFF, #000000) e tipografia (Poppins para títulos, Montserrat para corpo de texto). Elementos visuais como border-radius de 20px/30px e botões customizados complementam o design. O JavaScript Vanilla com Fetch API é usado para interações AJAX.

### Authentication & Authorization

A autenticação é gerida pelo Flask-Login com senhas seguras. A autorização baseada em funções (`@login_required`, `@admin_required`) restringe o acesso a rotas específicas. A segurança é reforçada com hash de senha, gerenciamento de sessão seguro, proteção CSRF via Flask-WTF e senha padrão do administrador configurável via variável de ambiente.

### State Management

O carrinho de compras é baseado em sessões Flask. Os pedidos possuem uma máquina de estados (`pendente`, `preparando`, `pronto`, `pago`, `finalizado`, `cancelado`). As mesas também gerenciam seu estado (`livre`, `ocupada`, `reservada`) e o pedido atual.

### Key Features Implemented

- **Sistema para Garçom Avançado**: 
  - Comanda digital com status de itens em tempo real
  - Mapa visual do salão com layout interativo de mesas
  - **Abertura e fechamento de mesas com validação de pagamento** - garçom pode abrir mesas livres e fechar mesas ocupadas, sendo que o fechamento só é permitido após confirmação do pagamento
  - Juntar e dividir mesas com transferência automática de pedidos
  - Transferência de comandas entre garçons com histórico completo
  - Sistema de mensagens rápidas com cozinha/bar em tempo real
  - Duplicar comandas e repetir pedidos anteriores
  - Modificadores de produtos (ponto da carne, adicionais, sem ingredientes)
  - Sistema de gorjeta manual e automática configurável
  - Divisão de conta avançada (por pessoa, item, valor) com pagamento múltiplo

- **Sistema para Cozinha (KDS)**: 
  - Painel de pedidos em tempo real com prioridade por cores
  - Controle de tempo de preparo por item com alertas de atraso
  - Filtro por seção de preparo (chapa, saladas, bebidas, etc)
  - Status individual de itens com timestamps
  - Recebimento de mensagens dos garçons

- **Sistema PDV/Caixa Completo**: 
  - Integração com comandas e delivery
  - Múltiplos métodos de pagamento (Pix, cartão, dinheiro)
  - Sangrias e suprimentos com controle de caixa
  - Abertura e fechamento de caixa por operador
  - Divisão de contas com pagamentos parciais
  - Relatórios completos por período

- **Gestão e Administração Premium**:
  - Dashboard gerencial com métricas avançadas em tempo real
  - Relatórios completos (faturamento, produtos, ticket médio, performance)
  - Controle de estoque com lotes, validade e alertas inteligentes
  - Sistema de fidelidade de clientes
  - Gestão de sugestões de produtos complementares
  - Controle de modificadores de produtos
  - Configuração de políticas de gorjeta
  - Log de auditoria completo de todas as ações

- **Módulo de Delivery**:
  - Cadastro e gestão de entregadores
  - Controle de pedidos de delivery
  - Rastreamento de rotas e status de entrega
  - Histórico completo de entregas

- **Sistema de Reservas**:
  - Reserva de mesas por data e horário
  - Fila de espera (waitlist)
  - Confirmação de reservas
  - Gestão de disponibilidade de mesas

- **Diferenciais Únicos**: 
  - Rastreamento completo do ciclo de vida do pedido
  - Sistema de priorização automática na cozinha
  - Sugestões inteligentes de produtos complementares
  - Controle granular de estoque com lotes e validade
  - Programa de fidelidade integrado
  - Divisão de contas flexível com múltiplas formas
  - Auditoria completa de todas as operações
  - Sistema de mensagens em tempo real entre equipes
  - Histórico completo de transferências e modificações

- **Configurações Avançadas**: 
  - Sistema de configurações da loja personalizável
  - Configuração de gorjetas automáticas
  - Gestão de horários e turnos de funcionários
  - Políticas de atendimento customizáveis

- **Dados de Exemplo**: Criação automática de categorias e produtos demonstrativos no primeiro start para facilitar a demonstração.

## External Dependencies

### Required Services

- **Database**: SQLite3 puro, utilizando um arquivo local `data/meatz.db`. Para deploy em plataformas como Render, é necessário um Persistent Disk.
- **Google Gemini AI**: Integração **totalmente opcional** para chatbot IA. O sistema funciona completamente sem a variável de ambiente `GEMINI_API_KEY`. Quando não configurada, o chatbot usa respostas baseadas em regras com dados do banco de dados (produtos, configurações) para fornecer uma experiência funcional.

### Third-Party Libraries

- **Core Framework**: Flask 3.0.0, Werkzeug 3.0.1, Gunicorn 21.2.0.
- **Authentication**: Flask-Login 0.6.3.
- **Forms & Security**: Flask-WTF 1.2.1.
- **Configuration**: python-dotenv 1.0.0.
- **AI**: google-generativeai 0.3.2.

### Environment Configuration

**Variáveis obrigatórias:**
- `SECRET_KEY`: Criptografia de sessão
- `SESSION_SECRET`: Gerenciamento de sessão Flask

**Variáveis opcionais:**
- `GEMINI_API_KEY`: Chatbot com IA (totalmente opcional - sistema funciona sem)
- `ADMIN_DEFAULT_PASSWORD`: Senha inicial do administrador (padrão: admin123)

## Recent Changes

### Novembro 2025 - Correções de Validação e Estabilidade

**Validações de Formulários Administrativos:**
- Implementadas validações robustas em todos os formulários administrativos (produtos, mesas, reservas, operações de caixa)
- Sistema agora rejeita submissões com dados inválidos ou vazios, exibindo mensagens claras ao usuário
- Prevenção de criação de registros com valores zero ou inválidos que violam regras de negócio

**Sistema de Chatbot Aprimorado:**
- Chatbot agora funciona completamente sem `GEMINI_API_KEY`
- Implementado sistema de respostas baseadas em regras com matching de palavras-chave
- Integração com dados do banco (produtos, configurações) para fornecer informações relevantes
- Fallback automático entre modo IA e modo baseado em regras

**Correções de PDV:**
- Adicionadas validações de `request.json` em todas as rotas PDV para evitar crashes
- Tratamento adequado de payloads vazios ou malformados
- Melhor experiência de erro para o usuário

**Melhorias de UX:**
- Adicionado favicon com emoji de hambúrguer (🍔)
- Configurado `Cache-Control` para evitar problemas de cache do navegador
- Headers HTTP otimizados para garantir conteúdo sempre atualizado

**Correções Técnicas:**
- Resolvidos 34+ erros de LSP relacionados a validação de tipos
- Melhor tratamento de tipos em conversões float/int
- Código mais robusto e à prova de erros

**Sistema de Navegação Completo:**
- Implementados botões de voltar em todas as 32 páginas do sistema
- Navegação contextual inteligente nas páginas do cliente para melhor UX:
  - cart.html → volta para menu (usuário veio do cardápio)
  - checkout.html → volta para cart (usuário veio do carrinho)
  - product_detail.html → volta para menu (usuário estava navegando no cardápio)
  - track_order.html → volta para home
  - menu.html → volta para home
- Todas as páginas admin voltam para dashboard
- Todas as páginas PDV voltam para PDV index (exceto finalize_order que volta para a mesa)
- Todas as páginas de autenticação voltam para home
- Estilo consistente com Bootstrap (btn btn-outline-secondary ou btn btn-outline-light para KDS)
- Navegação alinhada com padrões de mercado (Amazon, iFood, DoorDash)
