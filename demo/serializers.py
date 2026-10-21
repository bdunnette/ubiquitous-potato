from rest_framework import serializers

from .models import Item


class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the Item model, supporting full CRUD operations.
    """

    class Meta:
        model = Item
        fields = ["id", "title", "description", "created_at"]
        read_only_fields = ["id", "created_at"]
