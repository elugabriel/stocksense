from rest_framework import serializers
from .models import Product
from .models import Batch, StockMovement, StockAdjustment, StockTransfer
from .models import Warehouse, Category


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
    


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "branch", "warehouse_type", "address", "city", "capacity_units", "manager", "is_active"]
        read_only_fields = ["id"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "parent", "description", "is_active"]
        read_only_fields = ["id"]
        
class StockMovementSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    performed_by_username = serializers.CharField(source="performed_by.username", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id", "product", "product_sku", "product_name",
            "warehouse", "warehouse_name", "batch",
            "movement_type", "quantity", "reference_id",
            "performed_by", "performed_by_username", "notes", "timestamp",
        ]