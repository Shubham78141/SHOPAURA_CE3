from django.utils import timezone
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Product, Seller, SellerProductSubmission, Sale, Complaint

class SignUpForm(UserCreationForm):
    """Form for user registration"""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    """Form for user login"""
    username = forms.EmailField(widget=forms.TextInput(attrs={'autofocus': True}))

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProductForm(forms.ModelForm):
    """Form for product CRUD operations"""
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'original_price', 'discount_percentage',
            'stock', 'image_url', 'available_sizes', 'attributes', 'description'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'discount_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 0.01}),
        }

class ComplaintForm(forms.ModelForm):
    """Form for customer complaints"""
    class Meta:
        model = Complaint
        fields = ['name', 'email', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }

class ShippingForm(forms.Form):
    """Form for shipping details"""
    address = forms.CharField(max_length=200, required=True)
    city = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)
    zip_code = forms.CharField(max_length=20, required=True)
    country = forms.CharField(max_length=100, required=True)

class SellerSignUpForm(forms.ModelForm):
    """Form for seller registration"""
    class Meta:
        model = Seller
        fields = ['company_name']

class SellerProductSubmissionForm(forms.ModelForm):
    """Form for sellers to submit products"""
    class Meta:
        model = SellerProductSubmission
        fields = ['name', 'image_url', 'original_price', 'discount_percentage', 'stock', 'category', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'discount_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 0.01}),
        }

class SaleForm(forms.ModelForm):
    """Form for sale CRUD operations"""
    class Meta:
        model = Sale
        fields = ['name', 'discount_percentage', 'start_date', 'end_date', 'image_url', 'is_active']
        widgets = {
            'discount_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 0.01}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError("End date must be after start date.")
        if start_date and start_date > timezone.now() and cleaned_data.get('is_active'):
            self.add_error('start_date', "Cannot set sale as active if start date is in the future.")
        return cleaned_data