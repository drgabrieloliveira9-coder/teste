from app import create_app
from app.database import init_db
from app.db_operations import User, Settings
import os

app = create_app()

if __name__ == '__main__':
    init_db()
    
    if User.count() == 0:
        default_password = os.getenv('ADMIN_DEFAULT_PASSWORD', 'admin123')
        User.create(username='admin', email='admin@meatz.com', password=default_password, role='admin')
        print(f'⚠️  Usuário admin criado. ALTERE A SENHA IMEDIATAMENTE!')
        print(f'   Usuário: admin')
        print(f'   Senha padrão: {default_password}')
    
    if Settings.count() == 0:
        Settings.create(
            store_name='Meatz Burger',
            phone='(11) 99999-9999',
            email='contato@meatz.com',
            address='Rua Exemplo, 123',
            opening_hours='Seg-Dom: 11h-23h'
        )
    
    app.run(host='0.0.0.0', port=5000, debug=True)
