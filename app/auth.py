from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.db_operations import User, Customer
from app import UserSession

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember', False))
        
        user_row = User.get_by_username(username)
        
        if user_row and User.check_password(user_row, password):
            user_session = UserSession(user_row)
            login_user(user_session, remember=remember)
            next_page = request.args.get('next')
            
            if user_row['role'] == 'admin':
                return redirect(next_page if next_page else url_for('admin.dashboard'))
            else:
                return redirect(next_page if next_page else url_for('pdv.index'))
        else:
            flash('Usuário ou senha inválidos', 'danger')
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone', '')
        
        if User.get_by_username(username):
            flash('Nome de usuário já existe', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.get_by_email(email):
            flash('E-mail já cadastrado', 'danger')
            return redirect(url_for('auth.register'))
        
        User.create(username=username, email=email, password=password, phone=phone, role='garcom')
        
        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth.route('/cliente/login', methods=['GET', 'POST'])
def customer_login():
    if session.get('customer_id'):
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        if not name or not phone:
            flash('Por favor, preencha nome e telefone', 'danger')
            return redirect(url_for('auth.customer_login'))
        
        customer = Customer.get_by_phone(phone)
        
        if customer:
            if customer['name'] != name:
                flash('Nome não corresponde ao telefone cadastrado', 'danger')
                return redirect(url_for('auth.customer_login'))
            
            session['customer_id'] = customer['id']
            session['customer_name'] = customer['name']
            session['customer_phone'] = customer['phone']
            
            flash(f'Bem-vindo de volta, {customer["name"]}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.index'))
        else:
            customer_id = Customer.create(name=name, phone=phone)
            
            session['customer_id'] = customer_id
            session['customer_name'] = name
            session['customer_phone'] = phone
            
            flash(f'Cadastro realizado! Bem-vindo, {name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.index'))
    
    return render_template('auth/customer_login.html')

@auth.route('/cliente/logout')
def customer_logout():
    session.pop('customer_id', None)
    session.pop('customer_name', None)
    session.pop('customer_phone', None)
    flash('Você saiu da sua conta', 'info')
    return redirect(url_for('main.index'))
