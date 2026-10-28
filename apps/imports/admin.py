from django.contrib import admin
from django.utils.html import format_html
from .models import ImportBatch, GoogleSheetSource


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    """
    Admin interface for CSV/XLSX file imports.
    """
    list_display = (
        'filename', 
        'uploaded_by', 
        'status_badge', 
        'valid_count', 
        'invalid_count', 
        'duplicate_count', 
        'imported_at'
    )
    list_filter = ('status', 'imported_at', 'uploaded_by')
    search_fields = ('filename', 'uploaded_by__username')
    readonly_fields = (
        'id',
        'imported_at', 
        'completed_at', 
        'row_count',
        'valid_count', 
        'invalid_count', 
        'duplicate_count',
        'invalid_urls_log',
        'error_log'
    )
    ordering = ('-imported_at',)
    list_per_page = 25

    fieldsets = (
        ('File Information', {
            'fields': ('id', 'filename', 'file', 'uploaded_by')
        }),
        ('Processing Status', {
            'fields': ('status', 'error_log')
        }),
        ('Metrics', {
            'fields': (
                'row_count', 
                'valid_count', 
                'invalid_count', 
                'duplicate_count',
                'invalid_urls_log'
            )
        }),
        ('Timestamps', {
            'fields': ('imported_at', 'completed_at')
        }),
    )

    def status_badge(self, obj):
        """Renders a colored badge for the status in the list view."""
        colors = {
            'PENDING': '#6c757d',      # Gray
            'PROCESSING': '#ffc107',   # Yellow
            'COMPLETED': '#198754',    # Green
            'FAILED': '#dc3545',       # Red
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display().upper()
        )
    status_badge.short_description = "Status"


@admin.register(GoogleSheetSource)
class GoogleSheetSourceAdmin(admin.ModelAdmin):
    """
    Admin interface for live Google Sheets syncing.
    """
    list_display = (
        'name', 
        'spreadsheet_id', 
        'sheet_name', 
        'sync_status_badge', 
        'last_synced_at'
    )
    list_filter = ('is_active', 'last_synced_at')
    search_fields = ('name', 'spreadsheet_id')
    readonly_fields = ('last_synced_at',)
    list_per_page = 25

    fieldsets = (
        ('Sheet Identification', {
            'fields': ('name', 'spreadsheet_id', 'sheet_name')
        }),
        ('Authentication', {
            'fields': ('credentials_json',),
            'description': "Paste the full Service Account JSON key from Google Cloud. <strong>Keep this secret.</strong>"
        }),
        ('Sync Control', {
            'fields': ('is_active', 'last_synced_at')
        }),
    )

    def sync_status_badge(self, obj):
        """Renders a colored badge for the sync status in the list view."""
        if not obj.last_synced_at:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold; font-size: 11px;">NEVER SYNCED</span>'
            )
        if not obj.is_active:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold; font-size: 11px;">PAUSED</span>'
            )
        return format_html(
            '<span style="background-color: #198754; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold; font-size: 11px;">ACTIVE</span>'
        )
    sync_status_badge.short_description = "Sync Status"

    def get_readonly_fields(self, request, obj=None):
        """
        Hide the credentials_json field from non-superusers.
        Only superusers can view the private key.
        """
        readonly = list(self.readonly_fields)
        if not request.user.is_superuser:
            readonly.append('credentials_json')
        return readonly

    def save_model(self, request, obj, form, change):
        """
        When a new sheet is added or updated, log the action.
        (The actual sync is handled by Celery Beat every 30 minutes.)
        """
        super().save_model(request, obj, form, change)