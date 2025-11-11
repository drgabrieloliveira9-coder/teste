from app.database import get_db_connection
from datetime import datetime
import json

class ProductModifierGroup:
    @staticmethod
    def create(name, product_id=None, min_selection=0, max_selection=1, required=False):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO product_modifier_group (name, product_id, min_selection, max_selection, required)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, product_id, min_selection, max_selection, 1 if required else 0))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_product(product_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM product_modifier_group WHERE product_id = ?', (product_id,))
            return cursor.fetchall()
    
    @staticmethod
    def get_by_id(group_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM product_modifier_group WHERE id = ?', (group_id,))
            return cursor.fetchone()
    
    @staticmethod
    def get_all():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM product_modifier_group ORDER BY created_at DESC')
            return cursor.fetchall()

class ProductModifierOption:
    @staticmethod
    def create(modifier_group_id, name, price_adjustment=0, available=True):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO product_modifier_option (modifier_group_id, name, price_adjustment, available)
                VALUES (?, ?, ?, ?)
            ''', (modifier_group_id, name, price_adjustment, 1 if available else 0))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_group(modifier_group_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM product_modifier_option WHERE modifier_group_id = ? AND available = 1', (modifier_group_id,))
            return cursor.fetchall()

class OrderItemModifier:
    @staticmethod
    def create(order_item_id, modifier_option_id, price_adjustment):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO order_item_modifier (order_item_id, modifier_option_id, price_adjustment)
                VALUES (?, ?, ?)
            ''', (order_item_id, modifier_option_id, price_adjustment))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_order_item(order_item_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT oim.*, pmo.name as modifier_name, pmg.name as group_name
                FROM order_item_modifier oim
                JOIN product_modifier_option pmo ON oim.modifier_option_id = pmo.id
                JOIN product_modifier_group pmg ON pmo.modifier_group_id = pmg.id
                WHERE oim.order_item_id = ?
            ''', (order_item_id,))
            return cursor.fetchall()

class TableGrouping:
    @staticmethod
    def create(name, table_ids, merged_order_id=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            table_ids_str = ','.join(map(str, table_ids))
            cursor.execute('''
                INSERT INTO table_grouping (name, table_ids, merged_order_id)
                VALUES (?, ?, ?)
            ''', (name, table_ids_str, merged_order_id))
            return cursor.lastrowid
    
    @staticmethod
    def get_active():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM table_grouping WHERE dissolved_at IS NULL')
            return cursor.fetchall()
    
    @staticmethod
    def dissolve(group_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE table_grouping SET dissolved_at = CURRENT_TIMESTAMP WHERE id = ?', (group_id,))
            return cursor.rowcount > 0

class TableMergeHistory:
    @staticmethod
    def create(group_id, source_table_id, destination_table_id, action, performed_by):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO table_merge_history (group_id, source_table_id, destination_table_id, action, performed_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (group_id, source_table_id, destination_table_id, action, performed_by))
            return cursor.lastrowid

class OrderTransfer:
    @staticmethod
    def create(order_id, from_user_id, to_user_id, reason=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO order_transfer (order_id, from_user_id, to_user_id, reason)
                VALUES (?, ?, ?, ?)
            ''', (order_id, from_user_id, to_user_id, reason))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_order(order_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ot.*, 
                       u1.username as from_user, 
                       u2.username as to_user
                FROM order_transfer ot
                JOIN user u1 ON ot.from_user_id = u1.id
                JOIN user u2 ON ot.to_user_id = u2.id
                WHERE ot.order_id = ?
                ORDER BY ot.transferred_at DESC
            ''', (order_id,))
            return cursor.fetchall()

class ServiceMessage:
    @staticmethod
    def create(from_user_id, to_role, message, order_id=None, table_id=None, priority='normal'):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO service_message (order_id, table_id, from_user_id, to_role, message, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (order_id, table_id, from_user_id, to_role, message, priority))
            return cursor.lastrowid
    
    @staticmethod
    def get_unread_by_role(role, user_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sm.*, u.username as from_user
                FROM service_message sm
                JOIN user u ON sm.from_user_id = u.id
                LEFT JOIN service_message_receipt smr ON sm.id = smr.message_id AND smr.user_id = ?
                WHERE sm.to_role = ? AND smr.id IS NULL
                ORDER BY sm.created_at DESC
            ''', (user_id, role))
            return cursor.fetchall()
    
    @staticmethod
    def mark_as_read(message_id, user_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO service_message_receipt (message_id, user_id)
                VALUES (?, ?)
            ''', (message_id, user_id))
            return cursor.lastrowid

class OrderTemplate:
    @staticmethod
    def create(name, items_data, user_id=None, table_id=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            items_json = json.dumps(items_data)
            cursor.execute('''
                INSERT INTO order_template (name, user_id, table_id, items_data)
                VALUES (?, ?, ?, ?)
            ''', (name, user_id, table_id, items_json))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_user(user_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM order_template WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
            templates = cursor.fetchall()
            for template in templates:
                template['items_data'] = json.loads(template['items_data'])
            return templates
    
    @staticmethod
    def get_by_table(table_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM order_template WHERE table_id = ? ORDER BY created_at DESC LIMIT 5', (table_id,))
            templates = cursor.fetchall()
            for template in templates:
                template['items_data'] = json.loads(template['items_data'])
            return templates

class ServiceChargePolicy:
    @staticmethod
    def create(name, percentage=10.0, is_automatic=False):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO service_charge_policy (name, percentage, is_automatic)
                VALUES (?, ?, ?)
            ''', (name, percentage, 1 if is_automatic else 0))
            return cursor.lastrowid
    
    @staticmethod
    def get_active():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM service_charge_policy WHERE active = 1')
            return cursor.fetchall()
    
    @staticmethod
    def get_automatic():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM service_charge_policy WHERE active = 1 AND is_automatic = 1 LIMIT 1')
            return cursor.fetchone()

class OrderServiceCharge:
    @staticmethod
    def create(order_id, amount, percentage=None, policy_id=None, type='manual'):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO order_service_charge (order_id, policy_id, amount, percentage, type)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, policy_id, amount, percentage, type))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_order(order_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM order_service_charge WHERE order_id = ?', (order_id,))
            return cursor.fetchone()

class PaymentSplit:
    @staticmethod
    def create(order_id, split_number, amount, payment_method=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payment_split (order_id, split_number, amount, payment_method)
                VALUES (?, ?, ?, ?)
            ''', (order_id, split_number, amount, payment_method))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_order(order_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM payment_split WHERE order_id = ? ORDER BY split_number', (order_id,))
            return cursor.fetchall()
    
    @staticmethod
    def mark_paid(split_id, payment_method):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE payment_split SET paid = 1, payment_method = ? WHERE id = ?', (payment_method, split_id))
            return cursor.rowcount > 0

class AuditLog:
    @staticmethod
    def create(action, entity_type, entity_id=None, user_id=None, old_values=None, new_values=None, ip_address=None, user_agent=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            old_json = json.dumps(old_values) if old_values else None
            new_json = json.dumps(new_values) if new_values else None
            cursor.execute('''
                INSERT INTO audit_log (user_id, action, entity_type, entity_id, old_values, new_values, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, action, entity_type, entity_id, old_json, new_json, ip_address, user_agent))
            return cursor.lastrowid
    
    @staticmethod
    def get_recent(limit=100):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT al.*, u.username
                FROM audit_log al
                LEFT JOIN user u ON al.user_id = u.id
                ORDER BY al.created_at DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
    
    @staticmethod
    def get_by_entity(entity_type, entity_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT al.*, u.username
                FROM audit_log al
                LEFT JOIN user u ON al.user_id = u.id
                WHERE al.entity_type = ? AND al.entity_id = ?
                ORDER BY al.created_at DESC
            ''', (entity_type, entity_id))
            return cursor.fetchall()

class DeliveryDriver:
    @staticmethod
    def create(name, phone, vehicle_type=None, license_plate=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO delivery_driver (name, phone, vehicle_type, license_plate)
                VALUES (?, ?, ?, ?)
            ''', (name, phone, vehicle_type, license_plate))
            return cursor.lastrowid
    
    @staticmethod
    def get_all_active():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM delivery_driver WHERE active = 1')
            return cursor.fetchall()
    
    @staticmethod
    def get_by_id(driver_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM delivery_driver WHERE id = ?', (driver_id,))
            return cursor.fetchone()

class DeliveryOrder:
    @staticmethod
    def create(order_id, customer_name, customer_phone, delivery_address, delivery_fee=0, driver_id=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO delivery_order (order_id, driver_id, customer_name, customer_phone, delivery_address, delivery_fee)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (order_id, driver_id, customer_name, customer_phone, delivery_address, delivery_fee))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_status(status):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT do.*, o.total, o.status as order_status
                FROM delivery_order do
                JOIN "order" o ON do.order_id = o.id
                WHERE do.status = ?
                ORDER BY do.created_at DESC
            ''', (status,))
            return cursor.fetchall()
    
    @staticmethod
    def update_status(delivery_id, status):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            timestamp_field = None
            if status == 'picked_up':
                timestamp_field = 'picked_up_at'
            elif status == 'delivered':
                timestamp_field = 'delivered_at'
            
            if timestamp_field:
                cursor.execute(f'UPDATE delivery_order SET status = ?, {timestamp_field} = CURRENT_TIMESTAMP WHERE id = ?', (status, delivery_id))
            else:
                cursor.execute('UPDATE delivery_order SET status = ? WHERE id = ?', (status, delivery_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def assign_driver(delivery_id, driver_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE delivery_order SET driver_id = ? WHERE id = ?', (driver_id, delivery_id))
            return cursor.rowcount > 0

class DeliveryRouteEvent:
    @staticmethod
    def create(delivery_order_id, status, latitude=None, longitude=None, notes=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO delivery_route_event (delivery_order_id, status, latitude, longitude, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (delivery_order_id, status, latitude, longitude, notes))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_delivery(delivery_order_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM delivery_route_event WHERE delivery_order_id = ? ORDER BY created_at ASC', (delivery_order_id,))
            return cursor.fetchall()

class Reservation:
    @staticmethod
    def create(customer_name, customer_phone, party_size, reservation_date, reservation_time, customer_email=None, table_id=None, notes=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reservation (customer_name, customer_phone, customer_email, party_size, reservation_date, reservation_time, table_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_name, customer_phone, customer_email, party_size, reservation_date, reservation_time, table_id, notes))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_date(date):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reservation WHERE reservation_date = ? AND status != "cancelled" ORDER BY reservation_time', (date,))
            return cursor.fetchall()
    
    @staticmethod
    def confirm(reservation_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE reservation SET status = "confirmed", confirmed_at = CURRENT_TIMESTAMP WHERE id = ?', (reservation_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def cancel(reservation_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE reservation SET status = "cancelled", cancelled_at = CURRENT_TIMESTAMP WHERE id = ?', (reservation_id,))
            return cursor.rowcount > 0

class WaitlistEntry:
    @staticmethod
    def create(customer_name, customer_phone, party_size):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO waitlist_entry (customer_name, customer_phone, party_size)
                VALUES (?, ?, ?)
            ''', (customer_name, customer_phone, party_size))
            return cursor.lastrowid
    
    @staticmethod
    def get_waiting():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM waitlist_entry WHERE status = "waiting" ORDER BY created_at')
            return cursor.fetchall()
    
    @staticmethod
    def notify(entry_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE waitlist_entry SET status = "notified", notified_at = CURRENT_TIMESTAMP WHERE id = ?', (entry_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def seat(entry_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE waitlist_entry SET status = "seated", seated_at = CURRENT_TIMESTAMP WHERE id = ?', (entry_id,))
            return cursor.rowcount > 0

class CashOperation:
    @staticmethod
    def create(type, amount, performed_by, reason=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cash_operation (type, amount, reason, performed_by)
                VALUES (?, ?, ?, ?)
            ''', (type, amount, reason, performed_by))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_date(date):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT co.*, u.username
                FROM cash_operation co
                JOIN user u ON co.performed_by = u.id
                WHERE DATE(co.created_at) = ?
                ORDER BY co.created_at DESC
            ''', (date,))
            return cursor.fetchall()

class CashierSession:
    @staticmethod
    def create(user_id, opening_balance=0):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cashier_session (user_id, opening_balance)
                VALUES (?, ?)
            ''', (user_id, opening_balance))
            return cursor.lastrowid
    
    @staticmethod
    def get_open_by_user(user_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cashier_session WHERE user_id = ? AND status = "open" ORDER BY opened_at DESC LIMIT 1', (user_id,))
            return cursor.fetchone()
    
    @staticmethod
    def close_session(session_id, closing_balance):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE cashier_session SET status = "closed", closing_balance = ?, closed_at = CURRENT_TIMESTAMP WHERE id = ?', (closing_balance, session_id))
            return cursor.rowcount > 0

class ShiftAssignment:
    @staticmethod
    def create(user_id, shift_date, start_time, end_time):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO shift_assignment (user_id, shift_date, start_time, end_time)
                VALUES (?, ?, ?, ?)
            ''', (user_id, shift_date, start_time, end_time))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_date(date):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sa.*, u.username, u.role
                FROM shift_assignment sa
                JOIN user u ON sa.user_id = u.id
                WHERE sa.shift_date = ?
                ORDER BY sa.start_time
            ''', (date,))
            return cursor.fetchall()
    
    @staticmethod
    def clock_in(assignment_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE shift_assignment SET actual_start = CURRENT_TIMESTAMP, status = "active" WHERE id = ?', (assignment_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def clock_out(assignment_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE shift_assignment SET actual_end = CURRENT_TIMESTAMP, status = "completed" WHERE id = ?', (assignment_id,))
            return cursor.rowcount > 0

class InventoryBatch:
    @staticmethod
    def create(ingredient_name, quantity, unit, batch_number=None, expiry_date=None, supplier=None, purchase_price=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO inventory_batch (ingredient_name, batch_number, quantity, unit, expiry_date, supplier, purchase_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ingredient_name, batch_number, quantity, unit, expiry_date, supplier, purchase_price))
            return cursor.lastrowid
    
    @staticmethod
    def get_expiring_soon(days=7):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM inventory_batch 
                WHERE expiry_date IS NOT NULL 
                AND DATE(expiry_date) <= DATE('now', '+' || ? || ' days')
                ORDER BY expiry_date
            ''', (days,))
            return cursor.fetchall()

class InventoryTransaction:
    @staticmethod
    def create(ingredient_name, transaction_type, quantity, unit, order_id=None, batch_id=None, performed_by=None, notes=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO inventory_transaction (ingredient_name, transaction_type, quantity, unit, order_id, batch_id, performed_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ingredient_name, transaction_type, quantity, unit, order_id, batch_id, performed_by, notes))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_ingredient(ingredient_name, limit=50):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT it.*, u.username as performed_by_name
                FROM inventory_transaction it
                LEFT JOIN user u ON it.performed_by = u.id
                WHERE it.ingredient_name = ?
                ORDER BY it.created_at DESC
                LIMIT ?
            ''', (ingredient_name, limit))
            return cursor.fetchall()

class PrintJob:
    @staticmethod
    def create(printer_type, content_type, content_data):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            content_json = json.dumps(content_data)
            cursor.execute('''
                INSERT INTO print_job (printer_type, content_type, content_data)
                VALUES (?, ?, ?)
            ''', (printer_type, content_type, content_json))
            return cursor.lastrowid
    
    @staticmethod
    def mark_printed(job_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE print_job SET status = "printed", printed_at = CURRENT_TIMESTAMP WHERE id = ?', (job_id,))
            return cursor.rowcount > 0

class ReportExport:
    @staticmethod
    def create(report_type, format, parameters=None, generated_by=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            params_json = json.dumps(parameters) if parameters else None
            cursor.execute('''
                INSERT INTO report_export (report_type, format, parameters, generated_by)
                VALUES (?, ?, ?, ?)
            ''', (report_type, format, params_json, generated_by))
            return cursor.lastrowid
    
    @staticmethod
    def complete(export_id, file_path):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE report_export SET status = "completed", file_path = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?', (file_path, export_id))
            return cursor.rowcount > 0
