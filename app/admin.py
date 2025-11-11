from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.db_operations import Product, Category, Order, Table, User, OrderItem, Settings, Inventory, Customer, ProductSuggestion
from app.db_operations_extended import (ProductModifierGroup, ProductModifierOption, ServiceChargePolicy, 
                                        DeliveryDriver, Reservation, WaitlistEntry, CashOperation, 
                                        CashierSession, AuditLog)
from functools import wraps
from datetime import datetime, timedelta

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acesso negado. Apenas administradores.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@login_required
@admin_required
def dashboard():
    # Estatísticas gerais
    total_orders = Order.count()
    total_products = Product.count()
    total_revenue = Order.get_total_revenue_by_status('pago')
    pending_orders = Order.count_by_status('pendente')
    
    # Estatísticas da cozinha
    preparing_orders = Order.count_by_status('preparando')
    ready_orders = Order.count_by_status('pronto')
    delivered_orders = Order.count_by_status('entregue')
    
    # Pedidos recentes
    recent_orders = Order.get_recent(10)
    
    # Pedidos ativos com detalhes
    active_orders = Order.get_by_statuses(['pendente', 'preparando', 'pronto'])
    kitchen_orders = []
    total_items_pending = 0
    total_items_preparing = 0
    total_items_ready = 0
    
    for order in active_orders:
        items = OrderItem.get_by_order(order['id'])
        
        # Calcular tempo de espera
        order_age_minutes = 0
        if order['created_at']:
            try:
                created_time = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S')
                order_age_minutes = (datetime.now() - created_time).total_seconds() / 60
            except:
                pass
        
        # Contar items por status
        for item in items:
            if item['status'] == 'novo':
                total_items_pending += 1
            elif item['status'] == 'preparando':
                total_items_preparing += 1
            elif item['status'] == 'pronto':
                total_items_ready += 1
        
        kitchen_orders.append({
            'order': dict(order),
            'items': items,
            'age_minutes': int(order_age_minutes)
        })
    
    # Ordenar por tempo (mais antigos primeiro)
    kitchen_orders.sort(key=lambda x: x['age_minutes'], reverse=True)
    
    return render_template('admin/dashboard.html', 
                         total_orders=total_orders,
                         total_products=total_products,
                         total_revenue=total_revenue,
                         pending_orders=pending_orders,
                         preparing_orders=preparing_orders,
                         ready_orders=ready_orders,
                         delivered_orders=delivered_orders,
                         recent_orders=recent_orders,
                         kitchen_orders=kitchen_orders,
                         total_items_pending=total_items_pending,
                         total_items_preparing=total_items_preparing,
                         total_items_ready=total_items_ready)

@admin.route('/api/metrics')
@login_required
@admin_required
def api_metrics():
    """Endpoint JSON para métricas em tempo real do dashboard"""
    # Estatísticas gerais
    total_orders = Order.count()
    total_revenue = Order.get_total_revenue_by_status('pago')
    pending_orders = Order.count_by_status('pendente')
    
    # Estatísticas da cozinha
    preparing_orders = Order.count_by_status('preparando')
    ready_orders = Order.count_by_status('pronto')
    delivered_orders = Order.count_by_status('entregue')
    
    # Pedidos ativos
    active_orders = Order.get_by_statuses(['pendente', 'preparando', 'pronto'])
    total_items_pending = 0
    total_items_preparing = 0
    total_items_ready = 0
    
    kitchen_orders_data = []
    for order in active_orders:
        items = OrderItem.get_by_order(order['id'])
        
        # Calcular tempo de espera
        order_age_minutes = 0
        if order['created_at']:
            try:
                created_time = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S')
                order_age_minutes = (datetime.now() - created_time).total_seconds() / 60
            except:
                pass
        
        # Contar items por status
        for item in items:
            if item['status'] == 'novo':
                total_items_pending += 1
            elif item['status'] == 'preparando':
                total_items_preparing += 1
            elif item['status'] == 'pronto':
                total_items_ready += 1
        
        kitchen_orders_data.append({
            'id': order['id'],
            'table_number': order.get('table_number', 'N/A'),
            'status': order['status'],
            'age_minutes': int(order_age_minutes),
            'items_count': len(items)
        })
    
    return jsonify({
        'total_orders': total_orders,
        'total_revenue': float(total_revenue) if total_revenue else 0,
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'delivered_orders': delivered_orders,
        'total_items_pending': total_items_pending,
        'total_items_preparing': total_items_preparing,
        'total_items_ready': total_items_ready,
        'kitchen_orders': kitchen_orders_data,
        'timestamp': datetime.now().isoformat()
    })

