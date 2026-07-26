from rest_framework import serializers
from .models import Product
from .models import Batch, StockMovement, StockAdjustment, StockTransfer


class AddStockSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    lot_number = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=1)
    manufacture_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id", "sku", "name", "description", "category",
            "unit_of_measure", "cost_price", "selling_price",
            "reorder_level", "barcode", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        
class ReceiveStockFromVendorSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    lot_number = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=1)
    vendor_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    manufacture_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    
    
class ReturnStockSerializer(serializers.Serializer):
    class ReturnDirection(serializers.ChoiceField):
        pass

    product_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    batch_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)
    direction = serializers.ChoiceField(choices=["to_vendor", "from_customer"])
    is_resellable = serializers.BooleanField(default=True)
    reason = serializers.CharField(max_length=255)
    

class TransferStockSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    batch_id = serializers.IntegerField()
    source_warehouse_id = serializers.IntegerField()
    destination_warehouse_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
class RemoveDamagedExpiredSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    batch_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    reason_code = serializers.ChoiceField(choices=StockAdjustment.ReasonCode.choices)
    reason_notes = serializers.CharField(max_length=500)
    
class PhysicalCountSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    batch_id = serializers.IntegerField()
    counted_quantity = serializers.IntegerField(min_value=0)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)