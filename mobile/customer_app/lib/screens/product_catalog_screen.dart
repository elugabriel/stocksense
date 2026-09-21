import 'package:flutter/material.dart';
import 'package:stocksense_shared/stocksense_shared.dart';

import 'cart_screen.dart';

/// Browses `GET /api/v1/products/` (`core.views.ProductViewSet`).
///
/// The API has no server-side filtering configured (no DRF filter
/// backend in `REST_FRAMEWORK` settings), so `is_active` is applied
/// client-side here rather than as a query param that would silently
/// be ignored.
class ProductCatalogScreen extends StatefulWidget {
  const ProductCatalogScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<ProductCatalogScreen> createState() => _ProductCatalogScreenState();
}

class _ProductCatalogScreenState extends State<ProductCatalogScreen> {
  late Future<List<Product>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<Product>> _load() async {
    final response = await widget.apiClient.get('/products/');
    final data = decodeOrThrow(response);
    final list = (data is Map<String, dynamic> ? data['results'] : data) as List<dynamic>;
    return list
        .map((e) => Product.fromJson(e as Map<String, dynamic>))
        .where((p) => p.isActive)
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Catalog'),
        actions: [
          IconButton(
            icon: const Icon(Icons.shopping_cart_outlined),
            tooltip: 'Cart',
            onPressed: () => Navigator.of(context).pushNamed('/cart'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => setState(() => _future = _load()),
        child: FutureBuilder<List<Product>>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return Center(child: Text('Failed to load: ${snapshot.error}'));
            }
            final products = snapshot.data!;
            if (products.isEmpty) {
              return const Center(child: Text('No products available yet.'));
            }
            return ListView.builder(
              itemCount: products.length,
              itemBuilder: (context, index) {
                final product = products[index];
                return ListTile(
                  title: Text(product.name),
                  subtitle: Text('${product.sku} · ${product.unitOfMeasure}'),
                  trailing: Text('\$${product.sellingPrice.toStringAsFixed(2)}'),
                  onTap: () => Cart.instance.add(product),
                );
              },
            );
          },
        ),
      ),
    );
  }
}
