import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'meatz.db')

def get_db_path():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def apply_migrations():
    """Aplica migrações de esquema de forma idempotente"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        def column_exists(table_name, column_name):
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            return column_name in columns
        
        migrations = [
            ('"order"', 'order_type', 'ALTER TABLE "order" ADD COLUMN order_type TEXT DEFAULT "mesa"'),
            ('"order"', 'customer_id', 'ALTER TABLE "order" ADD COLUMN customer_id INTEGER'),
            ('"order"', 'delivery_address', 'ALTER TABLE "order" ADD COLUMN delivery_address TEXT'),
            ('"order"', 'delivery_fee', 'ALTER TABLE "order" ADD COLUMN delivery_fee REAL DEFAULT 0'),
            ('"order"', 'tip_amount', 'ALTER TABLE "order" ADD COLUMN tip_amount REAL DEFAULT 0'),
            ('"order"', 'tip_percentage', 'ALTER TABLE "order" ADD COLUMN tip_percentage REAL DEFAULT 0'),
            ('"order"', 'source_channel', 'ALTER TABLE "order" ADD COLUMN source_channel TEXT DEFAULT "mesa"'),
            ('product', 'prep_time_minutes', 'ALTER TABLE product ADD COLUMN prep_time_minutes INTEGER DEFAULT 15'),
            ('product', 'prep_section', 'ALTER TABLE product ADD COLUMN prep_section TEXT DEFAULT "geral"'),
            ('product', 'allows_modifiers', 'ALTER TABLE product ADD COLUMN allows_modifiers INTEGER DEFAULT 1'),
            ('order_item', 'status', 'ALTER TABLE order_item ADD COLUMN status TEXT DEFAULT "novo"'),
            ('order_item', 'prep_started_at', 'ALTER TABLE order_item ADD COLUMN prep_started_at TIMESTAMP'),
            ('order_item', 'prep_completed_at', 'ALTER TABLE order_item ADD COLUMN prep_completed_at TIMESTAMP'),
            ('order_item', 'delivered_at', 'ALTER TABLE order_item ADD COLUMN delivered_at TIMESTAMP'),
            ('order_item', 'group_priority', 'ALTER TABLE order_item ADD COLUMN group_priority INTEGER DEFAULT 0'),
            ('"table"', 'layout_x', 'ALTER TABLE "table" ADD COLUMN layout_x INTEGER DEFAULT 0'),
            ('"table"', 'layout_y', 'ALTER TABLE "table" ADD COLUMN layout_y INTEGER DEFAULT 0'),
            ('"table"', 'shape', 'ALTER TABLE "table" ADD COLUMN shape TEXT DEFAULT "square"'),
            ('payment', 'external_reference', 'ALTER TABLE payment ADD COLUMN external_reference TEXT'),
            ('payment', 'split_id', 'ALTER TABLE payment ADD COLUMN split_id INTEGER'),
            ('inventory', 'expiry_alert_days', 'ALTER TABLE inventory ADD COLUMN expiry_alert_days INTEGER DEFAULT 7'),
            ('user', 'commission_percentage', 'ALTER TABLE user ADD COLUMN commission_percentage REAL DEFAULT 0'),
            ('user', 'is_active', 'ALTER TABLE user ADD COLUMN is_active INTEGER DEFAULT 1'),
            ('user', 'last_login', 'ALTER TABLE user ADD COLUMN last_login TIMESTAMP'),
            ('settings', 'tip_percentage', 'ALTER TABLE settings ADD COLUMN tip_percentage REAL DEFAULT 10'),
            ('settings', 'enable_auto_tip', 'ALTER TABLE settings ADD COLUMN enable_auto_tip INTEGER DEFAULT 0'),
            ('settings', 'store_zipcode', 'ALTER TABLE settings ADD COLUMN store_zipcode TEXT DEFAULT ""'),
            ('settings', 'delivery_radius_km', 'ALTER TABLE settings ADD COLUMN delivery_radius_km REAL DEFAULT 5.0'),
            ('settings', 'enable_delivery', 'ALTER TABLE settings ADD COLUMN enable_delivery INTEGER DEFAULT 1'),
            ('settings', 'delivery_fee', 'ALTER TABLE settings ADD COLUMN delivery_fee REAL DEFAULT 5.0'),
            ('settings', 'store_latitude', 'ALTER TABLE settings ADD COLUMN store_latitude REAL'),
            ('settings', 'store_longitude', 'ALTER TABLE settings ADD COLUMN store_longitude REAL'),
            ('settings', 'store_city', 'ALTER TABLE settings ADD COLUMN store_city TEXT'),
            ('settings', 'store_state', 'ALTER TABLE settings ADD COLUMN store_state TEXT'),
            ('customer', 'address', 'ALTER TABLE customer ADD COLUMN address TEXT'),
            ('customer', 'zipcode', 'ALTER TABLE customer ADD COLUMN zipcode TEXT'),
            ('customer', 'city', 'ALTER TABLE customer ADD COLUMN city TEXT'),
            ('customer', 'state', 'ALTER TABLE customer ADD COLUMN state TEXT'),
            ('customer', 'latitude', 'ALTER TABLE customer ADD COLUMN latitude REAL'),
            ('customer', 'longitude', 'ALTER TABLE customer ADD COLUMN longitude REAL'),
        ]
        
        for table, column, sql in migrations:
            if not column_exists(table, column):
                try:
                    cursor.execute(sql)
                    print(f'✅ Migração aplicada: {table}.{column}')
                except sqlite3.OperationalError as e:
                    print(f'⚠️  Erro ao aplicar migração {table}.{column}: {e}')
        
        conn.commit()

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                role TEXT DEFAULT 'garcom',
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image_url TEXT,
                category_id INTEGER,
                available INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES category (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS "table" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number INTEGER UNIQUE NOT NULL,
                capacity INTEGER DEFAULT 4,
                status TEXT DEFAULT 'livre',
                pin TEXT,
                current_order_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (current_order_id) REFERENCES "order" (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS "order" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER,
                user_id INTEGER,
                status TEXT DEFAULT 'pendente',
                total REAL DEFAULT 0.0,
                payment_method TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (table_id) REFERENCES "table" (id),
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                price REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES "order" (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES product (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                method TEXT NOT NULL,
                status TEXT DEFAULT 'pendente',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES "order" (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_name TEXT DEFAULT 'MEATZ',
                logo_url TEXT DEFAULT '',
                phone TEXT DEFAULT '(61) 9 9999-9999',
                email TEXT DEFAULT 'contato@meatzburger.com',
                address TEXT DEFAULT 'Av. Principal, 175 - Centro, Cidade - UF',
                opening_hours TEXT DEFAULT '11:00 - 23:00 (Todos os dias)',
                whatsapp TEXT DEFAULT '5561999999999',
                instagram TEXT DEFAULT '',
                facebook TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_ingredient (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                ingredient_name TEXT NOT NULL,
                quantity_per_unit REAL DEFAULT 1.0,
                unit TEXT DEFAULT 'un',
                FOREIGN KEY (product_id) REFERENCES product (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_name TEXT UNIQUE NOT NULL,
                current_stock REAL DEFAULT 0,
                min_stock REAL DEFAULT 10,
                unit TEXT DEFAULT 'un',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE,
                email TEXT,
                loyalty_points INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loyalty_transaction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_id INTEGER,
                points INTEGER NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customer (id),
                FOREIGN KEY (order_id) REFERENCES "order" (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_split (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                split_type TEXT NOT NULL,
                number_of_splits INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES "order" (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_split_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                split_id INTEGER NOT NULL,
                order_item_id INTEGER NOT NULL,
                split_number INTEGER NOT NULL,
                amount REAL NOT NULL,
                paid INTEGER DEFAULT 0,
                FOREIGN KEY (split_id) REFERENCES order_split (id) ON DELETE CASCADE,
                FOREIGN KEY (order_item_id) REFERENCES order_item (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_suggestion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                suggested_product_id INTEGER NOT NULL,
                suggestion_type TEXT DEFAULT 'upsell',
                priority INTEGER DEFAULT 1,
                FOREIGN KEY (product_id) REFERENCES product (id) ON DELETE CASCADE,
                FOREIGN KEY (suggested_product_id) REFERENCES product (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_modifier_group (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                product_id INTEGER,
                min_selection INTEGER DEFAULT 0,
                max_selection INTEGER DEFAULT 1,
                required INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES product (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_modifier_option (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modifier_group_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price_adjustment REAL DEFAULT 0,
                available INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (modifier_group_id) REFERENCES product_modifier_group (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_item_modifier (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_item_id INTEGER NOT NULL,
                modifier_option_id INTEGER NOT NULL,
                price_adjustment REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_item_id) REFERENCES order_item (id) ON DELETE CASCADE,
                FOREIGN KEY (modifier_option_id) REFERENCES product_modifier_option (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS table_grouping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                table_ids TEXT NOT NULL,
                merged_order_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dissolved_at TIMESTAMP,
                FOREIGN KEY (merged_order_id) REFERENCES "order" (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS table_merge_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                source_table_id INTEGER NOT NULL,
                destination_table_id INTEGER,
                action TEXT NOT NULL,
                performed_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES table_grouping (id),
                FOREIGN KEY (source_table_id) REFERENCES "table" (id),
                FOREIGN KEY (destination_table_id) REFERENCES "table" (id),
                FOREIGN KEY (performed_by) REFERENCES user (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_transfer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                reason TEXT,
                transferred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES "order" (id),
                FOREIGN KEY (from_user_id) REFERENCES user (id),
                FOREIGN KEY (to_user_id) REFERENCES user (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_message (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                table_id INTEGER,
                from_user_id INTEGER NOT NULL,
                to_role TEXT NOT NULL,
                message TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES "order" (id),
                FOREIGN KEY (table_id) REFERENCES "table" (id),
                FOREIGN KEY (from_user_id) REFERENCES user (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_message_receipt (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES service_message (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_template (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                user_id INTEGER,
                table_id INTEGER,
                items_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id),
                FOREIGN KEY (table_id) REFERENCES "table" (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_charge_policy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                percentage REAL DEFAULT 10.0,
                is_automatic INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_service_charge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                policy_id INTEGER,
                amount REAL NOT NULL,
                percentage REAL,
                type TEXT DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES "order" (id),
                FOREIGN KEY (policy_id) REFERENCES service_charge_policy (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_split (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                split_number INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT,
                paid INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES "order" (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS delivery_driver (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                vehicle_type TEXT,
                license_plate TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS delivery_order (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                driver_id INTEGER,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                delivery_address TEXT NOT NULL,
                delivery_fee REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                estimated_time INTEGER,
                picked_up_at TIMESTAMP,
                delivered_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES "order" (id),
                FOREIGN KEY (driver_id) REFERENCES delivery_driver (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS delivery_route_event (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                delivery_order_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (delivery_order_id) REFERENCES delivery_order (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                customer_email TEXT,
                party_size INTEGER NOT NULL,
                reservation_date DATE NOT NULL,
                reservation_time TIME NOT NULL,
                table_id INTEGER,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                confirmed_at TIMESTAMP,
                cancelled_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (table_id) REFERENCES "table" (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS waitlist_entry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                party_size INTEGER NOT NULL,
                status TEXT DEFAULT 'waiting',
                notified_at TIMESTAMP,
                seated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cash_operation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                reason TEXT,
                performed_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (performed_by) REFERENCES user (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cashier_session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                opening_balance REAL DEFAULT 0,
                closing_balance REAL,
                status TEXT DEFAULT 'open',
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shift_assignment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                shift_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                actual_start TIMESTAMP,
                actual_end TIMESTAMP,
                status TEXT DEFAULT 'scheduled',
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_batch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_name TEXT NOT NULL,
                batch_number TEXT,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                expiry_date DATE,
                supplier TEXT,
                purchase_price REAL,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_transaction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_name TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                order_id INTEGER,
                batch_id INTEGER,
                performed_by INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES "order" (id),
                FOREIGN KEY (batch_id) REFERENCES inventory_batch (id),
                FOREIGN KEY (performed_by) REFERENCES user (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_subscription (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS print_job (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                printer_type TEXT NOT NULL,
                content_type TEXT NOT NULL,
                content_data TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                printed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_export (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                format TEXT NOT NULL,
                parameters TEXT,
                file_path TEXT,
                status TEXT DEFAULT 'pending',
                generated_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (generated_by) REFERENCES user (id)
            )
        ''')
        
        conn.commit()
        print('✅ Todas as tabelas criadas com sucesso!')
    
    apply_migrations()
