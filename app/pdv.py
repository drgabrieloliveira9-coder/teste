from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.db_operations import Product, Category, Order, Table, OrderItem, Payment, ProductSuggestion, Customer
from app.db_operations_extended import (ProductModifierGroup, ProductModifierOption, OrderItemModifier,
                                        TableGrouping, TableMergeHistory, OrderTransfer, ServiceMessage,
                                        OrderTemplate, ServiceChargePolicy, OrderServiceCharge, PaymentSplit,
                                        DeliveryOrder, AuditLog)
from datetime import datetime

pdv = Blueprint('pdv', __name__)

@pdv.route('/')
@login_required
def index():
    tables = Table.get_all()
    categories = Category.get_all()
    products = Product.get_all(available_only=True)
    return render_template('pdv/index.html', tables=tables, categories=categories, products=products)

@pdv.route('/mesa/<int:table_id>')
@login_required
def table_order(table_id):
    table = Table.get_by_id(table_id)
    if not table:
        abort(404)
    
    categories = Category.get_all()
    products = Product.get_all(available_only=True)
    
    current_order = None
    if table['current_order_id']:
        current_order = Order.get_by_id(table['current_order_id'])
    
    return render_template('pdv/table_order.html', 
                         table=table, 
                         categories=categories, 
                         products=products,
                         current_order=current_order)

@pdv.route('/api/pedido/criar', methods=['POST'])
@login_required
def create_order():
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    table_id = data.get('table_id')
    items = data.get('items', [])
    
    table = Table.get_by_id(table_id)
    if not table:
        abort(404)
    
    order_id = Order.create(
        table_id=table_id,
        user_id=current_user.id,
        status='pendente',
        total=0.0
    )
    
    total = 0
    for item in items:
        product = Product.get_by_id(item['product_id'])
        if product:
            OrderItem.create(
                order_id=order_id,
                product_id=product['id'],
                quantity=item['quantity'],
                price=product['price'],
                notes=item.get('notes', '')
            )
            total += product['price'] * item['quantity']
    
    Order.update(order_id, total=total)
    Table.update(table_id, status='ocupada', current_order_id=order_id)
    
    return jsonify({'success': True, 'order_id': order_id})

@pdv.route('/api/pedido/<int:order_id>/adicionar-item', methods=['POST'])
@login_required
def add_order_item(order_id):
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    order = Order.get_by_id(order_id)
    if not order:
        abort(404)
    
    product = Product.get_by_id(data['product_id'])
    if not product:
        return jsonify({'success': False, 'error': 'Produto não encontrado'}), 404
    
    quantity = int(data.get('quantity', 1))
    OrderItem.create(
        order_id=order['id'],
        product_id=product['id'],
        quantity=quantity,
        price=product['price'],
        notes=data.get('notes', '')
    )
    
    new_total = order['total'] + (product['price'] * quantity)
    Order.update(order_id, total=new_total)
    
    return jsonify({'success': True})

@pdv.route('/api/pedido/<int:order_id>/remover-item/<int:item_id>', methods=['POST'])
@login_required
def remove_order_item(order_id, item_id):
    order = Order.get_by_id(order_id)
    if not order:
        abort(404)
    
    item = OrderItem.get_by_id(item_id)
    if not item:
        abort(404)
    
    if item['order_id'] != order['id']:
        return jsonify({'success': False, 'error': 'Item não pertence a este pedido'}), 400
    
    new_total = order['total'] - (item['price'] * item['quantity'])
    OrderItem.delete(item_id)
    Order.update(order_id, total=new_total)
    
    return jsonify({'success': True})

@pdv.route('/pedido/<int:order_id>/finalizar', methods=['GET', 'POST'])
@login_required
def finalize_order(order_id):
    order = Order.get_by_id(order_id)
    if not order:
        abort(404)
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        
        Payment.create(
            order_id=order['id'],
            amount=order['total'],
            method=payment_method,
            status='pago'
        )
        
        Order.update(order_id, status='pago', payment_method=payment_method)
        
        if order['table_id']:
            Table.update(order['table_id'], status='livre', current_order_id=None)
        
        flash('Pedido finalizado com sucesso!', 'success')
        return redirect(url_for('pdv.index'))
    
    return render_template('pdv/finalize_order.html', order=order)

