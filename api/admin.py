import secrets

from django.contrib import admin

from api.models import SMS, BankAccount

# Register your models here.


admin.site.register(SMS)


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_number', 'bank_name', 'created_at')
    search_fields = ('name', 'account_number', 'bank_name')




# api/admin.py
from django.contrib import admin
from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'key_preview', 'is_active', 'created_at']
    readonly_fields = ['key', 'created_at']
    
    def key_preview(self, obj):
        return f"{obj.key[:12]}..."
    key_preview.short_description = 'Key'
    
    def save_model(self, request, obj, form, change):
        if not obj.key:
            obj.key = secrets.token_urlsafe(32)
        super().save_model(request, obj, form, change)