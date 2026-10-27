#!/usr/bin/env bash
# ==================================================================
# Review Compliance System — Render build script
# Safe to run repeatedly. Idempotent.
# ==================================================================
set -o errexit   # exit on error
set -o pipefail  # catch pipe errors

echo "🚀 Starting Review Compliance build..."

# ------------------------------------------------------------------
# 1. Install dependencies
# ------------------------------------------------------------------
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# ------------------------------------------------------------------
# 2. Apply migrations
#    NEVER delete existing migration files — they are your schema.
# ------------------------------------------------------------------
echo "🗄️  Applying migrations..."
python manage.py migrate --noinput

# ------------------------------------------------------------------
# 3. Collect static files
# ------------------------------------------------------------------
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# ------------------------------------------------------------------
# 4. Idempotent superuser creation
#    Only creates if it doesn't already exist.
# ------------------------------------------------------------------
echo "👤 Ensuring superuser exists..."
python manage.py shell << 'PYEOF'
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@reviewcompliance.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not password:
    print('⚠️  DJANGO_SUPERUSER_PASSWORD not set — skipping superuser creation.')
else:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'role': 'ADMIN',           # Matches your CustomUser ROLE_CHOICES
            'is_staff': True,
            'is_superuser': True,
        },
    )
    if created:
        user.set_password(password)
        user.save()
        print(f'✅ Superuser created: {username}')
    else:
        changed = False
        if not user.is_staff:
            user.is_staff = True; changed = True
        if not user.is_superuser:
            user.is_superuser = True; changed = True
        if user.role != 'ADMIN':
            user.role = 'ADMIN'; changed = True
        if password:
            user.set_password(password); changed = True
        if changed:
            user.save()
            print(f'✅ Superuser {username} updated.')
        else:
            print(f'ℹ️  Superuser {username} already exists — no changes.')
PYEOF

# ------------------------------------------------------------------
# 5. (Optional) Seed initial data
#    Only runs if you create a custom management command later.
# ------------------------------------------------------------------
# echo "🌱 Seeding initial data..."
# python manage.py seed_data || echo "⚠️  Seeding skipped (data may already exist)"

echo "✅ Build completed successfully."