@pdv.route('/caixa')
@login_required
def cashier():
    today_date = datetime.utcnow().date()
    today_orders = Order.get_by_date_and_status(today_date, 'pago')
    
    total_cash = sum(o['total'] for o in today_orders if o['payment_method'] == 'dinheiro')
    total_card = sum(o['total'] for o in today_orders if o['payment_method'] in ['credito', 'debito'])
    total_pix = sum(o['total'] for o in today_orders if o['payment_method'] == 'pix')
    total_day = sum(o['total'] for o in today_orders)
    
    return render_template('pdv/cashier.html',
                         orders=today_orders,
                         total_cash=total_cash,
                         total_card=total_card,
                         total_pix=total_pix,
                         total_day=total_day)

@pdv.route('/cozinha')
@login_required
def kitchen():
    from datetime import datetime, timedelta
    
    pending_orders = Order.get_by_statuses(['pendente', 'preparando'])
    
    orders_with_items = []
    for order in pending_orders:
        items = OrderItem.get_by_order(order['id'])
        
        order_age_minutes = 0
        if order['created_at']:
            try:
                created_time = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S')
                order_age_minutes = (datetime.now() - created_time).total_seconds() / 60
            except:
                pass
        
        priority_class = 'success'
        if order_age_minutes > 30:
            priority_class = 'danger'
        elif order_age_minutes > 15:
            priority_class = 'warning'
        
        orders_with_items.append({
            'order': dict(order),
            'items': items,
            'age_minutes': int(order_age_minutes),
            'priority_class': priority_class
        })
    
    orders_with_items.sort(key=lambda x: x['age_minutes'], reverse=True)
    
    return render_template('pdv/kitchen.html', orders_with_items=orders_with_items)

@pdv.route('/kds')
@login_required
def kds():
    """Kitchen Display System - Interface moderna para cozinha"""
    from datetime import datetime
    
    # Pegar todos os pedidos ativos
    pending_orders = Order.get_by_statuses(['pendente', 'preparando', 'pronto'])
    
    # Organizar pedidos por status com detalhes dos items
    new_orders = []
    preparing_orders = []
    ready_orders = []
    
    for order in pending_orders:
        items = OrderItem.get_by_order(order['id'])
        
        # Calcular tempo de espera
        order_age_minutes = 0
        if order['created_at']:
            try:
                created_time = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S')
                order_age_minutes = (datetime.now() - created_time).total_seconds() / 60
            except:
                pass
        
        # Definir prioridade
        priority_class = 'low'
        if order_age_minutes > 30:
            priority_class = 'critical'
        elif order_age_minutes > 20:
            priority_class = 'high'
        elif order_age_minutes > 10:
            priority_class = 'medium'
        
        order_data = {
            'order': dict(order),
            'items': items,
            'age_minutes': int(order_age_minutes),
            'priority_class': priority_class
        }
        
        # Organizar por status
        if order['status'] == 'pendente':
            new_orders.append(order_data)
        elif order['status'] == 'preparando':
            preparing_orders.append(order_data)
        elif order['status'] == 'pronto':
            ready_orders.append(order_data)
    
    # Ordenar por tempo (mais antigos primeiro)
    new_orders.sort(key=lambda x: x['age_minutes'], reverse=True)
    preparing_orders.sort(key=lambda x: x['age_minutes'], reverse=True)
    ready_orders.sort(key=lambda x: x['age_minutes'], reverse=True)
    
    # Pegar todas as seções únicas dos produtos
    all_products = Product.get_all()
    sections = list(set([p.get('prep_section', 'geral') for p in all_products if p.get('prep_section')]))
    
    return render_template('pdv/kds.html', 
                         new_orders=new_orders,
                         preparing_orders=preparing_orders,
                         ready_orders=ready_orders,
                         sections=sections)

