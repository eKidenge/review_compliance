from django import forms
from .models import PolicyAssessment, Approval, SubmissionAttempt
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML


class AssessmentForm(forms.ModelForm):
    """
    Form used by Reviewers to assess a case.
    Requires a category, rationale, and decision.
    """
    class Meta:
        model = PolicyAssessment
        fields = ['category', 'rationale', 'decision']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'rationale': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Provide specific evidence, quotes, and the exact policy that is being violated...'
            }),
            'decision': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # The <form> tag is already in the template
        self.helper.layout = Layout(
            Row(
                Column('category', css_class='form-group col-md-6 mb-0'),
                Column('decision', css_class='form-group col-md-6 mb-0'),
                css_class='form-row mb-3'
            ),
            'rationale',
            Submit('submit', 'Save Assessment', css_class='btn btn-warning w-100 mt-3')
        )

    def clean_rationale(self):
        rationale = self.cleaned_data.get('rationale')
        if len(rationale) < 20:
            raise forms.ValidationError("The rationale must be at least 20 characters long to be considered valid evidence.")
        return rationale


class ApprovalForm(forms.ModelForm):
    """
    Form used by Admins to approve an eligible case.
    """
    class Meta:
        model = Approval
        fields = ['rationale']
        widgets = {
            'rationale': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Reason for approval (e.g., Confirmed policy violation, evidence verified)...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'rationale',
            Submit('submit', 'Approve Case', css_class='btn btn-primary w-100 mt-3')
        )


class SubmissionForm(forms.ModelForm):
    """
    Form used by Submitters to record the receipt of a manual submission.
    """
    class Meta:
        model = SubmissionAttempt
        fields = ['method', 'receipt_reference', 'result']
        widgets = {
            'method': forms.TextInput(attrs={'placeholder': 'e.g., Google Business Profile Manual Report'}),
            'receipt_reference': forms.TextInput(attrs={'placeholder': 'e.g., Ticket #12345 or Confirmation ID'}),
            'result': forms.Select(choices=[
                ('', 'Select Result'),
                ('SUCCESS', 'Success - Report Received'),
                ('FAILED', 'Failed - Platform Rejected'),
                ('ERROR', 'Error - Technical Issue'),
            ]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('method', css_class='form-group col-md-6 mb-0'),
                Column('result', css_class='form-group col-md-6 mb-0'),
                css_class='form-row mb-3'
            ),
            'receipt_reference',
            Submit('submit', 'Record Receipt', css_class='btn btn-success w-100 mt-3')
        )

    def clean_receipt_reference(self):
        receipt = self.cleaned_data.get('receipt_reference')
        if len(receipt) < 5:
            raise forms.ValidationError("Please provide a valid receipt reference (at least 5 characters).")
        return receipt