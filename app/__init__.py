from flask import Flask
from flask_login import LoginManager, UserMixin
import os
from dotenv import load_dotenv

load_dotenv()

login_manager = LoginManager()

class UserSession(UserMixin):
    def __init__(self, user_row):
        self.id = user_row['id']
        self.username = user_row['username']
        self.email = user_row['email']
        self.role = user_row['role']
        self.phone = user_row['phone']

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET')
    
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
    app.config['TEMPLATES_AUTO_RELOAD'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    from app.database import init_db
    from app.db_operations import User, Settings, Category, Product
    
    init_db()
    
    if User.count() == 0:
        default_password = os.getenv('ADMIN_DEFAULT_PASSWORD', 'admin123')
        User.create(username='admin', email='admin@meatz.com', password=default_password, role='admin')
        print(f'⚠️  Usuário admin criado. ALTERE A SENHA IMEDIATAMENTE!')
    
    if Settings.count() == 0:
        Settings.create(
            store_name='Meatz Burger',
            phone='(11) 99999-9999',
            email='contato@meatz.com',
            address='Rua Exemplo, 123',
            opening_hours='Seg-Dom: 11h-23h'
        )
        print('✅ Configurações padrão criadas')
    
    if Category.count() == 0:
        print('🍔 Criando categorias de exemplo...')
        cat_burgers = Category.create(
            name='Burgers',
            description='Nossos deliciosos hambúrgueres artesanais',
            image_url='https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800'
        )
        cat_acompanhamentos = Category.create(
            name='Acompanhamentos',
            description='Porções e acompanhamentos perfeitos',
            image_url='https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=800'
        )
        cat_bebidas = Category.create(
            name='Bebidas',
            description='Bebidas geladas e refrescantes',
            image_url='https://images.unsplash.com/photo-1437418747212-8d9709afab22?w=800'
        )
        cat_sobremesas = Category.create(
            name='Sobremesas',
            description='Doces irresistíveis',
            image_url='https://images.unsplash.com/photo-1488477181946-6428a0291777?w=800'
        )
        print('✅ 4 categorias criadas')
    
    if Product.count() == 0:
        print('🍔 Criando produtos de exemplo...')
        categories = Category.get_all()
        cat_dict = {cat['name']: cat['id'] for cat in categories}
        
        Product.create(
            name='Meatz Clássico',
            description='Hambúrguer 180g, queijo cheddar, alface, tomate, cebola caramelizada e molho especial',
            price=28.90,
            category_id=cat_dict['Burgers'],
            image_url='https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800',
            available=True
        )
        
        Product.create(
            name='Meatz Bacon',
            description='Hambúrguer 180g, queijo, bacon crocante, cebola crispy e molho barbecue',
            price=32.90,
            category_id=cat_dict['Burgers'],
            image_url='https://images.unsplash.com/photo-1550547660-d9450f859349?w=800',
            available=True
        )
        
        Product.create(
            name='Meatz Duplo',
            description='Dois hambúrgueres 180g, queijo duplo, picles, cebola e molho especial',
            price=42.90,
            category_id=cat_dict['Burgers'],
            image_url='https://images.unsplash.com/photo-1594212699903-ec8a3eca50f5?w=800',
            available=True
        )
        
        Product.create(
            name='Meatz Vegetariano',
            description='Hambúrguer de grão-de-bico, queijo, alface, tomate e maionese verde',
            price=26.90,
            category_id=cat_dict['Burgers'],
            image_url='https://images.unsplash.com/photo-1520072959219-c595dc870360?w=800',
            available=True
        )
        
        Product.create(
            name='Batata Frita',
            description='Porção generosa de batatas fritas crocantes',
            price=15.90,
            category_id=cat_dict['Acompanhamentos'],
            image_url='https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=800',
            available=True
        )
        
        Product.create(
            name='Onion Rings',
            description='Anéis de cebola empanados e fritos',
            price=18.90,
            category_id=cat_dict['Acompanhamentos'],
            image_url='https://images.unsplash.com/photo-1639024471283-03518883512d?w=800',
            available=True
        )
        
        Product.create(
            name='Nuggets (10un)',
            description='10 nuggets de frango crocantes',
            price=22.90,
            category_id=cat_dict['Acompanhamentos'],
            image_url='https://images.unsplash.com/photo-1562967914-608f82629710?w=800',
            available=True
        )
        
        Product.create(
            name='Coca-Cola',
            description='Refrigerante Coca-Cola lata 350ml',
            price=6.00,
            category_id=cat_dict['Bebidas'],
            image_url='https://images.unsplash.com/photo-1554866585-cd94860890b7?w=800',
            available=True
        )
        
        Product.create(
            name='Suco Natural',
            description='Suco natural de laranja 500ml',
            price=12.00,
            category_id=cat_dict['Bebidas'],
            image_url='https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=800',
            available=True
        )
        
        Product.create(
            name='Milkshake',
            description='Milkshake cremoso (chocolate, morango ou baunilha)',
            price=16.90,
            category_id=cat_dict['Bebidas'],
            image_url='https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=800',
            available=True
        )
        
        Product.create(
            name='Brownie',
            description='Brownie de chocolate com sorvete de baunilha',
            price=14.90,
            category_id=cat_dict['Sobremesas'],
            image_url='https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=800',
            available=True
        )
        
        Product.create(
            name='Petit Gateau',
            description='Bolinho de chocolate quente com sorvete',
            price=18.90,
            category_id=cat_dict['Sobremesas'],
            image_url='https://images.unsplash.com/photo-1624353365286-3f8d62daad51?w=800',
            available=True
        )
        
        print('✅ 12 produtos criados')
        print('🎉 Dados de exemplo carregados com sucesso!')
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # type: ignore
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.db_operations import User
        user_row = User.get_by_id(int(user_id))
        if user_row:
            return UserSession(user_row)
        return None
    
    from app.routes import main
    from app.auth import auth
    from app.admin import admin
    from app.pdv import pdv
    from app.chatbot import chatbot
    
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(pdv, url_prefix='/pdv')
    app.register_blueprint(chatbot, url_prefix='/chatbot')
    
    @app.context_processor
    def inject_settings():
        from app.db_operations import Settings
        from flask import g
        
        if not hasattr(g, 'site_settings'):
            settings_row = Settings.get()
            if settings_row:
                g.site_settings = dict(settings_row)
            else:
                g.site_settings = {
                    'store_name': 'BurgerLoft',
                    'phone': '',
                    'email': '',
                    'address': '',
                    'opening_hours': ''
                }
        
        return dict(site_settings=g.site_settings)
    
    return app
