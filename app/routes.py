from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from app.db_operations import Product, Category, Order, OrderItem, Table, Customer, Settings
from app.geo_utils import get_coordinates_from_zipcode, is_within_delivery_radius

main = Blueprint('main', __name__)

@main.route('/')
def index():
    categories = Category.get_all()
    featured_products = Product.get_featured(4)
    return render_template('index.html', categories=categories, products=featured_products)

@main.route('/cardapio')
def menu():
    categories = Category.get_all()
    products = Product.get_all(available_only=True)
    return render_template('menu.html', categories=categories, products=products)

@main.route('/produto/<int:id>')
def product_detail(id):
    product = Product.get_by_id(id)
    if not product:
        abort(404)
    
    related = []
    if product['category_id']:
        all_related = Product.get_by_category(product['category_id'], available_only=True)
        related = [p for p in all_related if p['id'] != id][:3]
    
    return render_template('product_detail.html', product=product, related=related)

@main.route('/carrinho')
def cart():
    cart_items = session.get('cart', {})
    items = []
    total = 0
    
    for product_id, quantity in cart_items.items():
        product = Product.get_by_id(int(product_id))
        if product:
            subtotal = product['price'] * quantity
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
    
    return render_template('cart.html', items=items, total=total)

@main.route('/carrinho/adicionar/<int:product_id>', methods=['POST'])
def add_product_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    
    cart = session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        cart[product_id_str] += quantity
    else:
        cart[product_id_str] = quantity
    
    session['cart'] = cart
    flash('Produto adicionado ao carrinho!', 'success')
    return redirect(request.referrer or url_for('main.index'))

@main.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    product_id = str(data.get('product_id'))
    quantity = int(data.get('quantity', 1))
    
    cart = session.get('cart', {})
    
    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity
    
    session['cart'] = cart
    return jsonify({'success': True, 'cart_count': sum(cart.values())})

@main.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    product_id = str(data.get('product_id'))
    
    cart = session.get('cart', {})
    if product_id in cart:
        del cart[product_id]
    
    session['cart'] = cart
    return jsonify({'success': True})

@main.route('/api/cart/update', methods=['POST'])
def update_cart():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    product_id = str(data.get('product_id'))
    quantity = int(data.get('quantity', 1))
    
    cart = session.get('cart', {})
    
    if quantity > 0:
        cart[product_id] = quantity
    else:
        if product_id in cart:
            del cart[product_id]
    
    session['cart'] = cart
    return jsonify({'success': True})

@main.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('main.cart'))
    
    if not session.get('customer_id'):
        flash('Por favor, faça login para finalizar seu pedido', 'warning')
        return redirect(url_for('auth.customer_login', next=request.url))
    
    settings = Settings.get()
    settings_dict = dict(settings) if settings else {}
    delivery_enabled = settings_dict.get('enable_delivery', 1)
    delivery_fee = settings_dict.get('delivery_fee', 5.0) or 5.0
    
    if request.method == 'POST':
        order_type = request.form.get('order_type', 'retirada')
        payment_method = request.form.get('payment_method')
        notes = request.form.get('notes', '')
        customer_id = session.get('customer_id')
        
        total = 0
        for product_id, quantity in cart.items():
            product = Product.get_by_id(int(product_id))
            if product:
                total += product['price'] * quantity
        
        table_id = None
        delivery_address = None
        final_total = total
        
        if order_type == 'retirada':
            table_number = request.form.get('table_number')
            if table_number:
                try:
                    table_number = int(table_number)
                    table = Table.get_by_number(table_number)
                    if not table:
                        table_id = Table.create(number=table_number, capacity=4)
                    else:
                        table_id = table['id']
                except (ValueError, TypeError):
                    pass
        
        elif order_type == 'entrega':
            if not delivery_enabled:
                flash('Entregas não estão disponíveis no momento', 'danger')
                return redirect(url_for('main.checkout'))
            
            zipcode = request.form.get('zipcode', '').strip()
            address = request.form.get('address', '').strip()
            
            if not zipcode or not address:
                flash('Por favor, preencha CEP e endereço completo para entrega', 'danger')
                return redirect(url_for('main.checkout'))
            
            geo_data = get_coordinates_from_zipcode(zipcode)
            
            if not geo_data:
                flash('CEP inválido ou não encontrado', 'danger')
                return redirect(url_for('main.checkout'))
            
            if settings_dict.get('store_latitude') and settings_dict.get('store_longitude'):
                delivery_radius = settings_dict.get('delivery_radius_km', 5.0)
                within_radius, distance = is_within_delivery_radius(
                    geo_data['lat'], 
                    geo_data['lng'],
                    settings_dict['store_latitude'],
                    settings_dict['store_longitude'],
                    delivery_radius
                )
                
                if not within_radius:
                    flash(f'Desculpe, não entregamos nesta região. Você está a {distance:.1f}km da loja (máximo: {delivery_radius}km)', 'danger')
                    return redirect(url_for('main.checkout'))
            
            Customer.update(customer_id, 
                          zipcode=zipcode,
                          address=address,
                          city=geo_data.get('city'),
                          state=geo_data.get('state'),
                          latitude=geo_data.get('lat'),
                          longitude=geo_data.get('lng'))
            
            delivery_address = address
            final_total = total + delivery_fee
        
        order_id = Order.create(
            table_id=table_id,
            user_id=None,
            customer_id=customer_id,
            payment_method=payment_method,
            notes=notes,
            order_type=order_type,
            delivery_address=delivery_address,
            delivery_fee=delivery_fee if order_type == 'entrega' else 0,
            total=final_total,
            status='pendente'
        )
        
        for product_id, quantity in cart.items():
            product = Product.get_by_id(int(product_id))
            if product:
                OrderItem.create(
                    order_id=order_id,
                    product_id=product['id'],
                    quantity=quantity,
                    price=product['price']
                )
        
        if table_id:
            Table.update(table_id, current_order_id=order_id, status='ocupada')
        
        session['cart'] = {}
        
        return redirect(url_for('main.order_success', order_id=order_id))
    
    items = []
    total = 0
    for product_id, quantity in cart.items():
        product = Product.get_by_id(int(product_id))
        if product:
            subtotal = product['price'] * quantity
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
    
    customer = Customer.get_by_id(session.get('customer_id'))
    
    return render_template('checkout.html', 
                         items=items, 
                         total=total,
                         delivery_enabled=delivery_enabled,
                         delivery_fee=delivery_fee,
                         customer=customer)

