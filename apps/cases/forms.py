from django import forms
from .models import PolicyAssessment, Approval, SubmissionAttempt
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML


class AssessmentForm(forms.ModelForm):
    """
    Form used by Reviewers to assess a case.
    """
    # Define the categories of policy violations
    CATEGORY_CHOICES = [
        ('', 'Select Violation Category...'),
        ('SPAM', 'Spam or Misleading Content'),
        ('FAKE_ENGAGEMENT', 'Fake Engagement or Bot Activity'),
        ('CONFLICT_OF_INTEREST', 'Conflict of Interest'),
        ('OFF_TOPIC', 'Off-Topic or Irrelevant Content'),
        ('PROFANITY', 'Profanity or Hate Speech'),
        ('PERSONAL_INFO', 'Contains Personal Information'),
        ('ILLEGAL_CONTENT', 'Illegal or Restricted Content'),
        ('OTHER', 'Other Policy Violation'),
    ]

    # Define the decisions a reviewer can make
    DECISION_CHOICES = [
        ('', 'Select Decision...'),
        ('ELIGIBLE', 'Eligible - Violation Confirmed'),
        ('NOT_ELIGIBLE', 'Not Eligible - No Violation Found'),
        ('INSUFFICIENT_EVIDENCE', 'Insufficient Evidence - Needs More Proof'),
    ]

    # Override the model fields to force them to be dropdowns
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES, 
        widget=forms.Select(attrs={'class': 'form-select rounded-0'})
    )
    decision = forms.ChoiceField(
        choices=DECISION_CHOICES, 
        widget=forms.Select(attrs={'class': 'form-select rounded-0'})
    )

    class Meta:
        model = PolicyAssessment
        fields = ['category', 'rationale', 'decision']
        widgets = {
            'rationale': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'form-control rounded-0',
                'placeholder': 'Provide specific evidence, quotes, and the exact policy that is being violated...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False 
        self.helper.layout = Layout(
            Row(
                Column('category', css_class='form-group col-md-6 mb-3'),
                Column('decision', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'rationale',
            Submit('submit', 'Save Assessment', css_class='btn btn-dark w-100 rounded-0 fw-bold text-uppercase mt-3', style='letter-spacing: 0.5px;')
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
                'class': 'form-control rounded-0',
                'placeholder': 'Reason for approval (e.g., Confirmed policy violation, evidence verified)...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'rationale',
            Submit('submit', 'Approve Case', css_class='btn btn-dark w-100 rounded-0 fw-bold text-uppercase mt-3', style='letter-spacing: 0.5px;')
        )


class SubmissionForm(forms.ModelForm):
    """
    Form used by Submitters to record the receipt of a manual submission.
    """
    class Meta:
        model = SubmissionAttempt
        fields = ['method', 'receipt_reference', 'result']
        widgets = {
            'method': forms.TextInput(attrs={'class': 'form-control rounded-0', 'placeholder': 'e.g., Google Business Profile Manual Report'}),
            'receipt_reference': forms.TextInput(attrs={'class': 'form-control rounded-0', 'placeholder': 'e.g., Ticket #12345 or Confirmation ID'}),
            'result': forms.Select(attrs={'class': 'form-select rounded-0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('method', css_class='form-group col-md-6 mb-3'),
                Column('result', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'receipt_reference',
            Submit('submit', 'Record Receipt', css_class='btn btn-dark w-100 rounded-0 fw-bold text-uppercase mt-3', style='letter-spacing: 0.5px;')
        )

    def clean_receipt_reference(self):
        receipt = self.cleaned_data.get('receipt_reference')
        if len(receipt) < 5:
            raise forms.ValidationError("Please provide a valid receipt reference (at least 5 characters).")
        return receipt