@pdv.route('/api/kds/orders')
@login_required
def kds_api():
    """API JSON para KDS - retorna pedidos ativos para polling"""
    from datetime import datetime
    
    # Parâmetro opcional para filtrar por timestamp
    since = request.args.get('since', None)
    
    # Pegar todos os pedidos ativos
    pending_orders = Order.get_by_statuses(['pendente', 'preparando', 'pronto'])
    
    result = {
        'new': [],
        'preparing': [],
        'ready': [],
        'timestamp': datetime.now().isoformat()
    }
    
    for order in pending_orders:
        # Verificar se o pedido foi modificado desde o timestamp fornecido
        if since:
            try:
                # Aqui você poderia adicionar lógica para verificar updated_at
                pass
            except:
                pass
        
        items = OrderItem.get_by_order(order['id'])
        
        # Calcular tempo de espera
        order_age_minutes = 0
        if order['created_at']:
            try:
                created_time = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S')
                order_age_minutes = (datetime.now() - created_time).total_seconds() / 60
            except:
                pass
        
        # Definir prioridade
        priority_class = 'low'
        if order_age_minutes > 30:
            priority_class = 'critical'
        elif order_age_minutes > 20:
            priority_class = 'high'
        elif order_age_minutes > 10:
            priority_class = 'medium'
        
        # Enriquecer items com informações do produto (prep_section)
        items_with_section = []
        for item in items:
            product = Product.get_by_id(item['product_id'])
            items_with_section.append({
                'id': item['id'],
                'product_name': item['product_name'],
                'quantity': item['quantity'],
                'status': item.get('status', 'novo'),
                'notes': item.get('notes', ''),
                'prep_section': product.get('prep_section', 'geral') if product else 'geral'
            })
        
        order_data = {
            'id': order['id'],
            'table_number': order.get('table_number', 'N/A'),
            'status': order['status'],
            'age_minutes': int(order_age_minutes),
            'priority_class': priority_class,
            'created_at': order['created_at'],
            'items': items_with_section
        }
        
        # Organizar por status
        if order['status'] == 'pendente':
            result['new'].append(order_data)
        elif order['status'] == 'preparando':
            result['preparing'].append(order_data)
        elif order['status'] == 'pronto':
            result['ready'].append(order_data)
    
    # Ordenar por tempo (mais antigos primeiro)
    for status_list in [result['new'], result['preparing'], result['ready']]:
        status_list.sort(key=lambda x: x['age_minutes'], reverse=True)
    
    return jsonify(result)

@pdv.route('/api/pedido/<int:order_id>/status', methods=['POST'])
@login_required
def update_status(order_id):
    order = Order.get_by_id(order_id)
    if not order:
        abort(404)
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    Order.update(order_id, status=data.get('status'))
    
    return jsonify({'success': True})

@pdv.route('/api/item/<int:item_id>/status', methods=['POST'])
@login_required
def update_item_status(item_id):
    item = OrderItem.get_by_id(item_id)
    if not item:
        abort(404)
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    new_status = data.get('status')
    
    OrderItem.update_status(item_id, new_status)
    
    return jsonify({'success': True})

@pdv.route('/api/pedido/<int:order_id>/sugestoes')
@login_required
def get_order_suggestions(order_id):
    suggestions = ProductSuggestion.get_suggestions_for_order(order_id)
    
    suggestions_list = []
    for suggestion in suggestions:
        suggestions_list.append({
            'id': suggestion['id'],
            'name': suggestion['name'],
            'price': suggestion['price'],
            'description': suggestion['description'],
            'image_url': suggestion['image_url'],
            'suggestion_type': suggestion['suggestion_type']
        })
    
    return jsonify({'suggestions': suggestions_list})

@pdv.route('/api/mesa/<int:table_id>/dividir-conta', methods=['POST'])
@login_required
def split_bill(table_id):
    table = Table.get_by_id(table_id)
    if not table or not table['current_order_id']:
        return jsonify({'success': False, 'error': 'Mesa não possui pedido ativo'}), 400
    
    order = Order.get_by_id(table['current_order_id'])
    if not order:
        return jsonify({'success': False, 'error': 'Pedido não encontrado'}), 404
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    split_type = data.get('split_type', 'equal')
    num_splits = int(data.get('num_splits', 2))
    
    items = OrderItem.get_by_order(order['id'])
    total = order['total']
    tip = order.get('tip_amount', 0) if order.get('tip_amount') else 0
    total_with_tip = total + tip
    
    if split_type == 'equal':
        amount_per_person = total_with_tip / num_splits
        splits = []
        for i in range(num_splits):
            split_id = PaymentSplit.create(order['id'], i + 1, round(amount_per_person, 2))
            splits.append({
                'split_id': split_id,
                'person': i + 1,
                'amount': round(amount_per_person, 2),
                'items': 'Divisão igual'
            })
        return jsonify({'success': True, 'splits': splits})
    
    return jsonify({'success': True, 'message': 'Funcionalidade em desenvolvimento'})

@pdv.route('/mapa-salao')
@login_required
def floor_map():
    tables = Table.get_all()
    active_groups = TableGrouping.get_active()
    
    tables_data = []
    for table in tables:
        table_dict = dict(table)
        if table['current_order_id']:
            order = Order.get_by_id(table['current_order_id'])
            table_dict['order'] = dict(order) if order else None
        else:
            table_dict['order'] = None
        tables_data.append(table_dict)
    
    return render_template('pdv/floor_map.html', tables=tables_data, groups=active_groups)

