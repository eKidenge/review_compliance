from django.contrib import admin
from .models import ReviewCase, PolicyAssessment, Approval, SubmissionAttempt, Outcome

class PolicyAssessmentInline(admin.StackedInline):
    model = PolicyAssessment
    extra = 0
    can_delete = False

class ApprovalInline(admin.StackedInline):
    model = Approval
    extra = 0
    can_delete = False

@admin.register(ReviewCase)
class ReviewCaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'canonical_url', 'business_label', 'status', 'created_at')
    list_filter = ('status', 'source_batch')
    search_fields = ('canonical_url', 'business_label')
    inlines = [PolicyAssessmentInline, ApprovalInline]
    actions = ['mark_as_removed']

    @admin.action(description='Mark selected cases as Removed')
    def mark_as_removed(self, request, queryset):
        queryset.update(status='REMOVED')

admin.site.register(SubmissionAttempt)
admin.site.register(Outcome)