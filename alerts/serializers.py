from rest_framework import serializers
from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id", "alert_type", "severity", "product", "product_sku", "product_name",
            "warehouse", "warehouse_name", "batch", "message",
            "is_resolved", "resolved_at", "created_at",
        ]
        read_only_fields = ["id", "created_at"]