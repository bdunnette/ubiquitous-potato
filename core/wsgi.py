"""
WSGI config for django-zappa-uv project.

It exposes the WSGI callable as a module-level variable named ``application``.
Zappa invokes this callable on AWS Lambda.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = get_wsgi_application()
app = application  # Common alias
