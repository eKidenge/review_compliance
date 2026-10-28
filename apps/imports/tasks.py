import csv
import logging
import openpyxl
import gspread

from urllib.parse import urlparse

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from google.oauth2.service_account import Credentials

from .models import ImportBatch, GoogleSheetSource
from apps.cases.models import ReviewCase

logger = logging.getLogger(__name__)

ALLOWED_DOMAINS = {
    "google.com",
    "maps.google.com",
    "maps.app.goo.gl",
    "goo.gl",
}


def is_valid_google_url(url: str) -> bool:
    """
    Validate Google review URL.
    """
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        host = parsed.netloc.lower()

        return any(
            host == domain or host.endswith(f".{domain}")
            for domain in ALLOWED_DOMAINS
        )

    except Exception:
        return False


def load_urls_from_file(file_path):
    """
    Extract URLs from CSV or XLSX.
    """
    urls = []

    if file_path.endswith(".csv"):
        with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if not row:
                    continue
                value = str(row[0]).strip()
                if value:
                    urls.append(value)

    elif file_path.endswith(".xlsx"):
        workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet = workbook.active
        for row in sheet.iter_rows(min_row=1, values_only=True):
            if not row:
                continue
            value = row[0]
            if value:
                urls.append(str(value).strip())
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    return urls


@shared_task(bind=True, max_retries=3)
def process_import_batch_task(self, batch_id):
    batch = None

    try:
        batch = ImportBatch.objects.get(id=batch_id)

        # NEW: Set source_type based on the file extension
        if batch.file and batch.file.path.endswith(".xlsx"):
            batch.source_type = "XLSX"
        else:
            batch.source_type = "CSV"

        batch.status = "PROCESSING"
        batch.error_log = ""
        batch.save(update_fields=["status", "error_log", "source_type"])

        logger.info("Processing batch %s", batch_id)

        raw_urls = load_urls_from_file(batch.file.path)

        existing_urls = set(
            ReviewCase.objects.values_list("canonical_url", flat=True)
        )

        processed_urls = set()
        invalid_urls = []
        duplicate_count = 0
        invalid_count = 0
        cases_to_create = []

        for url in raw_urls:
            if not url.startswith("http"):
                invalid_count += 1
                invalid_urls.append(url)
                continue

            if not is_valid_google_url(url):
                invalid_count += 1
                invalid_urls.append(url)
                continue

            if url in processed_urls or url in existing_urls:
                duplicate_count += 1
                continue

            processed_urls.add(url)

            cases_to_create.append(
                ReviewCase(
                    canonical_url=url,
                    original_url=url,
                    source_batch=batch,
                    status="NEEDS_TRIAGE"
                )
            )

        created_count = 0

        with transaction.atomic():
            BATCH_SIZE = 1000
            for i in range(0, len(cases_to_create), BATCH_SIZE):
                chunk = cases_to_create[i:i + BATCH_SIZE]
                ReviewCase.objects.bulk_create(chunk, batch_size=BATCH_SIZE)
            created_count = len(cases_to_create)

        batch.row_count = len(raw_urls)
        batch.valid_count = created_count
        batch.invalid_count = invalid_count
        batch.duplicate_count = duplicate_count
        batch.invalid_urls_log = "\n".join(invalid_urls[:5000])
        batch.status = "COMPLETED"
        batch.completed_at = timezone.now()
        batch.save()

        logger.info("Batch %s completed. %s cases created.", batch_id, created_count)

        return {
            "batch_id": batch_id,
            "rows": len(raw_urls),
            "created": created_count,
            "duplicates": duplicate_count,
            "invalid": invalid_count,
        }

    except Exception as exc:
        logger.exception("Import batch failed: %s", batch_id)

        if batch:
            batch.status = "FAILED"
            batch.error_log = str(exc)
            batch.completed_at = timezone.now()
            batch.retry_count += 1  # NEW: Increment retry counter
            batch.save(update_fields=["status", "error_log", "completed_at", "retry_count"])

        raise self.retry(exc=exc, countdown=60)


@shared_task
def sync_google_sheet_task(source_id=None):
    """
    Syncs one (or all) active Google Sheets into the ReviewCase database.
    This task is scheduled by Celery Beat to run every 30 minutes (see settings.py).
    """
    if source_id:
        sources = GoogleSheetSource.objects.filter(id=source_id, is_active=True)
    else:
        sources = GoogleSheetSource.objects.filter(is_active=True)

    for source in sources:
        # NEW: Create an ImportBatch record for each sync attempt
        batch = None

        try:
            logger.info(f"Starting sync for Google Sheet: {source.name}")

            # Create the ImportBatch tracking record
            batch = ImportBatch.objects.create(
                filename=f"SYNC: {source.name}",
                source_type="GOOGLE_SHEET",
                status="PROCESSING",
                uploaded_by=None, # System-initiated sync
            )

            # 1. Authenticate using the stored Service Account JSON
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(
                source.credentials_json,
                scopes=scope
            )
            client = gspread.authorize(creds)

            # 2. Open the sheet and read all values
            sheet = client.open_by_key(source.spreadsheet_id).worksheet(source.sheet_name)
            all_values = sheet.get_all_values()

            if not all_values:
                logger.warning(f"Sheet {source.name} is empty. Skipping.")
                batch.status = "FAILED"
                batch.error_log = "Sheet is empty."
                batch.completed_at = timezone.now()
                batch.save()
                continue

            # 3. Extract URLs (skipping the header row)
            raw_urls = [
                str(row[0]).strip()
                for row in all_values[1:]
                if row and row[0]
            ]

            # 4. Validate and deduplicate against existing DB
            existing_urls = set(
                ReviewCase.objects.values_list("canonical_url", flat=True)
            )
            cases_to_create = []
            invalid_count = 0
            duplicate_count = 0
            invalid_urls = []

            for url in raw_urls:
                if not url.startswith("http") or not is_valid_google_url(url):
                    invalid_count += 1
                    invalid_urls.append(url)
                    continue
                if url in existing_urls:
                    duplicate_count += 1
                    continue

                cases_to_create.append(
                    ReviewCase(
                        canonical_url=url,
                        original_url=url,
                        source_batch=batch,
                        status="NEEDS_TRIAGE"
                    )
                )
                existing_urls.add(url)

            # 5. Bulk create inside a transaction
            with transaction.atomic():
                BATCH_SIZE = 1000
                for i in range(0, len(cases_to_create), BATCH_SIZE):
                    chunk = cases_to_create[i:i + BATCH_SIZE]
                    ReviewCase.objects.bulk_create(chunk, batch_size=BATCH_SIZE)

            source.last_synced_at = timezone.now()
            source.save()

            # Finalize the batch record
            batch.row_count = len(raw_urls)
            batch.valid_count = len(cases_to_create)
            batch.invalid_count = invalid_count
            batch.duplicate_count = duplicate_count
            batch.invalid_urls_log = "\n".join(invalid_urls[:5000])
            batch.status = "COMPLETED"
            batch.completed_at = timezone.now()
            batch.save()

            logger.info(
                f"Sync complete for {source.name}. "
                f"Created: {len(cases_to_create)}, "
                f"Duplicates: {duplicate_count}, "
                f"Invalid: {invalid_count}"
            )

        except Exception as e:
            logger.exception(f"Failed to sync Google Sheet: {source.name}")
            
            if batch:
                batch.status = "FAILED"
                batch.error_log = str(e)
                batch.completed_at = timezone.now()
                batch.save(update_fields=["status", "error_log", "completed_at"])