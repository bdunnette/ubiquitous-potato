import os
import sys

import django
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .models import Item


def home(request):
    """
    Renders the template dashboard displaying serverless architecture details,
    database persistence status, and interactive items.
    """
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        if title:
            Item.objects.create(title=title, description=description)
            messages.success(request, f"Created item: '{title}'! Saved to SQLite & synced to S3.")
        else:
            messages.error(request, "Item title cannot be empty.")
        return redirect("home")

    items = Item.objects.all()[:20]
    db_config = settings.DATABASES["default"]
    db_engine = db_config.get("ENGINE", "")
    is_s3_sqlite = "django_s3_sqlite" in db_engine

    context = {
        "items": items,
        "item_count": Item.objects.count(),
        "python_version": sys.version.split()[0],
        "django_version": django.get_version(),
        "db_engine": db_engine,
        "is_s3_sqlite": is_s3_sqlite,
        "s3_bucket": db_config.get("BUCKET", "Not configured") if is_s3_sqlite else "Local disk",
        "s3_db_name": db_config.get("NAME", "db.sqlite3"),
        "is_lambda": bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME")),
        "lambda_function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "Local execution"),
        "aws_region": os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "local")),
        "debug": settings.DEBUG,
        "static_backend": "S3 (django-storages)"
        if getattr(settings, "USE_S3_STATIC", False)
        else "WhiteNoise",
    }
    return render(request, "demo/index.html", context)


def delete_item(request, item_id):
    """
    Deletes an item to test database deletion and S3 sync.
    """
    if request.method == "POST":
        item = get_object_or_404(Item, id=item_id)
        title = item.title
        item.delete()
        messages.info(request, f"Deleted item: '{title}'.")
    return redirect("home")
