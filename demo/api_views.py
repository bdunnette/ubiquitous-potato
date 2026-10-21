import os
import sys
import time

import django
from django.conf import settings
import rest_framework
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Item
from .serializers import ItemSerializer


class ItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows items to be viewed, created, updated, or deleted.
    """

    queryset = Item.objects.all()
    serializer_class = ItemSerializer


@api_view(["GET"])
def api_info(request):
    """
    Informational endpoint providing system runtime details, database status,
    and record statistics in JSON format.
    """
    db_config = settings.DATABASES["default"]
    db_engine = db_config.get("ENGINE", "")
    is_s3_sqlite = "django_s3_sqlite" in db_engine

    return Response(
        {
            "name": "Django Serverless Template API",
            "status": "healthy",
            "timestamp": int(time.time()),
            "python_version": sys.version.split()[0],
            "django_version": django.get_version(),
            "drf_version": rest_framework.__version__,
            "environment": {
                "is_lambda": bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME")),
                "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "Local execution"),
                "aws_region": os.environ.get(
                    "AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "local")
                ),
                "debug": settings.DEBUG,
            },
            "database": {
                "engine": db_engine,
                "is_s3_sqlite": is_s3_sqlite,
                "bucket": db_config.get("BUCKET", "Not configured")
                if is_s3_sqlite
                else "Local disk",
                "name": db_config.get("NAME", "db.sqlite3"),
            },
            "stats": {
                "item_count": Item.objects.count(),
            },
        }
    )