@admin.route('/produtos')
@login_required
@admin_required
def products():
    products = Product.get_all()
    categories = Category.get_all()
    return render_template('admin/products.html', products=products, categories=categories)

@admin.route('/produto/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price_str = request.form.get('price')
        category_id = request.form.get('category_id')
        image_url = request.form.get('image_url', '')
        
        if not name or not price_str:
            flash('Nome e preço são obrigatórios', 'danger')
            categories = Category.get_all()
            return render_template('admin/add_product.html', categories=categories)
        
        try:
            price = float(price_str)
            if price < 0:
                flash('Preço não pode ser negativo', 'danger')
                categories = Category.get_all()
                return render_template('admin/add_product.html', categories=categories)
        except ValueError:
            flash('Preço inválido', 'danger')
            categories = Category.get_all()
            return render_template('admin/add_product.html', categories=categories)
        
        Product.create(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            image_url=image_url
        )
        
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('admin.products'))
    
    categories = Category.get_all()
    return render_template('admin/add_product.html', categories=categories)

@admin.route('/produto/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.get_by_id(id)
    if not product:
        abort(404)
    
    if request.method == 'POST':
        price_str = request.form.get('price')
        
        if not price_str:
            flash('Preço é obrigatório', 'danger')
            categories = Category.get_all()
            return render_template('admin/edit_product.html', product=product, categories=categories)
        
        try:
            price = float(price_str)
            if price < 0:
                flash('Preço não pode ser negativo', 'danger')
                categories = Category.get_all()
                return render_template('admin/edit_product.html', product=product, categories=categories)
        except ValueError:
            flash('Preço inválido', 'danger')
            categories = Category.get_all()
            return render_template('admin/edit_product.html', product=product, categories=categories)
        
        Product.update(
            id,
            name=request.form.get('name'),
            description=request.form.get('description'),
            price=price,
            category_id=request.form.get('category_id'),
            image_url=request.form.get('image_url', ''),
            available=request.form.get('available') == 'on'
        )
        
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin.products'))
    
    categories = Category.get_all()
    return render_template('admin/edit_product.html', product=product, categories=categories)

@admin.route('/produto/<int:id>/deletar', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    product = Product.get_by_id(id)
    if not product:
        abort(404)
    
    Product.delete(id)
    
    flash('Produto deletado com sucesso!', 'success')
    return redirect(url_for('admin.products'))

@admin.route('/categorias')
@login_required
@admin_required
def categories():
    categories = Category.get_all()
    return render_template('admin/categories.html', categories=categories)

@admin.route('/categoria/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        image_url = request.form.get('image_url', '')
        
        Category.create(name=name, description=description, image_url=image_url)
        
        flash('Categoria adicionada com sucesso!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/add_category.html')

@admin.route('/pedidos')
@login_required
@admin_required
def orders():
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        orders = Order.get_all()
    else:
        orders = Order.get_by_status(status_filter)
    
    return render_template('admin/orders.html', orders=orders, status_filter=status_filter)

@admin.route('/pedido/<int:id>')
@login_required
@admin_required
def order_detail(id):
    order = Order.get_by_id(id)
    if not order:
        abort(404)
    return render_template('admin/order_detail.html', order=order)

@admin.route('/pedido/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def update_order_status(id):
    order = Order.get_by_id(id)
    if not order:
        abort(404)
    
    new_status = request.form.get('status')
    
    Order.update(id, status=new_status)
    
    if new_status == 'finalizado' or new_status == 'cancelado':
        if order['table_id']:
            Table.update(order['table_id'], status='livre', current_order_id=None)
    
    flash('Status do pedido atualizado!', 'success')
    return redirect(url_for('admin.order_detail', id=id))

@admin.route('/mesas')
@login_required
@admin_required
def tables():
    tables = Table.get_all()
    return render_template('admin/tables.html', tables=tables)

@admin.route('/mesa/adicionar', methods=['POST'])
@login_required
@admin_required
def add_table():
    number_str = request.form.get('number')
    capacity_str = request.form.get('capacity')
    
    if not number_str:
        flash('Número da mesa é obrigatório', 'danger')
        return redirect(url_for('admin.tables'))
    
    try:
        number = int(number_str)
        capacity = int(capacity_str) if capacity_str else 4
        
        if number <= 0:
            flash('Número da mesa deve ser maior que zero', 'danger')
            return redirect(url_for('admin.tables'))
        
        if capacity <= 0:
            flash('Capacidade deve ser maior que zero', 'danger')
            return redirect(url_for('admin.tables'))
    except ValueError:
        flash('Valores inválidos para número ou capacidade', 'danger')
        return redirect(url_for('admin.tables'))
    
    if Table.get_by_number(number):
        flash('Mesa com este número já existe!', 'danger')
    else:
        Table.create(number=number, capacity=capacity)
        flash('Mesa adicionada com sucesso!', 'success')
    
    return redirect(url_for('admin.tables'))

@admin.route('/usuarios')
@login_required
@admin_required
def users():
    users = User.get_all()
    return render_template('admin/users.html', users=users)

@admin.route('/configuracoes', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    settings = Settings.get()
    
    if not settings:
        Settings.create()
        settings = Settings.get()
    
    if request.method == 'POST':
        from app.geo_utils import get_coordinates_from_zipcode
        
        store_zipcode = request.form.get('store_zipcode', '').strip()
        store_latitude = None
        store_longitude = None
        store_city = None
        store_state = None
        
        if store_zipcode:
            geo_data = get_coordinates_from_zipcode(store_zipcode)
            if geo_data:
                store_latitude = geo_data.get('lat')
                store_longitude = geo_data.get('lng')
                store_city = geo_data.get('city')
                store_state = geo_data.get('state')
            else:
                flash('CEP inválido ou não encontrado!', 'warning')
        
        try:
            delivery_fee_str = request.form.get('delivery_fee', '').strip()
            delivery_fee = float(delivery_fee_str) if delivery_fee_str else 5.0
            if delivery_fee < 0:
                delivery_fee = 5.0
        except (ValueError, TypeError):
            delivery_fee = 5.0
            flash('Taxa de entrega inválida, usando valor padrão R$ 5,00', 'warning')
        
        try:
            delivery_radius_str = request.form.get('delivery_radius_km', '').strip()
            delivery_radius_km = float(delivery_radius_str) if delivery_radius_str else 5.0
            if delivery_radius_km <= 0:
                delivery_radius_km = 5.0
        except (ValueError, TypeError):
            delivery_radius_km = 5.0
            flash('Raio de entrega inválido, usando valor padrão 5km', 'warning')
        
        Settings.update(
            store_name=request.form.get('store_name', 'MEATZ'),
            logo_url=request.form.get('logo_url', ''),
            phone=request.form.get('phone', ''),
            email=request.form.get('email', ''),
            address=request.form.get('address', ''),
            opening_hours=request.form.get('opening_hours', ''),
            whatsapp=request.form.get('whatsapp', ''),
            instagram=request.form.get('instagram', ''),
            facebook=request.form.get('facebook', ''),
            store_zipcode=store_zipcode,
            store_latitude=store_latitude,
            store_longitude=store_longitude,
            store_city=store_city,
            store_state=store_state,
            enable_delivery=1 if request.form.get('enable_delivery') else 0,
            delivery_fee=delivery_fee,
            delivery_radius_km=delivery_radius_km
        )
        
        flash('Configurações atualizadas com sucesso!', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', settings=settings)

@admin.route('/estoque')
@login_required
@admin_required
def inventory():
    all_inventory = Inventory.get_all()
    low_stock = Inventory.get_low_stock()
    return render_template('admin/inventory.html', inventory=all_inventory, low_stock=low_stock)

@admin.route('/relatorios')
@login_required
@admin_required
def reports():
    period = request.args.get('period', 'today')
    
    if period == 'today':
        start_date = datetime.now().date()
        orders = Order.get_by_date_and_status(start_date, 'pago')
    elif period == 'week':
        start_date = datetime.now().date() - timedelta(days=7)
        orders = []
        for i in range(8):
            date = start_date + timedelta(days=i)
            orders.extend(Order.get_by_date_and_status(date, 'pago'))
    elif period == 'month':
        start_date = datetime.now().date() - timedelta(days=30)
        orders = []
        for i in range(31):
            date = start_date + timedelta(days=i)
            orders.extend(Order.get_by_date_and_status(date, 'pago'))
    else:
        orders = []
    
    total_revenue = sum(o['total'] for o in orders)
    total_orders = len(orders)
    average_order = total_revenue / total_orders if total_orders > 0 else 0
    
    product_stats = {}
    for order in orders:
        items = OrderItem.get_by_order(order['id'])
        for item in items:
            product_name = item['product_name']
            if product_name not in product_stats:
                product_stats[product_name] = {'quantity': 0, 'revenue': 0}
            product_stats[product_name]['quantity'] += item['quantity']
            product_stats[product_name]['revenue'] += item['price'] * item['quantity']
    
    top_products = sorted(product_stats.items(), key=lambda x: x[1]['revenue'], reverse=True)[:10]
    
    return render_template('admin/reports.html', 
                         period=period,
                         total_revenue=total_revenue,
                         total_orders=total_orders,
                         average_order=average_order,
                         top_products=top_products)

@admin.route('/fidelidade')
@login_required
@admin_required
def loyalty():
    return render_template('admin/loyalty.html')

@admin.route('/sugestoes')
@login_required
@admin_required
def suggestions():
    all_products = Product.get_all()
    return render_template('admin/suggestions.html', products=all_products)

@admin.route('/api/sugestao/adicionar', methods=['POST'])
@login_required
@admin_required
def add_suggestion():
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    product_id = data.get('product_id')
    suggested_product_id = data.get('suggested_product_id')
    suggestion_type = data.get('suggestion_type', 'upsell')
    
    if product_id == suggested_product_id:
        return jsonify({'success': False, 'error': 'Produto não pode sugerir a si mesmo'}), 400
    
    ProductSuggestion.create(product_id, suggested_product_id, suggestion_type, priority=1)
    
    return jsonify({'success': True})

@admin.route('/modificadores')
@login_required
@admin_required
def modifiers():
    all_groups = ProductModifierGroup.get_all()
    all_products = Product.get_all()
    
    groups_with_options = []
    for group in all_groups:
        options = ProductModifierOption.get_by_group(group['id'])
        product = Product.get_by_id(group['product_id']) if group['product_id'] else None
        groups_with_options.append({
            'group': dict(group),
            'options': options,
            'product': product
        })
    
    return render_template('admin/modifiers.html', groups=groups_with_options, products=all_products)

@admin.route('/modificador/grupo/adicionar', methods=['POST'])
@login_required
@admin_required
def add_modifier_group():
    name = request.form.get('name')
    product_id = request.form.get('product_id')
    min_selection = int(request.form.get('min_selection', 0))
    max_selection = int(request.form.get('max_selection', 1))
    required = request.form.get('required') == 'on'
    
    ProductModifierGroup.create(
        name=name,
        product_id=product_id if product_id else None,
        min_selection=min_selection,
        max_selection=max_selection,
        required=required
    )
    
    flash('Grupo de modificadores criado com sucesso!', 'success')
    return redirect(url_for('admin.modifiers'))

@admin.route('/modificador/opcao/adicionar', methods=['POST'])
@login_required
@admin_required
def add_modifier_option():
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    group_id = data.get('group_id')
    name = data.get('name')
    price_str = data.get('price_adjustment', '0')
    price_adjustment = float(price_str) if price_str else 0.0
    
    option_id = ProductModifierOption.create(
        modifier_group_id=group_id,
        name=name,
        price_adjustment=price_adjustment
    )
    
    return jsonify({'success': True, 'option_id': option_id})

@admin.route('/gorjetas')
@login_required
@admin_required
def tips():
    policies = ServiceChargePolicy.get_active()
    return render_template('admin/tips.html', policies=policies)

@admin.route('/gorjeta/politica/adicionar', methods=['POST'])
@login_required
@admin_required
def add_tip_policy():
    name = request.form.get('name')
    percentage = float(request.form.get('percentage', 10))
    is_automatic = request.form.get('is_automatic') == 'on'
    
    ServiceChargePolicy.create(name=name, percentage=percentage, is_automatic=is_automatic)
    
    flash('Política de gorjeta criada com sucesso!', 'success')
    return redirect(url_for('admin.tips'))

@admin.route('/delivery')
@login_required
@admin_required
def delivery():
    drivers = DeliveryDriver.get_all_active()
    return render_template('admin/delivery.html', drivers=drivers)

@admin.route('/entregador/adicionar', methods=['POST'])
@login_required
@admin_required
def add_driver():
    name = request.form.get('name')
    phone = request.form.get('phone')
    vehicle_type = request.form.get('vehicle_type')
    license_plate = request.form.get('license_plate')
    
    DeliveryDriver.create(name=name, phone=phone, vehicle_type=vehicle_type, license_plate=license_plate)
    
    flash('Entregador cadastrado com sucesso!', 'success')
    return redirect(url_for('admin.delivery'))

@admin.route('/reservas')
@login_required
@admin_required
def reservations():
    today = datetime.now().date()
    reservations = Reservation.get_by_date(today)
    waitlist = WaitlistEntry.get_waiting()
    all_tables = Table.get_all()
    
    return render_template('admin/reservations.html', 
                         reservations=reservations, 
                         waitlist=waitlist,
                         tables=all_tables,
                         today=today)

@admin.route('/reserva/criar', methods=['POST'])
@login_required
@admin_required
def create_reservation():
    customer_name = request.form.get('customer_name')
    customer_phone = request.form.get('customer_phone')
    customer_email = request.form.get('customer_email')
    party_size_str = request.form.get('party_size')
    reservation_date = request.form.get('reservation_date')
    reservation_time = request.form.get('reservation_time')
    table_id = request.form.get('table_id')
    notes = request.form.get('notes')
    
    if not customer_name or not customer_phone or not party_size_str:
        flash('Nome, telefone e tamanho do grupo são obrigatórios', 'danger')
        return redirect(url_for('admin.reservations'))
    
    try:
        party_size = int(party_size_str)
        if party_size <= 0:
            flash('Tamanho do grupo deve ser maior que zero', 'danger')
            return redirect(url_for('admin.reservations'))
    except ValueError:
        flash('Tamanho do grupo inválido', 'danger')
        return redirect(url_for('admin.reservations'))
    
    Reservation.create(
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        party_size=party_size,
        reservation_date=reservation_date,
        reservation_time=reservation_time,
        table_id=table_id if table_id else None,
        notes=notes
    )
    
    flash('Reserva criada com sucesso!', 'success')
    return redirect(url_for('admin.reservations'))

@admin.route('/reserva/<int:id>/confirmar', methods=['POST'])
@login_required
@admin_required
def confirm_reservation(id):
    Reservation.confirm(id)
    flash('Reserva confirmada!', 'success')
    return redirect(url_for('admin.reservations'))

@admin.route('/caixa/operacoes')
@login_required
@admin_required
def cash_operations():
    today = datetime.now().date()
    operations = CashOperation.get_by_date(today)
    
    total_sangria = sum(op['amount'] for op in operations if op['type'] == 'sangria')
    total_suprimento = sum(op['amount'] for op in operations if op['type'] == 'suprimento')
    
    return render_template('admin/cash_operations.html', 
                         operations=operations,
                         total_sangria=total_sangria,
                         total_suprimento=total_suprimento,
                         today=today)

@admin.route('/caixa/operacao/adicionar', methods=['POST'])
@login_required
@admin_required
def add_cash_operation():
    type = request.form.get('type')
    amount_str = request.form.get('amount')
    reason = request.form.get('reason')
    
    if not amount_str:
        flash('Valor é obrigatório', 'danger')
        return redirect(url_for('admin.cash_operations'))
    
    try:
        amount = float(amount_str)
        if amount <= 0:
            flash('Valor deve ser maior que zero', 'danger')
            return redirect(url_for('admin.cash_operations'))
    except ValueError:
        flash('Valor inválido', 'danger')
        return redirect(url_for('admin.cash_operations'))
    
    CashOperation.create(type=type, amount=amount, reason=reason, performed_by=current_user.id)
    
    flash(f'{"Sangria" if type == "sangria" else "Suprimento"} registrado com sucesso!', 'success')
    return redirect(url_for('admin.cash_operations'))

@admin.route('/auditoria')
@login_required
@admin_required
def audit():
    logs = AuditLog.get_recent(100)
    return render_template('admin/audit.html', logs=logs)
