from django import forms
from .models import Cliente

class ClienteLoginForm(forms.Form):
    nome = forms.CharField(max_length=100, required=True, label='Nome')
    whatsapp = forms.CharField(max_length=15, required=True, label='WhatsApp')

    def clean_whatsapp(self):
        whatsapp = self.cleaned_data['whatsapp']
        return ''.join(filter(str.isdigit, whatsapp)) #remove simbolos e espacos