@main.route('/pedido/<int:order_id>/sucesso')
def order_success(order_id):
    order = Order.get_by_id(order_id)
    if not order:
        abort(404)
    return render_template('order_success.html', order=order)

@main.route('/pedido/<int:order_id>/acompanhar')
def track_order(order_id):
    """Página de acompanhamento do pedido em tempo real para clientes"""
    from datetime import datetime
    
    order = Order.get_by_id(order_id)
    if not order:
        abort(404)
    
    items = OrderItem.get_by_order(order_id)
    
    # Calcular tempo desde o pedido
    order_age_minutes = 0
    if order['created_at']:
        try:
            created_time = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S')
            order_age_minutes = int((datetime.now() - created_time).total_seconds() / 60)
        except:
            pass
    
    # Calcular progresso do pedido (0-100%)
    total_items = len(items)
    items_done = sum(1 for item in items if item['status'] in ['pronto', 'entregue'])
    progress = int((items_done / total_items * 100)) if total_items > 0 else 0
    
    # Definir status amigável e tempo estimado
    status_friendly = {
        'pendente': 'Pedido Recebido',
        'preparando': 'Em Preparação',
        'pronto': 'Pronto para Retirada/Entrega',
        'entregue': 'Entregue',
        'finalizado': 'Finalizado',
        'cancelado': 'Cancelado'
    }
    
    estimated_time = ''
    if order['status'] == 'pendente':
        estimated_time = '10-15 minutos'
    elif order['status'] == 'preparando':
        estimated_time = '5-10 minutos'
    elif order['status'] == 'pronto':
        estimated_time = 'Disponível agora'
    
    return render_template('track_order.html',
                         order=order,
                         items=items,
                         order_age_minutes=order_age_minutes,
                         progress=progress,
                         status_friendly=status_friendly.get(order['status'], order['status']),
                         estimated_time=estimated_time)

@main.route('/api/pedido/<int:order_id>/status')
def order_status_api(order_id):
    """API JSON para acompanhamento do pedido - usado para polling"""
    from datetime import datetime
    
    order = Order.get_by_id(order_id)
    if not order:
        return jsonify({'error': 'Pedido não encontrado'}), 404
    
    items = OrderItem.get_by_order(order_id)
    
    # Calcular tempo desde o pedido
    order_age_minutes = 0
    if order['created_at']:
        try:
            created_time = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S')
            order_age_minutes = int((datetime.now() - created_time).total_seconds() / 60)
        except:
            pass
    
    # Calcular progresso do pedido (0-100%)
    total_items = len(items)
    items_done = sum(1 for item in items if item['status'] in ['pronto', 'entregue'])
    progress = int((items_done / total_items * 100)) if total_items > 0 else 0
    
    # Definir status amigável e tempo estimado
    status_friendly_map = {
        'pendente': 'Pedido Recebido',
        'preparando': 'Em Preparação',
        'pronto': 'Pronto para Retirada/Entrega',
        'entregue': 'Entregue',
        'finalizado': 'Finalizado',
        'cancelado': 'Cancelado'
    }
    
    estimated_time = ''
    if order['status'] == 'pendente':
        estimated_time = '10-15 minutos'
    elif order['status'] == 'preparando':
        estimated_time = '5-10 minutos'
    elif order['status'] == 'pronto':
        estimated_time = 'Disponível agora'
    
    return jsonify({
        'order_id': order_id,
        'status': order['status'],
        'status_friendly': status_friendly_map.get(order['status'], order['status']),
        'progress': progress,
        'estimated_time': estimated_time,
        'order_age_minutes': order_age_minutes,
        'total_items': total_items,
        'items_done': items_done,
        'timestamp': datetime.now().isoformat()
    })

@main.route('/api/cart/count')
def cart_count():
    cart = session.get('cart', {})
    return jsonify({'count': sum(cart.values())})

@main.route('/mesas')
@login_required
def tables():
    all_tables = Table.get_all()
    return render_template('tables.html', tables=all_tables)
