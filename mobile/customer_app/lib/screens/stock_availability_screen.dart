import 'package:flutter/material.dart';
import 'package:stocksense_shared/stocksense_shared.dart';

/// Shows per-product stock levels from `GET /api/v1/dashboard/stock/`
/// (`core.views.StockDashboardView`), using its `by_product` bucket:
/// `{product__sku, product__name, total_quantity}`.
class StockAvailabilityScreen extends StatefulWidget {
  const StockAvailabilityScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<StockAvailabilityScreen> createState() => _StockAvailabilityScreenState();
}

class _StockAvailabilityScreenState extends State<StockAvailabilityScreen> {
  late Future<List<_ProductAvailability>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<_ProductAvailability>> _load() async {
    final response = await widget.apiClient.get('/dashboard/stock/');
    final data = decodeOrThrow(response) as Map<String, dynamic>;
    final byProduct = data['by_product'] as List<dynamic>;
    return byProduct
        .map((e) => _ProductAvailability.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Stock Availability')),
      body: RefreshIndicator(
        onRefresh: () async => setState(() => _future = _load()),
        child: FutureBuilder<List<_ProductAvailability>>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return Center(child: Text('Failed to load: ${snapshot.error}'));
            }
            final rows = snapshot.data!;
            if (rows.isEmpty) {
              return const Center(child: Text('No stock data yet.'));
            }
            return ListView.builder(
              itemCount: rows.length,
              itemBuilder: (context, index) {
                final row = rows[index];
                final inStock = row.totalQuantity > 0;
                return ListTile(
                  title: Text(row.productName),
                  subtitle: Text(row.productSku),
                  trailing: Chip(
                    label: Text(inStock ? '${row.totalQuantity} in stock' : 'Out of stock'),
                    backgroundColor: inStock
                        ? Colors.green.withValues(alpha: 0.15)
                        : Colors.red.withValues(alpha: 0.15),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}

class _ProductAvailability {
  const _ProductAvailability({
    required this.productSku,
    required this.productName,
    required this.totalQuantity,
  });

  final String productSku;
  final String productName;
  final int totalQuantity;

  factory _ProductAvailability.fromJson(Map<String, dynamic> json) => _ProductAvailability(
        productSku: json['product__sku'] as String? ?? '',
        productName: json['product__name'] as String? ?? '',
        totalQuantity: (json['total_quantity'] as num?)?.toInt() ?? 0,
      );
}
