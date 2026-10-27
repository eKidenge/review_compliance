#!/usr/bin/env bash
# ==================================================================
# Review Compliance System — Render build script
# Safe to run repeatedly. Idempotent.
# ==================================================================
set -o errexit   # exit on error
set -o pipefail  # catch pipe errors

echo "🚀 Starting Review Compliance build..."

# ------------------------------------------------------------------
# 0. Fix Render static directory warning
# ------------------------------------------------------------------
echo "📁 Ensuring static directory exists..."
mkdir -p static
touch static/.gitkeep

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
# 4. Idempotent user creation for ALL roles
# ------------------------------------------------------------------
echo "👤 Ensuring all default role accounts exist..."
python manage.py shell << 'PYEOF'
import os
from django.contrib.auth import get_user_model

User = get_user_model()

# Fetch master password from environment (fallback for local testing)
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@12345!')

# List of users to create: (username, email, role, is_staff, is_superuser)
users_to_create = [
    ('admin', 'admin@reviewcompliance.com', 'ADMIN', True, True),
    ('reviewer1', 'reviewer@reviewcompliance.com', 'REVIEWER', False, False),
    ('submitter1', 'submitter@reviewcompliance.com', 'SUBMITTER', False, False),
    ('client1', 'client@reviewcompliance.com', 'CLIENT', False, False),
]

for username, email, role, is_staff, is_superuser in users_to_create:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'role': role,
            'is_staff': is_staff,
            'is_superuser': is_superuser,
        },
    )
    
    if created:
        user.set_password(password)
        user.save()
        print(f'✅ Created {role}: {username}')
    else:
        # Update existing user to ensure role/password are correct
        changed = False
        if user.role != role:
            user.role = role; changed = True
        if user.is_staff != is_staff:
            user.is_staff = is_staff; changed = True
        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser; changed = True
        if not user.check_password(password):
            user.set_password(password); changed = True
            
        if changed:
            user.save()
            print(f'✅ Updated {role}: {username}')
        else:
            print(f'ℹ️  {role} {username} already exists — no changes.')
PYEOF

echo "✅ Build completed successfully."
