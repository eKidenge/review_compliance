from django import forms
from .models import ImportBatch
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class ImportBatchForm(forms.ModelForm):
    class Meta:
        model = ImportBatch
        fields = ['file']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1024 * 1024: # 10MB limit
                raise forms.ValidationError("File size cannot exceed 10MB.")
            if not file.name.endswith(('.csv', '.xlsx')):
                raise forms.ValidationError("Only .csv and .xlsx files are allowed.")
        return file