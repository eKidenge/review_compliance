from django import forms
from .models import PolicyAssessment, Approval, SubmissionAttempt

class AssessmentForm(forms.ModelForm):
    class Meta:
        model = PolicyAssessment
        fields = ['category', 'rationale', 'decision']
        widgets = {
            'rationale': forms.Textarea(attrs={'rows': 4}),
        }

class ApprovalForm(forms.ModelForm):
    class Meta:
        model = Approval
        fields = ['rationale']
        widgets = {
            'rationale': forms.Textarea(attrs={'rows': 3}),
        }

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = SubmissionAttempt
        fields = ['method', 'receipt_reference', 'result']