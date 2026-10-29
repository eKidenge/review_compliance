
from django import forms
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

from .models import PolicyAssessment, Approval, SubmissionAttempt


class AssessmentForm(forms.ModelForm):
    """
    Form used by reviewers to assess a review case.
    """

    CATEGORY_CHOICES = [
        ("", "Select Violation Category..."),
        ("SPAM", "Spam or Misleading Content"),
        ("FAKE_ENGAGEMENT", "Fake Engagement or Bot Activity"),
        ("CONFLICT_OF_INTEREST", "Conflict of Interest"),
        ("OFF_TOPIC", "Off-Topic or Irrelevant Content"),
        ("PROFANITY", "Profanity or Hate Speech"),
        ("PERSONAL_INFO", "Contains Personal Information"),
        ("ILLEGAL_CONTENT", "Illegal or Restricted Content"),
        ("OTHER", "Other Policy Violation"),
    ]

    DECISION_CHOICES = [
        ("", "Select Decision..."),
        ("ELIGIBLE", "Eligible - Violation Confirmed"),
        ("NOT_ELIGIBLE", "Not Eligible - No Violation Found"),
        (
            "INSUFFICIENT_EVIDENCE",
            "Insufficient Evidence - Needs More Proof",
        ),
    ]

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        widget=forms.Select(
            attrs={"class": "form-select rounded-0"}
        ),
        required=True,
    )

    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.Select(
            attrs={"class": "form-select rounded-0"}
        ),
        required=True,
    )

    class Meta:
        model = PolicyAssessment
        fields = ["category", "rationale", "decision"]
        widgets = {
            "rationale": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control rounded-0",
                    "placeholder": (
                        "Provide specific evidence, relevant quotes, "
                        "and the exact policy that may have been violated."
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Row(
                Column(
                    "category",
                    css_class="form-group col-md-6 mb-3",
                ),
                Column(
                    "decision",
                    css_class="form-group col-md-6 mb-3",
                ),
                css_class="form-row",
            ),
            "rationale",
            Submit(
                "submit",
                "Save Assessment",
                css_class=(
                    "btn btn-dark w-100 rounded-0 fw-bold "
                    "text-uppercase mt-3"
                ),
            ),
        )

    def clean_rationale(self):
        rationale = self.cleaned_data.get("rationale", "").strip()

        if len(rationale) < 20:
            raise ValidationError(
                "The rationale must be at least 20 characters long "
                "to provide meaningful evidence."
            )

        return rationale


class ApprovalForm(forms.ModelForm):
    """
    Form used by authorized administrators to approve or reject a case.

    The decision and approving user are assigned by the view,
    not submitted directly through this form.
    """

    class Meta:
        model = Approval
        fields = ["rationale"]
        widgets = {
            "rationale": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control rounded-0",
                    "placeholder": (
                        "Explain the decision and how the evidence "
                        "was verified."
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            "rationale",
            Submit(
                "submit",
                "Approve Case",
                css_class=(
                    "btn btn-dark w-100 rounded-0 fw-bold "
                    "text-uppercase mt-3"
                ),
            ),
        )

    def clean_rationale(self):
        rationale = self.cleaned_data.get("rationale", "").strip()

        if len(rationale) < 10:
            raise ValidationError(
                "Please provide a reason of at least 10 characters."
            )

        return rationale


class SubmissionForm(forms.ModelForm):
    """
    Form used to record a genuine, manually completed report submission.

    The submitting user, case, and submission timestamp should be
    assigned by the view.
    """

    class Meta:
        model = SubmissionAttempt
        fields = [
            "method",
            "receipt_reference",
            "result",
        ]
        widgets = {
            "method": forms.TextInput(
                attrs={
                    "class": "form-control rounded-0",
                    "placeholder": (
                        "e.g., Google Business Profile manual report"
                    ),
                }
            ),
            "receipt_reference": forms.TextInput(
                attrs={
                    "class": "form-control rounded-0",
                    "placeholder": (
                        "e.g., Genuine support ticket or confirmation ID"
                    ),
                }
            ),
            "result": forms.Select(
                attrs={"class": "form-select rounded-0"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Row(
                Column(
                    "method",
                    css_class="form-group col-md-6 mb-3",
                ),
                Column(
                    "result",
                    css_class="form-group col-md-6 mb-3",
                ),
                css_class="form-row",
            ),
            "receipt_reference",
            Submit(
                "submit",
                "Record Submission",
                css_class=(
                    "btn btn-dark w-100 rounded-0 fw-bold "
                    "text-uppercase mt-3"
                ),
            ),
        )

    def clean_method(self):
        method = self.cleaned_data.get("method", "").strip()

        if len(method) < 3:
            raise ValidationError(
                "Please provide a valid submission method."
            )

        return method

    def clean_receipt_reference(self):
        receipt = self.cleaned_data.get(
            "receipt_reference", ""
        ).strip()

        if len(receipt) < 5:
            raise ValidationError(
                "Please provide a valid receipt reference "
                "of at least 5 characters."
            )

        return receipt
