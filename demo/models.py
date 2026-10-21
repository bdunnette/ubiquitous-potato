from django.db import models


class Item(models.Model):
    """
    Sample model to verify that database reads and writes succeed
    and persist across AWS Lambda invocations via django-s3-sqlite.
    """

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title
