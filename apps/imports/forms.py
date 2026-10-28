from django import forms
from .models import ImportBatch, GoogleSheetSource
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Row, Column, Submit, HTML


class ImportBatchForm(forms.ModelForm):
    """
    Form for uploading CSV/XLSX files for bulk ingestion.
    """
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


class GoogleSheetSourceForm(forms.ModelForm):
    """
    Form for Admins to configure a live Google Sheet sync source.
    This is a complex form because it handles a JSON credential blob.
    """
    class Meta:
        model = GoogleSheetSource
        fields = ['name', 'spreadsheet_id', 'sheet_name', 'credentials_json', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control rounded-0',
                'placeholder': 'e.g., Client A - Main Google Sheet'
            }),
            'spreadsheet_id': forms.TextInput(attrs={
                'class': 'form-control rounded-0',
                'placeholder': 'The long ID between /d/ and /edit in the URL'
            }),
            'sheet_name': forms.TextInput(attrs={
                'class': 'form-control rounded-0',
                'placeholder': 'Sheet1'
            }),
            'credentials_json': forms.Textarea(attrs={
                'class': 'form-control rounded-0 font-monospace',
                'rows': 8,
                'placeholder': 'Paste the full Service Account JSON key from Google Cloud here...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('sheet_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'spreadsheet_id',
            'credentials_json',
            HTML('<div class="form-check mb-4">'),
            'is_active',
            HTML('</div>'),
            HTML('<hr class="my-4">'),
            Submit('submit', 'Save Google Sheet Source', css_class='btn btn-dark w-100 rounded-0 fw-bold text-uppercase', style='letter-spacing: 0.5px;')
        )

    def clean_credentials_json(self):
        """Ensure the JSON is valid before saving."""
        import json
        data = self.cleaned_data.get('credentials_json')
        if isinstance(data, str):
            try:
                json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format. Please paste the valid Service Account key.")
        elif isinstance(data, dict):
            # If it's already a dict (e.g., set by admin), it's valid.
            pass
        return data

    def clean_spreadsheet_id(self):
        """Extract the ID if the user pastes the full URL."""
        sid = self.cleaned_data.get('spreadsheet_id')
        if sid and 'docs.google.com' in sid:
            try:
                # Extract ID from URL: https://docs.google.com/spreadsheets/d/[ID]/edit
                sid = sid.split('/d/')[1].split('/')[0]
            except IndexError:
                raise forms.ValidationError("Could not extract spreadsheet ID from the URL. Please paste the ID directly.")
        return sid