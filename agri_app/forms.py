from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from .models import User

class AgriRegistrationForm(UserCreationForm):
    # Only show Farmer and Buyer to the public
    role = forms.ChoiceField(choices=[('Farmer', 'Farmer'), ('Buyer', 'Buyer')])

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("full_name", "email", "role", "phone_number","address")




from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['crop_name', 'category', 'price_per_unit', 'quantity_available', 'description', 'image']
        widgets = {
            'crop_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity_available': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

@login_required
def sell_product_view(request):
    if request.method == 'POST':
        # request.FILES is required for the image to upload!
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.farmer = request.user
            product.save()
            return redirect('market_list')
    else:
        form = ProductForm()
    return render(request, 'agri_app/sell_product.html', {'form': form})

from .models import Equipment  # Make sure to import the Equipment model!

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'description', 'rate_per_hour', 'rate_per_day', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mahindra Tractor, Spraying Drone'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the condition, features, and your location.'}),
            'rate_per_hour': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '₹ per hour (optional)'}),
            'rate_per_day': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '₹ per day (optional)'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


from django import forms
from .models import NewsUpdate
class NewsUpdateForm(forms.ModelForm):
    class Meta:
        model = NewsUpdate
        # Including 'image' so farmers can upload pictures!
        fields = ['title', 'content', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter the news title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your update here...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }