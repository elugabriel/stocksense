/// Mirrors `core.serializers.ProductSerializer` / `core.models.Product`.
class Product {
  const Product({
    required this.id,
    required this.sku,
    required this.name,
    this.description = '',
    this.category,
    required this.unitOfMeasure,
    required this.costPrice,
    required this.sellingPrice,
    this.reorderLevel = 0,
    this.barcode,
    this.isActive = true,
    this.createdAt,
    this.updatedAt,
  });

  final int id;
  final String sku;
  final String name;
  final String description;
  final int? category;
  final String unitOfMeasure;
  final double costPrice;
  final double sellingPrice;
  final int reorderLevel;
  final String? barcode;
  final bool isActive;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  factory Product.fromJson(Map<String, dynamic> json) => Product(
        id: json['id'] as int,
        sku: json['sku'] as String,
        name: json['name'] as String,
        description: json['description'] as String? ?? '',
        category: json['category'] as int?,
        unitOfMeasure: json['unit_of_measure'] as String,
        costPrice: double.parse(json['cost_price'].toString()),
        sellingPrice: double.parse(json['selling_price'].toString()),
        reorderLevel: json['reorder_level'] as int? ?? 0,
        barcode: json['barcode'] as String?,
        isActive: json['is_active'] as bool? ?? true,
        createdAt: json['created_at'] != null
            ? DateTime.parse(json['created_at'] as String)
            : null,
        updatedAt: json['updated_at'] != null
            ? DateTime.parse(json['updated_at'] as String)
            : null,
      );

  Map<String, dynamic> toJson() => {
        'sku': sku,
        'name': name,
        'description': description,
        'category': category,
        'unit_of_measure': unitOfMeasure,
        'cost_price': costPrice,
        'selling_price': sellingPrice,
        'reorder_level': reorderLevel,
        'barcode': barcode,
        'is_active': isActive,
      };
}
