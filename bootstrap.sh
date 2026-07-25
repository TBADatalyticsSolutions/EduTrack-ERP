#!/bin/bash

echo "========================================="
echo " EduTrack ERP Bootstrap"
echo "========================================="

# Create project folders
mkdir -p apps
mkdir -p templates
mkdir -p static
mkdir -p media
mkdir -p docs
mkdir -p tests

touch apps/__init__.py

echo "Creating Django Apps..."

APPS=(
accounts
schools
students
teachers
parents
academics
attendance
finance
results
reports
notifications
api
)

for APP in "${APPS[@]}"
do
    echo "Creating $APP ..."
    python manage.py startapp "$APP" "apps/$APP"
done

echo ""
echo "Updating AppConfig..."

for APP in "${APPS[@]}"
do
cat > apps/$APP/apps.py <<EOF
from django.apps import AppConfig


class ${APP^}Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.$APP"
EOF
done

echo ""
echo "Bootstrap completed successfully!"
echo ""
echo "Apps created:"
ls apps