@pdv.route('/api/mesas/juntar', methods=['POST'])
@login_required
def merge_tables():
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    table_ids = data.get('table_ids', [])
    name = data.get('name', f'Mesas {",".join(map(str, table_ids))}')
    
    if len(table_ids) < 2:
        return jsonify({'success': False, 'error': 'Selecione pelo menos 2 mesas'}), 400
    
    main_table = Table.get_by_id(table_ids[0])
    merged_order_id = main_table['current_order_id']
    
    group_id = TableGrouping.create(name, table_ids, merged_order_id)
    
    for table_id in table_ids:
        TableMergeHistory.create(group_id, table_id, table_ids[0], 'merge', current_user.id)
    
    AuditLog.create('merge_tables', 'table_grouping', group_id, current_user.id, 
                   None, {'table_ids': table_ids, 'name': name})
    
    return jsonify({'success': True, 'group_id': group_id})

@pdv.route('/api/mesas/separar/<int:group_id>', methods=['POST'])
@login_required
def split_tables(group_id):
    from app.database import get_db_connection
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM table_grouping WHERE id = ? AND dissolved_at IS NULL', (group_id,))
        group = cursor.fetchone()
    
    if not group:
        return jsonify({'success': False, 'error': 'Grupo não encontrado'}), 404
    
    table_ids = [int(tid) for tid in group['table_ids'].split(',')]
    merged_order_id = group['merged_order_id']
    
    if table_ids:
        main_table_id = table_ids[0]
        Table.update(main_table_id, status='ocupada' if merged_order_id else 'livre')
        
        for table_id in table_ids[1:]:
            Table.update(table_id, status='livre', current_order_id=None)
    
    TableGrouping.dissolve(group_id)
    
    AuditLog.create('split_tables', 'table_grouping', group_id, current_user.id, 
                   {'table_ids': table_ids, 'order_preserved_on': table_ids[0] if table_ids else None})
    
    return jsonify({'success': True, 'main_table_id': table_ids[0] if table_ids else None})

@pdv.route('/api/mesas/<int:table_id>/abrir', methods=['POST'])
@login_required
def open_table(table_id):
    table = Table.get_by_id(table_id)
    if not table:
        return jsonify({'success': False, 'error': 'Mesa não encontrada'}), 404
    
    if table['status'] == 'ocupada':
        return jsonify({'success': False, 'error': 'Mesa já está ocupada'}), 400
    
    Table.update(table_id, status='ocupada')
    
    AuditLog.create('open_table', 'table', table_id, current_user.id,
                   {'status': table['status']}, {'status': 'ocupada'})
    
    return jsonify({'success': True, 'message': 'Mesa aberta com sucesso'})

@pdv.route('/api/mesas/<int:table_id>/fechar', methods=['POST'])
@login_required
def close_table(table_id):
    table = Table.get_by_id(table_id)
    if not table:
        return jsonify({'success': False, 'error': 'Mesa não encontrada'}), 404
    
    if table['status'] == 'livre':
        return jsonify({'success': False, 'error': 'Mesa já está livre'}), 400
    
    if table['current_order_id']:
        order = Order.get_by_id(table['current_order_id'])
        if order:
            payments = Payment.get_by_order(order['id'])
            paid_payments = [p for p in payments if p['status'] == 'pago']
            
            if not paid_payments or order['status'] != 'pago':
                return jsonify({
                    'success': False, 
                    'error': 'Mesa não pode ser fechada. O pagamento ainda não foi confirmado.'
                }), 400
    
    Table.update(table_id, status='livre', current_order_id=None)
    
    AuditLog.create('close_table', 'table', table_id, current_user.id,
                   {'status': table['status'], 'current_order_id': table['current_order_id']}, 
                   {'status': 'livre', 'current_order_id': None})
    
    return jsonify({'success': True, 'message': 'Mesa fechada com sucesso'})

@pdv.route('/api/pedido/<int:order_id>/transferir', methods=['POST'])
@login_required
def transfer_order(order_id):
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    to_user_id = data.get('to_user_id')
    reason = data.get('reason')
    
    order = Order.get_by_id(order_id)
    if not order:
        return jsonify({'success': False, 'error': 'Pedido não encontrado'}), 404
    
    OrderTransfer.create(order_id, current_user.id, to_user_id, reason)
    Order.update(order_id, user_id=to_user_id)
    
    AuditLog.create('transfer_order', 'order', order_id, current_user.id,
                   {'user_id': order['user_id']}, {'user_id': to_user_id})
    
    return jsonify({'success': True})

