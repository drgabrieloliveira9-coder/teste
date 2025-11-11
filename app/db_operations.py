from app.database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User:
    @staticmethod
    def create(username, email, password, role='garcom', phone=None):
        password_hash = generate_password_hash(password)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user (username, email, password_hash, role, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, role, phone))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(user_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user WHERE id = ?', (user_id,))
            return cursor.fetchone()
    
    @staticmethod
    def get_by_username(username):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user WHERE username = ?', (username,))
            return cursor.fetchone()
    
    @staticmethod
    def get_by_email(email):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user WHERE email = ?', (email,))
            return cursor.fetchone()
    
    @staticmethod
    def get_all():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user ORDER BY created_at DESC')
            return cursor.fetchall()
    
    @staticmethod
    def count():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM user')
            return cursor.fetchone()['count']
    
    @staticmethod
    def check_password(user_row, password):
        return check_password_hash(user_row['password_hash'], password)
    
    @staticmethod
    def update(user_id, **kwargs):
        fields = []
        values = []
        for key, value in kwargs.items():
            if key == 'password':
                fields.append('password_hash = ?')
                values.append(generate_password_hash(value))
            else:
                fields.append(f'{key} = ?')
                values.append(value)
        
        values.append(user_id)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE user SET {", ".join(fields)} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(user_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM user WHERE id = ?', (user_id,))
            return cursor.rowcount > 0

class Category:
    @staticmethod
    def create(name, description=None, image_url=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO category (name, description, image_url)
                VALUES (?, ?, ?)
            ''', (name, description, image_url))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(category_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM category WHERE id = ?', (category_id,))
            return cursor.fetchone()
    
    @staticmethod
    def get_all():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM category ORDER BY created_at DESC')
            return cursor.fetchall()
    
    @staticmethod
    def update(category_id, **kwargs):
        fields = [f'{key} = ?' for key in kwargs.keys()]
        values = list(kwargs.values()) + [category_id]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE category SET {", ".join(fields)} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(category_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM category WHERE id = ?', (category_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def count():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM category')
            return cursor.fetchone()['count']

class Product:
    @staticmethod
    def create(name, price, description=None, image_url=None, category_id=None, available=True):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO product (name, description, price, image_url, category_id, available)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, description, price, image_url, category_id, 1 if available else 0))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(product_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM product WHERE id = ?', (product_id,))
            return cursor.fetchone()
    
    @staticmethod
    def get_all(available_only=False):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if available_only:
                cursor.execute('SELECT * FROM product WHERE available = 1 ORDER BY created_at DESC')
            else:
                cursor.execute('SELECT * FROM product ORDER BY created_at DESC')
            return cursor.fetchall()
    
    @staticmethod
    def get_by_category(category_id, available_only=False):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if available_only:
                cursor.execute('SELECT * FROM product WHERE category_id = ? AND available = 1 ORDER BY created_at DESC', (category_id,))
            else:
                cursor.execute('SELECT * FROM product WHERE category_id = ? ORDER BY created_at DESC', (category_id,))
            return cursor.fetchall()
    
    @staticmethod
    def get_featured(limit=4):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM product WHERE available = 1 LIMIT ?', (limit,))
            return cursor.fetchall()
    
    @staticmethod
    def update(product_id, **kwargs):
        if 'available' in kwargs:
            kwargs['available'] = 1 if kwargs['available'] else 0
        fields = [f'{key} = ?' for key in kwargs.keys()]
        values = list(kwargs.values()) + [product_id]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE product SET {", ".join(fields)} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(product_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM product WHERE id = ?', (product_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def count():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM product')
            return cursor.fetchone()['count']

class Table:
    @staticmethod
    def create(number, capacity=4, pin=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO "table" (number, capacity, pin)
                VALUES (?, ?, ?)
            ''', (number, capacity, pin))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(table_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM "table" WHERE id = ?', (table_id,))
            return cursor.fetchone()
    
    @staticmethod
    def get_by_number(number):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM "table" WHERE number = ?', (number,))
            return cursor.fetchone()
    
    @staticmethod
    def get_all():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM "table" ORDER BY number')
            return cursor.fetchall()
    
    @staticmethod
    def update(table_id, **kwargs):
        fields = [f'{key} = ?' for key in kwargs.keys()]
        values = list(kwargs.values()) + [table_id]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE "table" SET {", ".join(fields)} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(table_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM "table" WHERE id = ?', (table_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def count():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM "table"')
            return cursor.fetchone()['count']

class Order:
    @staticmethod
    def create(table_id=None, user_id=None, customer_id=None, status='pendente', total=0.0, 
              payment_method=None, notes=None, order_type='mesa', delivery_address=None, delivery_fee=0.0):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO "order" (table_id, user_id, customer_id, status, total, payment_method, notes, 
                                   order_type, delivery_address, delivery_fee)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (table_id, user_id, customer_id, status, total, payment_method, notes, 
                 order_type, delivery_address, delivery_fee))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(order_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM "order" WHERE id = ?', (order_id,))
            return cursor.fetchone()
    
    @staticmethod
    def get_all():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM "order" ORDER BY created_at DESC')
            return cursor.fetchall()
    
    @staticmethod
    def get_by_status(status):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM "order" WHERE status = ? ORDER BY created_at DESC', (status,))
            return cursor.fetchall()
    
    @staticmethod
    def get_by_table(table_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM "order" WHERE table_id = ? ORDER BY created_at DESC', (table_id,))
            return cursor.fetchall()
    
    @staticmethod
    def update(order_id, **kwargs):
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.now()
        fields = [f'{key} = ?' for key in kwargs.keys()]
        values = list(kwargs.values()) + [order_id]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE "order" SET {", ".join(fields)} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(order_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM "order" WHERE id = ?', (order_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def count():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM "order"')
            return cursor.fetchone()['count']
    
    @staticmethod
    def count_by_status(status):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM "order" WHERE status = ?', (status,))
            return cursor.fetchone()['count']
    
    @staticmethod
    def get_recent(limit=10):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM "order" ORDER BY created_at DESC LIMIT ?', (limit,))
            return cursor.fetchall()
    
    @staticmethod
    def get_total_revenue_by_status(status):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(total) as revenue FROM "order" WHERE status = ?', (status,))
            result = cursor.fetchone()
            return result['revenue'] if result['revenue'] is not None else 0
    
    @staticmethod
    def get_by_date_and_status(date, status):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM "order" 
                WHERE DATE(created_at) = DATE(?) AND status = ?
                ORDER BY created_at DESC
            ''', (date, status))
            return cursor.fetchall()
    
    @staticmethod
    def get_by_statuses(statuses):
        if not statuses:
            return []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join(['?' for _ in statuses])
            cursor.execute(f'''
                SELECT * FROM "order" 
                WHERE status IN ({placeholders})
                ORDER BY created_at ASC
            ''', statuses)
            return cursor.fetchall()

class OrderItem:
    @staticmethod
    def create(order_id, product_id, quantity, price, notes=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO order_item (order_id, product_id, quantity, price, notes, status)
                VALUES (?, ?, ?, ?, ?, 'novo')
            ''', (order_id, product_id, quantity, price, notes))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(item_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM order_item WHERE id = ?', (item_id,))
            return cursor.fetchone()
    
    @staticmethod
    def get_by_order(order_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT oi.*, p.name as product_name, p.image_url as product_image, p.prep_section
                FROM order_item oi
                JOIN product p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            ''', (order_id,))
            return cursor.fetchall()
    
    @staticmethod
    def update_status(item_id, status):
        timestamp_field = None
        if status == 'preparando':
            timestamp_field = 'prep_started_at'
        elif status == 'pronto':
            timestamp_field = 'prep_completed_at'
        elif status == 'entregue':
            timestamp_field = 'delivered_at'
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if timestamp_field:
                cursor.execute(f'''
                    UPDATE order_item 
                    SET status = ?, {timestamp_field} = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, item_id))
            else:
                cursor.execute('UPDATE order_item SET status = ? WHERE id = ?', (status, item_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def get_prep_time(item_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    CAST((julianday(COALESCE(prep_completed_at, CURRENT_TIMESTAMP)) - julianday(prep_started_at)) * 24 * 60 AS INTEGER) as prep_time_minutes
                FROM order_item 
                WHERE id = ?
            ''', (item_id,))
            result = cursor.fetchone()
            return result['prep_time_minutes'] if result else 0
    
    @staticmethod
    def delete(item_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM order_item WHERE id = ?', (item_id,))
            return cursor.rowcount > 0

class Payment:
    @staticmethod
    def create(order_id, amount, method, status='pendente'):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payment (order_id, amount, method, status)
                VALUES (?, ?, ?, ?)
            ''', (order_id, amount, method, status))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(payment_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM payment WHERE id = ?', (payment_id,))
            return cursor.fetchone()
    
    @staticmethod
    def get_by_order(order_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM payment WHERE order_id = ?', (order_id,))
            return cursor.fetchall()
    
    @staticmethod
    def update(payment_id, **kwargs):
        fields = [f'{key} = ?' for key in kwargs.keys()]
        values = list(kwargs.values()) + [payment_id]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE payment SET {", ".join(fields)} WHERE id = ?', values)
            return cursor.rowcount > 0

class Settings:
    @staticmethod
    def create(**kwargs):
        defaults = {
            'store_name': 'MEATZ',
            'logo_url': '',
            'phone': '(61) 9 9999-9999',
            'email': 'contato@meatzburger.com',
            'address': 'Av. Principal, 175 - Centro, Cidade - UF',
            'opening_hours': '11:00 - 23:00 (Todos os dias)',
            'whatsapp': '5561999999999',
            'instagram': '',
            'facebook': ''
        }
        defaults.update(kwargs)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            fields = ', '.join(defaults.keys())
            placeholders = ', '.join(['?' for _ in defaults])
            cursor.execute(f'INSERT INTO settings ({fields}) VALUES ({placeholders})', list(defaults.values()))
            return cursor.lastrowid
    
    @staticmethod
    def get():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM settings LIMIT 1')
            return cursor.fetchone()
    
    @staticmethod
    def update(**kwargs):
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.now()
        
        fields = [f'{key} = ?' for key in kwargs.keys()]
        values = list(kwargs.values())
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE settings SET {", ".join(fields)}', values)
            return cursor.rowcount > 0
    
    @staticmethod
    def count():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM settings')
            return cursor.fetchone()['count']

class Customer:
    @staticmethod
    def create(name, phone, email=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO customer (name, phone, email, loyalty_points, total_spent)
                VALUES (?, ?, ?, 0, 0)
            ''', (name, phone, email))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(customer_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customer WHERE id = ?', (customer_id,))
            return cursor.fetchone()
    
    @staticmethod
    def get_by_phone(phone):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customer WHERE phone = ?', (phone,))
            return cursor.fetchone()
    
    @staticmethod
    def update_loyalty_points(customer_id, points_delta):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE customer 
                SET loyalty_points = loyalty_points + ?
                WHERE id = ?
            ''', (points_delta, customer_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def update_total_spent(customer_id, amount):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE customer 
                SET total_spent = total_spent + ?
                WHERE id = ?
            ''', (amount, customer_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def update(customer_id, **kwargs):
        fields = [f'{key} = ?' for key in kwargs.keys()]
        values = list(kwargs.values()) + [customer_id]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE customer SET {", ".join(fields)} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    @staticmethod
    def get_all():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customer ORDER BY name')
            return cursor.fetchall()

class ProductSuggestion:
    @staticmethod
    def create(product_id, suggested_product_id, suggestion_type='upsell', priority=1):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO product_suggestion (product_id, suggested_product_id, suggestion_type, priority)
                VALUES (?, ?, ?, ?)
            ''', (product_id, suggested_product_id, suggestion_type, priority))
            return cursor.lastrowid
    
    @staticmethod
    def get_suggestions_for_product(product_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, ps.suggestion_type, ps.priority
                FROM product_suggestion ps
                JOIN product p ON ps.suggested_product_id = p.id
                WHERE ps.product_id = ? AND p.available = 1
                ORDER BY ps.priority DESC
            ''', (product_id,))
            return cursor.fetchall()
    
    @staticmethod
    def get_suggestions_for_order(order_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT p.*, ps.suggestion_type
                FROM order_item oi
                JOIN product_suggestion ps ON oi.product_id = ps.product_id
                JOIN product p ON ps.suggested_product_id = p.id
                WHERE oi.order_id = ? AND p.available = 1
                ORDER BY ps.priority DESC
                LIMIT 5
            ''', (order_id,))
            return cursor.fetchall()

class Inventory:
    @staticmethod
    def create(ingredient_name, current_stock, min_stock=10, unit='un'):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO inventory (ingredient_name, current_stock, min_stock, unit)
                VALUES (?, ?, ?, ?)
            ''', (ingredient_name, current_stock, min_stock, unit))
            return cursor.lastrowid
    
    @staticmethod
    def get_all():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM inventory ORDER BY ingredient_name')
            return cursor.fetchall()
    
    @staticmethod
    def get_low_stock():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM inventory 
                WHERE current_stock <= min_stock
                ORDER BY current_stock ASC
            ''')
            return cursor.fetchall()
    
    @staticmethod
    def update_stock(ingredient_name, quantity_delta):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE inventory 
                SET current_stock = current_stock + ?, last_updated = CURRENT_TIMESTAMP
                WHERE ingredient_name = ?
            ''', (quantity_delta, ingredient_name))
            return cursor.rowcount > 0
