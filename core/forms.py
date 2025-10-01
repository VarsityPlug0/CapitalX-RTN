from django import forms
from .models import Deposit

class VoucherDepositForm(forms.ModelForm):
    class Meta:
        model = Deposit
        fields = ['amount', 'voucher_code', 'voucher_image']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
            'voucher_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter voucher code'}),
            'voucher_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }