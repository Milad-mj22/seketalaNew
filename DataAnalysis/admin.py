
from django.contrib import admin

from DataAnalysis.models import Invoice,InvoiceItem

# Register your models here.


from django.contrib import admin
from django.db.models import Sum
from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    fields = ('food_name', 'price', 'quantity', 'total')
    readonly_fields = ('total',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number',
        'name',
        'phone',
        'nahveh',
        'created_at',
        'items_count',
        'total_price_formatted',
        'discount',
        'peyk',
        'anaam',
        'moshtarak',
        'serv',
        'pnum',
        'shomare_pos',
        'mablagh_pos',
        'hazine_peyk',
        'naghdi',
        'nonaghdi',
        'mandeh',

    )

    list_filter = ('created_at',)
    search_fields = ('invoice_number', 'name', 'phone')
    ordering = ('-created_at',)

    readonly_fields = ('total_price',)
    inlines = [InvoiceItemInline]

    fieldsets = (
        ('اطلاعات فاکتور', {
            'fields': (
                'invoice_number',
                'name',
                'phone',
                'nahveh',
                'created_at',
                'discount',
                'peyk',
                'anaam',
                        'moshtarak',
        'serv',
        'pnum',
        'shomare_pos',
        'mablagh_pos',
        'hazine_peyk',
        'naghdi',
        'nonaghdi',
        'mandeh',

            )
        }),
        ('مبالغ', {
            'fields': ('total_price',),
        }),
    )

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'تعداد آیتم‌ها'

    def total_price_formatted(self, obj):
        return f"{obj.total_price:,} ریال"
    total_price_formatted.short_description = 'مبلغ کل'


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        'invoice',
        'food_name',
        'price_formatted',
        'quantity',
        'total_formatted',
    )

    list_filter = ('invoice',)
    search_fields = ('food_name',)
    autocomplete_fields = ('invoice',)

    def price_formatted(self, obj):
        return f"{obj.price:,} ریال"
    price_formatted.short_description = 'قیمت واحد'

    def total_formatted(self, obj):
        return f"{obj.total:,} ریال"
    total_formatted.short_description = 'جمع کل'




from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count

from .models import FoodItems
from django.contrib import admin
from django.utils.html import format_html, mark_safe

from .models import FoodItems


@admin.register(FoodItems)
class FoodItemsAdmin(BaseFoodItemsAdmin := admin.ModelAdmin):
    list_display = (
        "id",
        "food_name",
        "sepdar_code_display",
        "foodsoft_code_display",
        "status_badge",
    )
    list_display_links = ("id", "food_name")
    search_fields = ("food_name", "sepdar_code", "foodsoft_code")
    search_help_text = "جستجو بر اساس نام غذا، کد سپیدار یا کد فودسافت"
    ordering = ("food_name",)
    list_per_page = 50
    list_max_show_all = 200

    fieldsets = (
        ("اطلاعات اصلی", {"fields": ("food_name",)}),
        ("کدها", {
            "fields": ("sepdar_code", "foodsoft_code"),
            "description": "کد سپیدار و کد فودسافت می‌توانند خالی باشند.",
        }),
    )

    actions = ("clear_sepdar_code", "clear_foodsoft_code")

    # ---------- متدهای نمایشی ----------
    @admin.display(description="کد سپیدار", ordering="sepdar_code")
    def sepdar_code_display(self, obj):
        if obj.sepdar_code:
            return format_html(
                '<span style="background:#e8f5e9; color:#1b5e20; '
                'padding:2px 8px; border-radius:6px; font-family:monospace;">{}</span>',
                obj.sepdar_code,
            )
        return mark_safe('<span style="color:#b71c1c;">—</span>')

    @admin.display(description="کد فودسافت", ordering="foodsoft_code")
    def foodsoft_code_display(self, obj):
        if obj.foodsoft_code:
            return format_html(
                '<span style="background:#e3f2fd; color:#0d47a1; '
                'padding:2px 8px; border-radius:6px; font-family:monospace;">{}</span>',
                obj.foodsoft_code,
            )
        return mark_safe('<span style="color:#b71c1c;">—</span>')

    @admin.display(description="وضعیت")
    def status_badge(self, obj):
        has_sep = bool(obj.sepdar_code)
        has_soft = bool(obj.foodsoft_code)

        if has_sep and has_soft:
            return mark_safe(
                '<span style="background:#c8e6c9; color:#1b5e20; '
                'padding:3px 10px; border-radius:12px; font-size:11px;">'
                '✓ کامل</span>'
            )
        if has_sep or has_soft:
            return mark_safe(
                '<span style="background:#fff9c4; color:#f57f17; '
                'padding:3px 10px; border-radius:12px; font-size:11px;">'
                '◐ ناقص</span>'
            )
        return mark_safe(
            '<span style="background:#ffcdd2; color:#b71c1c; '
            'padding:3px 10px; border-radius:12px; font-size:11px;">'
            '✗ بدون کد</span>'
        )

    # ---------- اکشن‌ها ----------
    @admin.action(description="پاک کردن کد سپیدار موارد انتخاب‌شده")
    def clear_sepdar_code(self, request, queryset):
        count = queryset.update(sepdar_code=None)
        self.message_user(request, f"کد سپیدار {count} مورد پاک شد.")

    @admin.action(description="پاک کردن کد فودسافت موارد انتخاب‌شده")
    def clear_foodsoft_code(self, request, queryset):
        count = queryset.update(foodsoft_code=None)
        self.message_user(request, f"کد فودسافت {count} مورد پاک شد.")