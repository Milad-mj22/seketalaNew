from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.template.response import TemplateResponse
from datetime import datetime, timedelta

from DataAnalysis.models import Invoice, InvoiceItem, FoodItems


# ============================================================
#  Inline آیتم‌های فاکتور
# ============================================================
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    fields = ('food_name', 'price', 'quantity', 'total')
    readonly_fields = ('total',)


# ============================================================
#  ادمین فاکتور + حذف بر اساس تاریخ
# ============================================================
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'name', 'phone', 'nahveh', 'created_at',
        'items_count', 'total_price_formatted', 'discount', 'peyk',
        'anaam', 'moshtarak', 'serv', 'pnum', 'shomare_pos',
        'mablagh_pos', 'hazine_peyk', 'naghdi', 'nonaghdi', 'mandeh',
    )

    list_filter = ('created_at', 'nahveh')
    search_fields = ('invoice_number', 'name', 'phone')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'          # ← نوار تاریخ بالای لیست
    readonly_fields = ('total_price',)
    inlines = [InvoiceItemInline]

    fieldsets = (
        ('اطلاعات فاکتور', {
            'fields': (
                'invoice_number', 'name', 'phone', 'nahveh', 'created_at',
                'discount', 'peyk', 'anaam', 'moshtarak', 'serv', 'pnum',
                'shomare_pos', 'mablagh_pos', 'hazine_peyk',
                'naghdi', 'nonaghdi', 'mandeh',
            )
        }),
        ('مبالغ', {'fields': ('total_price',)}),
    )

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'تعداد آیتم‌ها'

    def total_price_formatted(self, obj):
        return f"{obj.total_price:,} ریال"
    total_price_formatted.short_description = 'مبلغ کل'

    # ---------------- URL سفارشی ----------------
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'delete-by-date/',
                self.admin_site.admin_view(self.delete_by_date_view),
                name='DataAnalysis_invoice_delete_by_date',
            ),
        ]
        return custom + urls

    # ---------------- صفحه حذف بر اساس تاریخ ----------------
    def delete_by_date_view(self, request):
        target_date = None
        count = None
        deleted = False

        if request.method == 'POST':
            action = request.POST.get('action_type', 'preview')
            date_str = (request.POST.get('target_date') or '').strip()

            if not date_str:
                messages.error(request, 'لطفاً تاریخ را انتخاب کنید.')
            else:
                try:
                    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'فرمت تاریخ نامعتبر است.')
                    target_date = None

                if target_date:
                    start = timezone.make_aware(
                        datetime.combine(target_date, datetime.min.time())
                    )
                    end = start + timedelta(days=1)

                    qs = Invoice.objects.filter(
                        created_at__gte=start, created_at__lt=end
                    )
                    count = qs.count()

                    if action == 'delete':
                        if count == 0:
                            messages.warning(
                                request,
                                f'هیچ فاکتوری در تاریخ {target_date} یافت نشد.'
                            )
                        else:
                            qs.delete()
                            messages.success(
                                request,
                                f'✅ {count} فاکتور مربوط به {target_date} حذف شد.'
                            )
                            deleted = True
                            target_date = None
                            count = None

        # ---------------- ساخت HTML داخل خود ادمین ----------------
        csrf = request.META.get('CSRF_COOKIE', '')

        result_box = ''
        if count is not None and target_date is not None:
            if count == 0:
                result_box = format_html(
                    '<div style="background:#fff3cd; color:#856404; padding:12px 16px;'
                    ' border-radius:8px; margin:15px 0;">'
                    'در تاریخ <b>{}</b> هیچ فاکتوری وجود ندارد.</div>',
                    str(target_date),
                )
            else:
                result_box = format_html(
                    '<div style="background:#e3f2fd; color:#0d47a1; padding:12px 16px;'
                    ' border-radius:8px; margin:15px 0;">'
                    'در تاریخ <b>{}</b> تعداد <b>{}</b> فاکتور پیدا شد. '
                    'برای حذف همه، دکمه قرمز زیر را بزنید.</div>',
                    str(target_date), count,
                )

        delete_button = ''
        if count and count > 0:
            delete_button = format_html(
                '<form method="post" style="display:inline;">'
                '<input type="hidden" name="csrfmiddlewaretoken" value="{}">'
                '<input type="hidden" name="target_date" value="{}">'
                '<input type="hidden" name="action_type" value="delete">'
                '<button type="submit" onclick="return confirm(\'مطمئنی؟ تمام فاکتورهای این روز حذف میشوند.\');"'
                ' style="background:#b71c1c; color:#fff; padding:10px 22px;'
                ' border:none; border-radius:8px; cursor:pointer; font-size:14px;">'
                '🗑 حذف همه فاکتورهای این روز</button></form>',
                csrf, str(target_date),
            )

        form_html = format_html('''
            <div style="max-width:640px; background:#fff; padding:24px;
                        border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,.08);
                        margin-top:15px;">
                <h2 style="margin-top:0;">🗑 حذف فاکتورهای یک روز خاص</h2>
                <p style="color:#555;">تاریخ مورد نظر را انتخاب کنید (میلادی):</p>
                <form method="post">
                    <input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">
                    <input type="hidden" name="action_type" value="preview">
                    <input type="date" name="target_date" required value="{val}"
                           style="padding:10px; font-size:15px; border-radius:8px;
                                  border:1px solid #ccc; width:100%;">
                    <button type="submit"
                            style="margin-top:15px; background:#0d47a1; color:#fff;
                                   padding:10px 22px; border:none; border-radius:8px;
                                   cursor:pointer; font-size:14px;">
                        🔍 نمایش فاکتورهای این روز
                    </button>
                </form>
                {result}
                <div style="margin-top:15px;">{delbtn}</div>
                <p style="margin-top:25px;">
                    <a href="../" style="color:#0d47a1;">← بازگشت به لیست فاکتورها</a>
                </p>
            </div>
        ''', csrf=csrf,
             val=(str(target_date) if target_date else ''),
             result=mark_safe(result_box),
             delbtn=mark_safe(delete_button))

        context = {
            **self.admin_site.each_context(request),
            'title': 'حذف فاکتورهای یک روز',
            'opts': self.model._meta,
            'form_html': form_html,
        }
        return TemplateResponse(
            request,
            'admin/DataAnalysis/invoice/delete_by_date.html',
            context,
        )


# ============================================================
#  ادمین آیتم‌های فاکتور
# ============================================================
@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        'invoice', 'food_name', 'price_formatted', 'quantity', 'total_formatted',
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


# ============================================================
#  ادمین FoodItems
# ============================================================
@admin.register(FoodItems)
class FoodItemsAdmin(admin.ModelAdmin):
    list_display = (
        "id", "food_name", "sepdar_code_display",
        "foodsoft_code_display", "status_badge",
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

    @admin.action(description="پاک کردن کد سپیدار موارد انتخاب‌شده")
    def clear_sepdar_code(self, request, queryset):
        count = queryset.update(sepdar_code=None)
        self.message_user(request, f"کد سپیدار {count} مورد پاک شد.")

    @admin.action(description="پاک کردن کد فودسافت موارد انتخاب‌شده")
    def clear_foodsoft_code(self, request, queryset):
        count = queryset.update(foodsoft_code=None)
        self.message_user(request, f"کد فودسافت {count} مورد پاک شد.")