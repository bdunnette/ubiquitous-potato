"""
URL configuration for django-zappa-uv project.
"""

import time

from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    """
    Lightweight health check endpoint for AWS API Gateway / Route 53 / CloudWatch.
    """
    db_engine = settings.DATABASES["default"]["ENGINE"]
    is_s3_sqlite = "django_s3_sqlite" in db_engine
    bucket = settings.DATABASES["default"].get("BUCKET", "N/A") if is_s3_sqlite else "local"

    return JsonResponse(
        {
            "status": "healthy",
            "timestamp": int(time.time()),
            "database": {
                "engine": db_engine,
                "is_s3_sqlite": is_s3_sqlite,
                "bucket": bucket,
            },
            "debug": settings.DEBUG,
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("", include("demo.urls")),
]
