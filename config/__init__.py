from __future__ import absolute_import, unicode_literals

# Import Celery application to make it available on Django startup
from .celery import app as celery_app

__all__ = ("celery_app",)
