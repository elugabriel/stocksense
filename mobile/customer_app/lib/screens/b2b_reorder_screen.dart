import 'package:flutter/material.dart';
import 'package:stocksense_shared/stocksense_shared.dart';

import 'cart_screen.dart';

/// Lets a repeat/B2B buyer re-add every line from a past order to the
/// cart in one tap, instead of hunting each product down again in the
/// catalog. Reuses the same `GET /api/v1/sales/` data as
/// [OrderHistoryScreen] — see that screen's doc comment for the
/// "no customer FK on Sale yet" caveat this inherits.
class B2bReorderScreen extends StatefulWidget {
  const B2bReorderScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<B2bReorderScreen> createState() => _B2bReorderScreenState();
}

class _B2bReorderScreenState extends State<B2bReorderScreen> {
  late Future<List<Sale>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<Sale>> _load() async {
    final response = await widget.apiClient.get('/sales/');
    final data = decodeOrThrow(response);
    final list = (data is Map<String, dynamic> ? data['results'] : data) as List<dynamic>;
    return list.map((e) => Sale.fromJson(e as Map<String, dynamic>)).toList();
  }

  void _reorder(Sale order) {
    for (final line in order.lines) {
      // SaleLine only carries product id/sku/name/unit_price — not
      // the full Product (unit of measure, current price, etc.), so
      // this stands in the line's own unit_price as the cart price
      // rather than round-tripping to `/products/{id}/` per line.
      Cart.instance.add(
        Product(
          id: line.product,
          sku: line.productSku,
          name: line.productName,
          unitOfMeasure: '',
          costPrice: 0,
          sellingPrice: line.unitPrice,
        ),
        quantity: line.quantity,
      );
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Added ${order.lines.length} item(s) from ${order.saleNumber} to your cart.')),
    );
    Navigator.of(context).pushNamed('/cart');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reorder a Past Order')),
      body: FutureBuilder<List<Sale>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Failed to load: ${snapshot.error}'));
          }
          final orders = snapshot.data!;
          if (orders.isEmpty) {
            return const Center(child: Text('No past orders to reorder from.'));
          }
          return ListView.builder(
            itemCount: orders.length,
            itemBuilder: (context, index) {
              final order = orders[index];
              return ListTile(
                title: Text(order.saleNumber),
                subtitle: Text('${order.lines.length} item(s) · \$${order.total.toStringAsFixed(2)}'),
                trailing: FilledButton.tonal(
                  onPressed: () => _reorder(order),
                  child: const Text('Reorder'),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
