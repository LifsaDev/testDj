from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Customer

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')
    phone_number = forms.CharField(max_length=20, help_text='Required')

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Ex : client1'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'minimum 8 lettres'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'meme mot de pass'})
        self.fields['phone_number'].widget.attrs.update({'placeholder': 'Ex: +226 78569632'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Ex: salif@gmail.com'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        customer = Customer.objects.create(
            user=user,
            username=user.username,
            email=user.email,
            phone_number=self.cleaned_data['phone_number']
        )
        return user
