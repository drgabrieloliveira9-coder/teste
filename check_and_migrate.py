import sqlite3
import os

DB_PATH = 'data/meatz.db'

def check_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Total de tabelas encontradas: {len(tables)}")
    print("\nTabelas existentes:")
    for table in tables:
        print(f"  - {table}")
    
    expected_new_tables = [
        'product_modifier_group', 'product_modifier_option', 'order_item_modifier',
        'table_grouping', 'table_merge_history', 'order_transfer',
        'service_message', 'service_message_receipt', 'order_template',
        'service_charge_policy', 'order_service_charge', 'payment_split',
        'audit_log', 'delivery_driver', 'delivery_order', 'delivery_route_event',
        'reservation', 'waitlist_entry', 'cash_operation', 'cashier_session',
        'shift_assignment', 'inventory_batch', 'inventory_transaction',
        'notification_subscription', 'print_job', 'report_export'
    ]
    
    missing_tables = [t for t in expected_new_tables if t not in tables]
    
    if missing_tables:
        print(f"\n❌ FALTAM {len(missing_tables)} TABELAS:")
        for table in missing_tables:
            print(f"  - {table}")
    else:
        print("\n✅ Todas as novas tabelas foram criadas!")
    
    conn.close()
    return missing_tables

if __name__ == '__main__':
    missing = check_tables()
    
    if missing:
        print("\n🔧 Para criar as tabelas faltantes, delete o banco data/meatz.db")
        print("   O sistema vai recriá-lo automaticamente com todas as tabelas.")
