from django import forms
from .models import ImportBatch
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

class ImportBatchForm(forms.ModelForm):
    class Meta:
        model = ImportBatch
        fields = ['file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        # CRITICAL: Prevent Crispy from rendering a <form> tag since our HTML already has one
        self.helper.form_tag = False 
        self.helper.layout = Layout(
            Field('file', css_class='form-control-lg') # Make the file input larger
        )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1024 * 1024: # 10MB limit
                raise forms.ValidationError("File size cannot exceed 10MB.")
            if not file.name.endswith(('.csv', '.xlsx')):
                raise forms.ValidationError("Only .csv and .xlsx files are allowed.")
        return file