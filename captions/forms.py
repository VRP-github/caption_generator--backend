from django import forms
from .models import CaptionRequest

class CaptionRequestForm(forms.ModelForm):
    class Meta:
        model = CaptionRequest
        fields = ['image', 'style', 'length', 'people', 'location', 'moment', 'sample_captions']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            }),
            'style': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'length': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'people': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@friend1, @friend2'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Paris, Central Park'
            }),
            'moment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'A highlight...'
            }),
            'sample_captions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'e.g.\nChasing sunsets.\nVibes on point.'
            }),
        }
