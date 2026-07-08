import sqlite3
import jdatetime
from datetime import datetime

# ============================================
# تنظیمات اولیه - مسیر دیتابیس را وارد کنید
# ============================================
DB_PATH = 'db (8).sqlite3'  # مسیر فایل دیتابیس خود را وارد کنید

def dict_factory(cursor, row):
    """تبدیل خروجی به دیکشنری"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def connect_db():
    """اتصال به دیتابیس"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    return conn

# ============================================
# تبدیل تاریخ شروع سال ۱۴۰۵ به میلادی
# ============================================
start_date_1405 = jdatetime.date(1405, 1, 1).togregorian()
start_date_str = start_date_1405.strftime('%Y-%m-%d')

print("=" * 80)
print(f"📅 تاریخ شروع: {start_date_str}")
print("=" * 80)

# ============================================
# اتصال به دیتابیس
# ============================================
conn = connect_db()
cursor = conn.cursor()

# ============================================
# ۱. پیدا کردن invoice_number‌های تکراری در سال ۱۴۰۵ و بعد
# ============================================
duplicate_query = """
    SELECT invoice_number, COUNT(*) as count
    FROM DataAnalysis_invoice
    WHERE DATE(created_at) >= ?
    GROUP BY invoice_number
    HAVING COUNT(*) > 1
"""

cursor.execute(duplicate_query, (start_date_str,))
duplicate_invoices = cursor.fetchall()

# استخراج لیست شماره‌های تکراری
duplicate_numbers = [row['invoice_number'] for row in duplicate_invoices]

print(f"📊 تعداد invoice_number‌های تکراری در سال ۱۴۰۵ و بعد: {len(duplicate_numbers)}")
print("=" * 80)

if not duplicate_numbers:
    print("❌ هیچ فاکتور تکراری پیدا نشد!")
    conn.close()
    exit()

# نمایش لیست شماره‌های تکراری
print("\n🔢 لیست invoice_number‌های تکراری:")
for row in duplicate_invoices:
    print(f"   • شماره {row['invoice_number']}: {row['count']} بار تکرار شده")

# ============================================
# ۲. دریافت InvoiceItem‌های مربوط به این فاکتورها
# ============================================
placeholders = ','.join('?' * len(duplicate_numbers))

items_query = f"""
    SELECT 
        ii.id,
        ii.food_name,
        ii.price,
        ii.quantity,
        ii.total,
        i.invoice_number,
        i.name,
        i.created_at,
        i.id as invoice_id
    FROM DataAnalysis_invoiceitem ii
    JOIN DataAnalysis_invoice i ON ii.invoice_id = i.id
    WHERE i.invoice_number IN ({placeholders})
    AND DATE(i.created_at) >= ?
    ORDER BY i.invoice_number, i.created_at
"""

params = duplicate_numbers + [start_date_str]
cursor.execute(items_query, params)
duplicate_items = cursor.fetchall()

# ============================================
# ۳. نمایش آیتم‌های تکراری
# ============================================
print("\n📋 لیست آیتم‌های فاکتورهای تکراری:")
print("=" * 80)

for item in duplicate_items:
    print(f"""
📄 فاکتور شماره: {item['invoice_number']} (ID: {item['invoice_id']})
   🏷️  نام مشتری: {item['name']}
   📅 تاریخ: {item['created_at']}
   🍽️  نام غذا: {item['food_name']}
   💰 قیمت: {item['price']:,}
   🔢 تعداد: {item['quantity']}
   💵 مجموع: {item['total']:,}
   {'-' * 50}
""")

# ============================================
# ۴. حذف فاکتورهای تکراری (نگهداری جدیدترین)
# ============================================
print("\n" + "=" * 80)
print("🗑️  حذف فاکتورهای تکراری (نگهداری جدیدترین)")
print("=" * 80)

confirm = input("آیا مطمئن هستید که می‌خواهید فاکتورهای تکراری را حذف کنید؟ (yes/no): ")

if confirm.lower() == 'yes':
    # اتصال مجدد به دیتابیس برای انجام عملیات حذف
    conn_delete = sqlite3.connect(DB_PATH)
    cursor_delete = conn_delete.cursor()
    
    deleted_count = 0
    deleted_invoices = []
    
    for invoice_num in duplicate_numbers:
        # پیدا کردن همه فاکتورها با این شماره
        find_query = """
            SELECT id, created_at, name
            FROM DataAnalysis_invoice
            WHERE invoice_number = ?
            AND DATE(created_at) >= ?
            ORDER BY created_at ASC
        """
        
        cursor_delete.execute(find_query, (invoice_num, start_date_str))
        invoices = cursor_delete.fetchall()
        
        if len(invoices) > 1:
            # همه به جز آخرین (جدیدترین) را حذف کن
            for inv in invoices[:-1]:  # همه به جز آخرین
                invoice_id = inv[0]
                
                # ۱. ابتدا آیتم‌های این فاکتور را حذف کن
                delete_items_query = "DELETE FROM DataAnalysis_invoiceitem WHERE invoice_id = ?"
                cursor_delete.execute(delete_items_query, (invoice_id,))
                

                # ۳. خود فاکتور را حذف کن
                delete_invoice_query = "DELETE FROM DataAnalysis_invoice WHERE id = ?"
                cursor_delete.execute(delete_invoice_query, (invoice_id,))
                
                deleted_count += 1
                deleted_invoices.append({
                    'invoice_number': invoice_num,
                    'id': invoice_id,
                    'created_at': inv[1],
                    'name': inv[2]
                })
    
    # ذخیره تغییرات
    conn_delete.commit()
    
    # نمایش نتایج حذف
    print("\n✅ عملیات حذف با موفقیت انجام شد!")
    print(f"📊 تعداد کل فاکتورهای حذف شده: {deleted_count}")
    
    if deleted_invoices:
        print("\n📋 لیست فاکتورهای حذف شده:")
        print("=" * 80)
        for inv in deleted_invoices:
            print(f"""
🗑️  فاکتور شماره: {inv['invoice_number']}
   🆔 ID: {inv['id']}
   🏷️  مشتری: {inv['name']}
   📅 تاریخ: {inv['created_at']}
   {'-' * 50}
""")
    
    # بستن اتصال
    conn_delete.close()
    
else:
    print("❌ عملیات حذف لغو شد!")

# ============================================
# بستن اتصال اصلی
# ============================================
conn.close()
print("\n✅ عملیات با موفقیت انجام شد!")