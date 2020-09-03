from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget



PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('p', 'PayPal')
)


class CheckoutForm(forms.Form):
    street_address =  forms.CharField(max_length=300, required=True, widget=forms.TextInput(attrs={
        'placeholder' : '1234 Main St' 
    }))
    apartment_address = forms.CharField(max_length=300, required=False, widget=forms.TextInput(attrs={
        'placeholder' : 'Apartment or suite'
    }))
    country = CountryField(blank_label='(Choose...)').formfield(widget=CountrySelectWidget(attrs={
        'class' : 'custom-select d-block w-100',
    }))
    zip = forms.CharField(widget=forms.TextInput(attrs={
        'class' : 'form-control'
    }))
    same_shipping_address = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    save_info = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    payment_options = forms.ChoiceField(widget=forms.RadioSelect,choices=PAYMENT_CHOICES)