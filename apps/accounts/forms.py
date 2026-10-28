from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML

class CustomUserCreationForm(UserCreationForm):
    """
    Form for Admins to register new personnel and assign roles.
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # CRITICAL: Prevents double <form> tags
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('username', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('role', css_class='form-group col-md-6 mb-3'),
                Column('phone_number', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'password1',
            'password2',
            HTML('<hr class="my-4">'),
            Submit('submit', 'Register Personnel', css_class='btn btn-dark w-100 rounded-0 fw-bold text-uppercase', style='letter-spacing: 0.5px;')
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists in the registry.")
        return email


class CustomUserChangeForm(UserChangeForm):
    """
    Form for Admins to update existing personnel records.
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Clean up the default Django password field UI
        if 'password' in self.fields:
            self.fields['password'].help_text = '<span class="text-muted small">Raw passwords are not stored. Use the link above to reset.</span>'
            self.fields['password'].widget = forms.HiddenInput() # Hide the password field widget

        # Clean up the "Active" checkbox UI
        if 'is_active' in self.fields:
            self.fields['is_active'].label = "Account Active"
            self.fields['is_active'].help_text = "Uncheck to suspend access without deleting the record."
            self.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('username', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('role', css_class='form-group col-md-6 mb-3'),
                Column('phone_number', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            # Custom layout for the Active checkbox
            HTML('<div class="form-check mt-2 mb-3">'),
            'is_active',
            HTML('</div>'),
            HTML('<hr class="my-4">'),
            Submit('submit', 'Save Record Amendment', css_class='btn btn-dark w-100 rounded-0 fw-bold text-uppercase', style='letter-spacing: 0.5px;')
        )


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for users to update their own profile (they cannot change their role).
    """
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-3'),
                Column('phone_number', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            HTML('<hr class="my-4">'),
            Submit('submit', 'Submit Amendment Request', css_class='btn btn-dark w-100 rounded-0 fw-bold text-uppercase', style='letter-spacing: 0.5px;')
        )