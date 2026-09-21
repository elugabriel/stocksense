/// Mirrors `core.serializers.StockMovementSerializer` / `core.models.StockMovement`.
class StockMovement {
  const StockMovement({
    required this.id,
    required this.product,
    this.productSku = '',
    this.productName = '',
    required this.warehouse,
    this.warehouseName = '',
    this.batch,
    required this.movementType,
    required this.quantity,
    this.referenceId = '',
    this.performedBy,
    this.performedByUsername,
    this.notes = '',
    required this.timestamp,
  });

  final int id;
  final int product;
  final String productSku;
  final String productName;
  final int warehouse;
  final String warehouseName;
  final int? batch;

  /// One of: received, sale, transfer_out, transfer_in, adjustment,
  /// return, damage — see `StockMovement.MovementType` in core/models.py.
  final String movementType;

  /// Positive for stock increases, negative for decreases.
  final int quantity;
  final String referenceId;
  final int? performedBy;
  final String? performedByUsername;
  final String notes;
  final DateTime timestamp;

  factory StockMovement.fromJson(Map<String, dynamic> json) => StockMovement(
        id: json['id'] as int,
        product: json['product'] as int,
        productSku: json['product_sku'] as String? ?? '',
        productName: json['product_name'] as String? ?? '',
        warehouse: json['warehouse'] as int,
        warehouseName: json['warehouse_name'] as String? ?? '',
        batch: json['batch'] as int?,
        movementType: json['movement_type'] as String,
        quantity: json['quantity'] as int,
        referenceId: json['reference_id'] as String? ?? '',
        performedBy: json['performed_by'] as int?,
        performedByUsername: json['performed_by_username'] as String?,
        notes: json['notes'] as String? ?? '',
        timestamp: DateTime.parse(json['timestamp'] as String),
      );
}
