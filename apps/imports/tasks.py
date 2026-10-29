
import csv
import logging
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import gspread
import openpyxl

from celery import shared_task
from django.db import IntegrityError, transaction
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

BATCH_SIZE = 500
INVALID_LOG_LIMIT = 5000


def normalize_google_url(value):
    """Validate and normalize a Google URL for consistent deduplication."""
    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value or len(value) > 8192:
        return None

    try:
        parsed = urlparse(value)

        if parsed.scheme.lower() not in {"http", "https"}:
            return None

        # Reject credentials and malformed URLs.
        if parsed.username is not None or parsed.password is not None:
            return None

        host = (parsed.hostname or "").lower().rstrip(".")

        if not host:
            return None

        if not any(
            host == domain or host.endswith("." + domain)
            for domain in ALLOWED_DOMAINS
        ):
            return None

        # Accessing port also detects malformed port values.
        _ = parsed.port

        # Fragments don't identify a different server-side resource.
        normalized = parsed._replace(
            scheme="https",
            netloc=host,
            fragment="",
        )

        return urlunparse(normalized)

    except (ValueError, TypeError, AttributeError):
        return None


def is_valid_google_url(url):
    """Backward-compatible validation helper."""
    return normalize_google_url(url) is not None


def load_urls_from_file(file_path):
    """Read URLs from the first column of CSV or XLSX files."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    urls = []

    if suffix == ".csv":
        with path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.reader(file)

            # Preserve the existing convention that row one is a header.
            next(reader, None)

            for row in reader:
                if row and row[0] is not None:
                    urls.append(str(row[0]).strip())

    elif suffix == ".xlsx":
        workbook = openpyxl.load_workbook(
            path,
            read_only=True,
            data_only=True,
        )

        try:
            sheet = workbook.active

            for row in sheet.iter_rows(
                min_row=2,
                min_col=1,
                max_col=1,
                values_only=True,
            ):
                value = row[0]

                if value is not None:
                    urls.append(str(value).strip())
        finally:
            workbook.close()

    else:
        raise ValueError(
            f"Unsupported file type: {suffix}"
        )

    return urls


def prepare_case_import(raw_urls, batch):
    """Validate and deduplicate URLs before writing to the database."""
    existing_urls = set(
        ReviewCase.objects.values_list(
            "canonical_url", flat=True
        )
    )

    seen_urls = set()
    cases = []
    invalid_urls = []
    duplicates = 0
    invalid = 0

    for raw_url in raw_urls:
        normalized = normalize_google_url(raw_url)

        if normalized is None:
            invalid += 1
            invalid_urls.append(str(raw_url)[:8192])
            continue

        if normalized in seen_urls or normalized in existing_urls:
            duplicates += 1
            continue

        seen_urls.add(normalized)

        cases.append(
            ReviewCase(
                canonical_url=normalized,
                original_url=str(raw_url).strip(),
                source_batch=batch,
                status="NEEDS_TRIAGE",
            )
        )

    return cases, invalid_urls, duplicates, invalid


def save_import_cases(cases):
    """Insert cases in bounded batches within a transaction."""
    created = 0

    with transaction.atomic():
        for offset in range(0, len(cases), BATCH_SIZE):
            chunk = cases[offset:offset + BATCH_SIZE]

            # An IntegrityError is not silently swallowed. A database
            # uniqueness constraint should protect against concurrent jobs.
            ReviewCase.objects.bulk_create(
                chunk,
                batch_size=BATCH_SIZE,
            )
            created += len(chunk)

    return created


def finalize_batch(
    batch,
    row_count,
    created_count,
    duplicate_count,
    invalid_count,
    invalid_urls,
):
    batch.row_count = row_count
    batch.valid_count = created_count
    batch.duplicate_count = duplicate_count
    batch.invalid_count = invalid_count
    batch.invalid_urls_log = "\n".join(
        invalid_urls[:INVALID_LOG_LIMIT]
    )
    batch.status = "COMPLETED"
    batch.completed_at = timezone.now()
    batch.error_log = ""

    batch.save()


@shared_task(bind=True, max_retries=3)
def process_import_batch_task(self, batch_id):
    batch = None

    try:
        batch = ImportBatch.objects.get(id=batch_id)

        batch.status = "PROCESSING"
        batch.error_log = ""

        if batch.file:
            suffix = Path(batch.file.name).suffix.lower()

            if suffix == ".xlsx":
                batch.source_type = "XLSX"
            elif suffix == ".csv":
                batch.source_type = "CSV"
            else:
                raise ValueError(
                    f"Unsupported import file: {suffix}"
                )

        batch.save(
            update_fields=[
                "status",
                "error_log",
                "source_type",
            ]
        )

        logger.info("Processing import batch %s", batch_id)

        raw_urls = load_urls_from_file(batch.file.path)

        cases, invalid_urls, duplicates, invalid = (
            prepare_case_import(raw_urls, batch)
        )

        created = save_import_cases(cases)

        finalize_batch(
            batch=batch,
            row_count=len(raw_urls),
            created_count=created,
            duplicate_count=duplicates,
            invalid_count=invalid,
            invalid_urls=invalid_urls,
        )

        logger.info(
            "Import %s completed: rows=%s, created=%s, "
            "duplicates=%s, invalid=%s",
            batch_id,
            len(raw_urls),
            created,
            duplicates,
            invalid,
        )

        return {
            "batch_id": str(batch_id),
            "rows": len(raw_urls),
            "created": created,
            "duplicates": duplicates,
            "invalid": invalid,
        }

    except Exception as exc:
        logger.exception("Import batch %s failed", batch_id)

        # Celery's retry count is authoritative for this task attempt.
        if self.request.retries < self.max_retries:
            if batch:
                batch.status = "PROCESSING"
                batch.error_log = (
                    f"Attempt {self.request.retries + 1} failed: "
                    f"{str(exc)[:4000]}"
                )
                batch.save(
                    update_fields=["status", "error_log"]
                )

            raise self.retry(
                exc=exc,
                countdown=60 * (self.request.retries + 1),
            )

        if batch:
            batch.status = "FAILED"
            batch.error_log = str(exc)[:4000]
            batch.completed_at = timezone.now()
            batch.retry_count = (
                batch.retry_count + 1
            )
            batch.save(
                update_fields=[
                    "status",
                    "error_log",
                    "completed_at",
                    "retry_count",
                ]
            )

        raise


@shared_task(bind=True, max_retries=3)
def sync_google_sheet_task(self, source_id=None):
    """Synchronize active Google Sheets into ReviewCase records."""
    if source_id is not None:
        sources = GoogleSheetSource.objects.filter(
            id=source_id,
            is_active=True,
        )
    else:
        sources = GoogleSheetSource.objects.filter(
            is_active=True
        )

    results = []

    for source in sources:
        batch = None

        try:
            logger.info("Starting sheet sync: %s", source.name)

            batch = ImportBatch.objects.create(
                filename=f"SYNC: {source.name}",
                source_type="GOOGLE_SHEET",
                status="PROCESSING",
                uploaded_by=None,
            )

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets.readonly",
            ]

            credentials = Credentials.from_service_account_info(
                source.credentials_json,
                scopes=scopes,
            )

            client = gspread.authorize(credentials)

            worksheet = client.open_by_key(
                source.spreadsheet_id
            ).worksheet(source.sheet_name)

            values = worksheet.get_all_values()

            if not values:
                raise ValueError("Google Sheet is empty.")

            # First row is treated as a header, matching the
            # existing application convention.
            raw_urls = [
                str(row[0]).strip()
                for row in values[1:]
                if row and row[0]
            ]

            cases, invalid_urls, duplicates, invalid = (
                prepare_case_import(raw_urls, batch)
            )

            created = save_import_cases(cases)

            finalize_batch(
                batch=batch,
                row_count=len(raw_urls),
                created_count=created,
                duplicate_count=duplicates,
                invalid_count=invalid,
                invalid_urls=invalid_urls,
            )

            source.last_synced_at = timezone.now()
            source.save(update_fields=["last_synced_at"])

            results.append({
                "source_id": str(source.id),
                "status": "COMPLETED",
                "created": created,
                "duplicates": duplicates,
                "invalid": invalid,
            })

            logger.info(
                "Sheet sync completed: %s; created=%s",
                source.name,
                created,
            )

        except Exception as exc:
            logger.exception(
                "Google Sheet sync failed: %s",
                source.name,
            )

            if batch:
                batch.status = "FAILED"
                batch.error_log = str(exc)[:4000]
                batch.completed_at = timezone.now()
                batch.save(
                    update_fields=[
                        "status",
                        "error_log",
                        "completed_at",
                    ]
                )

            results.append({
                "source_id": str(source.id),
                "status": "FAILED",
                "error": str(exc)[:1000],
            })

    return results
