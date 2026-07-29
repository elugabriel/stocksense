from rest_framework import serializers
from .models import Sale, SaleLine


class SaleLineInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    batch_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)


class RecordSaleSerializer(serializers.Serializer):
    sale_number = serializers.CharField(max_length=100)
    branch_id = serializers.IntegerField(required=False, allow_null=True)
    warehouse_id = serializers.IntegerField()
    customer_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=Sale.PaymentMethod.choices, default="cash")
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)
    lines = SaleLineInputSerializer(many=True)


class SaleLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SaleLine
        fields = ["id", "product", "product_sku", "product_name", "batch", "quantity", "unit_price", "line_total"]


class SaleSerializer(serializers.ModelSerializer):
    lines = SaleLineSerializer(many=True, read_only=True)
    sold_by_username = serializers.CharField(source="sold_by.username", read_only=True)

    class Meta:
        model = Sale
        fields = [
            "id", "sale_number", "branch", "warehouse", "customer_name",
            "customer_phone", "customer_email", "payment_method",
            "sold_by", "sold_by_username", "subtotal", "discount", "total",
            "notes", "created_at", "lines",
        ]