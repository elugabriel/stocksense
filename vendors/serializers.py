from rest_framework import serializers
from .models import Vendor, PurchaseOrder, PurchaseOrderLine


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            "id", "name", "contact_person", "email", "phone",
            "address", "city", "country", "payment_terms",
            "default_lead_time_days", "status", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = ["id", "product", "product_sku", "product_name", "quantity_ordered", "quantity_received", "unit_cost"]
        read_only_fields = ["id"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    lines = PurchaseOrderLineSerializer(many=True, required=False)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "vendor", "vendor_name", "order_number", "status",
            "expected_delivery_date", "actual_delivery_date",
            "created_by", "notes", "created_at", "lines",
        ]
        read_only_fields = ["id", "created_at", "created_by"]

    def create(self, validated_data):
        lines_data = validated_data.pop("lines", [])
        purchase_order = PurchaseOrder.objects.create(**validated_data)
        for line_data in lines_data:
            PurchaseOrderLine.objects.create(purchase_order=purchase_order, **line_data)
        return purchase_order