# forms.py
from django import forms

class DBUploadForm(forms.Form):
    file = forms.FileField(label="Upload your SQLite DB file (.db)")






# your_app/forms.py
from django import forms
from .models import FoodItems


class FoodItemsForm(forms.ModelForm):
    class Meta:
        model = FoodItems
        fields = ['food_name', 'foodsoft_code', 'sepdar_code']
        widgets = {
            'food_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام غذا را وارد کنید',
                'required': True,
            }),
            'foodsoft_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'کد فودسافت (اختیاری)',
            }),
            'sepdar_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'کد سپیدار (اختیاری)',
            }),
        }
        labels = {
            'food_name': 'نام غذا',
            'foodsoft_code': 'کد فودسافت',
            'sepdar_code': 'کد سپیدار',
        }
    
    def clean_food_name(self):
        """اعتبارسنجی نام غذا"""
        food_name = self.cleaned_data.get('food_name', '').strip()
        if not food_name:
            raise forms.ValidationError('نام غذا الزامی است')
        return food_name
    
    def clean_foodsoft_code(self):
        """اعتبارسنجی کد فودسافت (یکتا)"""
        code = self.cleaned_data.get('foodsoft_code', '').strip() or None
        
        if code:
            qs = FoodItems.objects.filter(foodsoft_code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('این کد فودسافت قبلاً استفاده شده است')
        
        return code
    
    def clean_sepdar_code(self):
        """اعتبارسنجی کد سپیدار"""
        code = self.cleaned_data.get('sepdar_code', '').strip() or None
        return code


class FoodItemsSearchForm(forms.Form):
    """فرم جستجو"""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'جستجو بر اساس نام یا کد...',
        })
    )