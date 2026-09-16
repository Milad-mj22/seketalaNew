from django.db import models
from django.contrib.auth.models import User

# Create your models here.




class SMS(models.Model):
    sender = models.CharField(max_length=50)
    message = models.TextField()
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} - {self.received_at}"
    



class BankAccount(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام حساب")
    account_number = models.CharField(max_length=50, unique=True, verbose_name="شماره حساب")
    bank_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="نام بانک")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")


    def __str__(self):
        return f"{self.name} - {self.account_number}"
    





class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('system', 'System'), ('assistant', 'Assistant')])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(ChatSession, on_delete=models.SET_NULL, null=True, blank=True)
    order_summary = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'در انتظار'),
        ('confirmed', 'تأیید شده'),
        ('preparing', 'در حال آماده‌سازی'),
        ('ready', 'آماده'),
        ('delivered', 'تحویل داده شده'),
        ('cancelled', 'لغو شده')
    ], default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)







# seketalamanager/api/models.py
import secrets
from django.db import models


class APIKey(models.Model):
    key = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.key[:8]}..."
    
    @classmethod
    def generate(cls, name):
        """ساخت یک API Key جدید"""
        return cls.objects.create(
            key=secrets.token_urlsafe(32),
            name=name
        )







class LowStockReport(models.Model):
    """ذخیره کل داده ورودی به صورت JSON"""
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('reviewed', 'بررسی شده'),
        ('resolved', 'حل شده'),
    ]
    
    # کل داده JSON که از سپیدار میاد
    data = models.JSONField(
        help_text='کل داده ورودی به صورت JSON',
        verbose_name='داده JSON'
    )
    
    # فیلدهای کمکی برای جستجو و فیلتر سریع
    source = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='منبع'
    )
    total_items = models.IntegerField(
        default=0,
        verbose_name='کل اقلام'
    )
    low_stock_count = models.IntegerField(
        default=0,
        verbose_name='تعداد اقلام کمبود'
    )
    
    # فیلدهای محاسباتی برای گزارش‌گیری سریع‌تر
    shortage_percent = models.FloatField(
        default=0,
        verbose_name='درصد کمبود',
        help_text='درصد اقلامی که کمبود دارند نسبت به کل'
    )
    total_shortage = models.FloatField(
        default=0,
        verbose_name='مجموع کمبود',
        help_text='مجموع کمبود همه اقلام'
    )
    critical_count = models.IntegerField(
        default=0,
        verbose_name='تعداد اقلام بحرانی',
        help_text='اقلام با وضعیت danger'
    )
    warning_count = models.IntegerField(
        default=0,
        verbose_name='تعداد اقلام هشدار',
        help_text='اقلام با وضعیت warning'
    )
    
    # اطلاعات دریافت
    received_from_key = models.ForeignKey(
        APIKey, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reports',
        verbose_name='دریافت شده از'
    )
    received_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ دریافت',
        db_index=True
    )
    sender_timestamp = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='زمان ارسال مبدأ'
    )
    
    # اطلاعات IP و User Agent برای امنیت
    sender_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name='IP فرستنده'
    )
    user_agent = models.CharField(
        max_length=500, 
        blank=True,
        verbose_name='User Agent'
    )
    
    # وضعیت بررسی
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت',
        db_index=True
    )
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت'
    )
    
    # آیا این گزارش جدید است؟ (برای notification)
    is_read = models.BooleanField(
        default=False,
        verbose_name='خوانده شده',
        db_index=True
    )
    
    class Meta:
        ordering = ['-received_at']
        verbose_name = 'گزارش کمبود موجودی'
        verbose_name_plural = 'گزارش‌های کمبود موجودی'
        indexes = [
            models.Index(fields=['-received_at']),
            models.Index(fields=['status', '-received_at']),
            models.Index(fields=['is_read', '-received_at']),
        ]
    
    def __str__(self):
        return (
            f"گزارش {self.received_at.strftime('%Y/%m/%d %H:%M')} - "
            f"{self.low_stock_count} قلم"
        )
    
    def save(self, *args, **kwargs):
        """محاسبه خودکار فیلدهای آماری قبل از ذخیره"""
        if self.data:
            items = self.data.get('low_stock_items', [])
            
            # محاسبه مجموع کمبود
            self.total_shortage = sum(
                float(item.get('shortage', 0)) for item in items
            )
            
            # شمارش بحرانی و هشدار
            self.critical_count = sum(
                1 for item in items if item.get('status') == 'danger'
            )
            self.warning_count = sum(
                1 for item in items if item.get('status') == 'warning'
            )
            
            # محاسبه درصد کمبود
            if self.total_items > 0:
                self.shortage_percent = round(
                    (self.low_stock_count / self.total_items) * 100, 2
                )
            else:
                self.shortage_percent = 0
        
        super().save(*args, **kwargs)
    
    @property
    def items(self):
        """دسترسی سریع به آیتم‌ها از JSON"""
        if not self.data:
            return []
        items = self.data.get('low_stock_items', [])
        # مرتب‌سازی بر اساس کمبود
        return sorted(items, key=lambda x: x.get('shortage', 0), reverse=True)
    
    @property
    def critical_items(self):
        """فقط اقلام بحرانی"""
        return [item for item in self.items if item.get('status') == 'danger']
    
    @property
    def warning_items(self):
        """فقط اقلام هشدار"""
        return [item for item in self.items if item.get('status') == 'warning']
    
    def mark_as_read(self):
        """علامت‌گذاری به عنوان خوانده شده"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
    """ذخیره کل داده ورودی به صورت JSON"""
    
    # کل داده JSON که از سپیدار میاد
    data = models.JSONField(help_text='کل داده ورودی به صورت JSON')
    
    # فیلدهای کمکی برای جستجو و فیلتر سریع
    source = models.CharField(max_length=100, blank=True)
    total_items = models.IntegerField(default=0)
    low_stock_count = models.IntegerField(default=0)
    
    # اطلاعات دریافت
    received_from_key = models.ForeignKey(
        APIKey, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    received_at = models.DateTimeField(auto_now_add=True)
    sender_timestamp = models.CharField(max_length=100, blank=True)  # timestamp ارسالی از مبدأ
    
    class Meta:
        ordering = ['-received_at']
        verbose_name = 'گزارش کمبود موجودی'
        verbose_name_plural = 'گزارش‌های کمبود موجودی'
    
    def __str__(self):
        return f"گزارش {self.received_at.strftime('%Y/%m/%d %H:%M')} - {self.low_stock_count} قلم"