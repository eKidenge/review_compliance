import csv
import openpyxl
from urllib.parse import urlparse
from celery import shared_task
from .models import ImportBatch
from apps.cases.models import ReviewCase


@shared_task(bind=True, max_retries=3)
def process_import_batch_task(self, batch_id):
    try:
        batch = ImportBatch.objects.get(id=batch_id)
        batch.status = 'PROCESSING'
        batch.save()

        file_path = batch.file.path
        raw_urls = []

        # Parse based on file type
        if file_path.endswith('.csv'):
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader, None) # Skip header
                for row in reader:
                    if row and row[0].strip():
                        raw_urls.append(row[0].strip())
                        
        elif file_path.endswith('.xlsx'):
            wb = openpyxl.load_workbook(file_path, read_only=True)
            sheet = wb.active
            # Start from row 1 since your file doesn't have a header
            for row in sheet.iter_rows(min_row=1, values_only=True):
                if row and row[0]:
                    raw_urls.append(str(row[0]).strip())

        # --- VALIDATION & DEDUPLICATION ---
        
        processed_urls = set()
        db_urls = set(ReviewCase.objects.values_list('canonical_url', flat=True))

        cases_to_create = []
        dup_count = 0
        inv_count = 0

        # List of allowed Google domain formats
        allowed_domains = ['google.com', 'goo.gl', 'maps.app.goo.gl', 'maps.google.com']

        for url in raw_urls:
            # Skip obvious non-URL rows (like "# Reviewer Link" or blank lines)
            if not url.startswith('http'):
                inv_count += 1
                continue

            parsed = urlparse(url)
            
            # Check if the domain matches the allowed list
            is_valid_domain = any(domain in parsed.netloc for domain in allowed_domains)
            
            if not (parsed.scheme in ['http', 'https'] and is_valid_domain):
                inv_count += 1
                continue
            
            # Skip duplicates (both in this batch and in the database)
            if url in processed_urls or url in db_urls:
                dup_count += 1
                continue

            processed_urls.add(url)
            cases_to_create.append(ReviewCase(
                canonical_url=url,
                original_url=url,
                source_batch=batch,
                status='NEEDS_TRIAGE'
            ))

        # Bulk create for performance (single SQL query)
        ReviewCase.objects.bulk_create(cases_to_create)

        # Update Batch Stats
        batch.row_count = len(raw_urls)
        batch.valid_count = len(cases_to_create)
        batch.invalid_count = inv_count
        batch.duplicate_count = dup_count
        batch.status = 'COMPLETED'
        batch.save()

    except Exception as exc:
        batch.status = 'FAILED'
        batch.error_log = str(exc)
        batch.save()
        raise self.retry(exc=exc, countdown=60)