@pdv.route('/api/mensagem/enviar', methods=['POST'])
@login_required
def send_message():
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    to_role = data.get('to_role', 'cozinha')
    message = data.get('message')
    order_id = data.get('order_id')
    table_id = data.get('table_id')
    priority = data.get('priority', 'normal')
    
    message_id = ServiceMessage.create(
        from_user_id=current_user.id,
        to_role=to_role,
        message=message,
        order_id=order_id,
        table_id=table_id,
        priority=priority
    )
    
    return jsonify({'success': True, 'message_id': message_id})

@pdv.route('/api/mensagens/nao-lidas')
@login_required
def get_unread_messages():
    messages = ServiceMessage.get_unread_by_role(current_user.role, current_user.id)
    return jsonify({'messages': [dict(m) for m in messages]})

@pdv.route('/api/mensagem/<int:message_id>/marcar-lida', methods=['POST'])
@login_required
def mark_message_read(message_id):
    ServiceMessage.mark_as_read(message_id, current_user.id)
    return jsonify({'success': True})

@pdv.route('/api/pedido/<int:order_id>/duplicar', methods=['POST'])
@login_required
def duplicate_order(order_id):
    original_order = Order.get_by_id(order_id)
    if not original_order:
        return jsonify({'success': False, 'error': 'Pedido não encontrado'}), 404
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    table_id = data.get('table_id', original_order['table_id'])
    
    new_order_id = Order.create(
        table_id=table_id,
        user_id=current_user.id,
        status='pendente',
        total=0.0
    )
    
    items = OrderItem.get_by_order(order_id)
    total = 0
    for item in items:
        OrderItem.create(
            order_id=new_order_id,
            product_id=item['product_id'],
            quantity=item['quantity'],
            price=item['price'],
            notes=item.get('notes', '')
        )
        total += item['price'] * item['quantity']
        
        modifiers = OrderItemModifier.get_by_order_item(item['id'])
        for mod in modifiers:
            OrderItemModifier.create(new_order_id, mod['modifier_option_id'], mod['price_adjustment'])
    
    Order.update(new_order_id, total=total)
    
    if table_id:
        Table.update(table_id, status='ocupada', current_order_id=new_order_id)
    
    return jsonify({'success': True, 'order_id': new_order_id})

@pdv.route('/api/pedido/<int:order_id>/gorjeta', methods=['POST'])
@login_required
def add_tip(order_id):
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    tip_type = data.get('type', 'manual')
    
    order = Order.get_by_id(order_id)
    if not order:
        return jsonify({'success': False, 'error': 'Pedido não encontrado'}), 404
    
    if tip_type == 'automatic':
        policy = ServiceChargePolicy.get_automatic()
        if policy:
            tip_amount = order['total'] * (policy['percentage'] / 100)
            tip_percentage = policy['percentage']
            OrderServiceCharge.create(order_id, tip_amount, tip_percentage, policy['id'], 'automatic')
        else:
            tip_amount = order['total'] * 0.10
            tip_percentage = 10
            OrderServiceCharge.create(order_id, tip_amount, tip_percentage, None, 'automatic')
    else:
        tip_amount = float(data.get('amount', 0))
        tip_percentage = (tip_amount / order['total'] * 100) if order['total'] > 0 else 0
        OrderServiceCharge.create(order_id, tip_amount, tip_percentage, None, 'manual')
    
    Order.update(order_id, tip_amount=tip_amount, tip_percentage=tip_percentage)
    
    return jsonify({'success': True, 'tip_amount': tip_amount})

@pdv.route('/api/produto/<int:product_id>/modificadores')
@login_required
def get_product_modifiers(product_id):
    groups = ProductModifierGroup.get_by_product(product_id)
    
    modifiers_data = []
    for group in groups:
        options = ProductModifierOption.get_by_group(group['id'])
        modifiers_data.append({
            'group': dict(group),
            'options': [dict(opt) for opt in options]
        })
    
    return jsonify({'modifiers': modifiers_data})

@pdv.route('/delivery/pedidos')
@login_required
def delivery_orders():
    pending = DeliveryOrder.get_by_status('pending')
    in_progress = DeliveryOrder.get_by_status('picked_up')
    
    return render_template('pdv/delivery_orders.html', 
                         pending=pending,
                         in_progress=in_progress)
