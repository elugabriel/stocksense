/// Mirrors `sales.serializers.SaleLineSerializer` / `sales.models.SaleLine`.
class SaleLine {
  const SaleLine({
    required this.id,
    required this.product,
    this.productSku = '',
    this.productName = '',
    this.batch,
    required this.quantity,
    required this.unitPrice,
    required this.lineTotal,
  });

  final int id;
  final int product;
  final String productSku;
  final String productName;
  final int? batch;
  final int quantity;
  final double unitPrice;
  final double lineTotal;

  factory SaleLine.fromJson(Map<String, dynamic> json) => SaleLine(
        id: json['id'] as int,
        product: json['product'] as int,
        productSku: json['product_sku'] as String? ?? '',
        productName: json['product_name'] as String? ?? '',
        batch: json['batch'] as int?,
        quantity: json['quantity'] as int,
        unitPrice: double.parse(json['unit_price'].toString()),
        lineTotal: double.parse(json['line_total'].toString()),
      );
}

/// Mirrors `sales.serializers.SaleSerializer` / `sales.models.Sale`.
class Sale {
  const Sale({
    required this.id,
    required this.saleNumber,
    this.branch,
    this.warehouse,
    this.customerName = '',
    this.customerPhone = '',
    this.customerEmail = '',
    required this.paymentMethod,
    this.soldBy,
    this.soldByUsername,
    required this.subtotal,
    required this.discount,
    required this.total,
    this.notes = '',
    required this.createdAt,
    this.lines = const [],
  });

  final int id;
  final String saleNumber;
  final int? branch;
  final int? warehouse;
  final String customerName;
  final String customerPhone;
  final String customerEmail;

  /// One of: cash, card, bank_transfer, mobile_money, other.
  final String paymentMethod;
  final int? soldBy;
  final String? soldByUsername;
  final double subtotal;
  final double discount;
  final double total;
  final String notes;
  final DateTime createdAt;
  final List<SaleLine> lines;

  factory Sale.fromJson(Map<String, dynamic> json) => Sale(
        id: json['id'] as int,
        saleNumber: json['sale_number'] as String,
        branch: json['branch'] as int?,
        warehouse: json['warehouse'] as int?,
        customerName: json['customer_name'] as String? ?? '',
        customerPhone: json['customer_phone'] as String? ?? '',
        customerEmail: json['customer_email'] as String? ?? '',
        paymentMethod: json['payment_method'] as String,
        soldBy: json['sold_by'] as int?,
        soldByUsername: json['sold_by_username'] as String?,
        subtotal: double.parse(json['subtotal'].toString()),
        discount: double.parse(json['discount'].toString()),
        total: double.parse(json['total'].toString()),
        notes: json['notes'] as String? ?? '',
        createdAt: DateTime.parse(json['created_at'] as String),
        lines: (json['lines'] as List<dynamic>? ?? [])
            .map((e) => SaleLine.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
