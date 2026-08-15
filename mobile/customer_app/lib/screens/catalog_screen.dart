import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared/api_client.dart';
import 'login_screen.dart';
import 'order_history_screen.dart';

class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  bool _isLoading = true;
  String? _error;
  List<dynamic> _products = [];
  final Map<int, int> _cart = {}; // productId -> quantity

  @override
  void initState() {
    super.initState();
    _loadCatalog();
  }

  Future<void> _loadCatalog() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    final response = await ApiClient.get("/catalog/");

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      setState(() {
        _products = data["products"];
        _isLoading = false;
      });
    } else {
      setState(() {
        _error = "Failed to load products.";
        _isLoading = false;
      });
    }
  }

  void _addToCart(int productId) {
    setState(() {
      _cart[productId] = (_cart[productId] ?? 0) + 1;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Added to cart"), duration: Duration(seconds: 1)),
    );
  }

  Future<void> _logout(BuildContext context) async {
    await ApiClient.clearTokens();
    if (context.mounted) {
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
    }
  }

  int get _cartCount => _cart.values.fold(0, (sum, qty) => sum + qty);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4F5F7),
      appBar: AppBar(
        title: const Text("StockSense Shop"),
        backgroundColor: const Color(0xFF27AE60),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.receipt_long),
            tooltip: "My Orders",
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const OrderHistoryScreen())),
          ),
          Stack(
            children: [
              IconButton(
                icon: const Icon(Icons.shopping_cart),
                onPressed: () => _showCartAndCheckout(),
              ),
              if (_cartCount > 0)
                Positioned(
                  right: 6,
                  top: 6,
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle),
                    child: Text("$_cartCount", style: const TextStyle(color: Colors.white, fontSize: 10)),
                  ),
                ),
            ],
          ),
          IconButton(icon: const Icon(Icons.logout), onPressed: () => _logout(context)),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : RefreshIndicator(
                  onRefresh: _loadCatalog,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _products.length,
                    itemBuilder: (context, index) {
                      final p = _products[index];
                      final inStock = p["in_stock"] == true;

                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(p["name"], style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
                              Text(p["sku"], style: const TextStyle(color: Colors.grey, fontSize: 12)),
                              const SizedBox(height: 8),
                              Text("₦${p["selling_price"]}", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Color(0xFF27AE60))),
                              const SizedBox(height: 6),
                              Text(
                                inStock ? "In Stock (${p["total_stock"]} available)" : "Out of Stock",
                                style: TextStyle(color: inStock ? Colors.green : Colors.red, fontSize: 13),
                              ),
                              const SizedBox(height: 10),
                              SizedBox(
                                width: double.infinity,
                                child: ElevatedButton(
                                  onPressed: inStock ? () => _addToCart(p["id"]) : null,
                                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF27AE60), foregroundColor: Colors.white),
                                  child: const Text("Add to Cart"),
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }

  void _showCartAndCheckout() {
    if (_cart.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Your cart is empty.")));
      return;
    }

    showModalBottomSheet(
      context: context,
      builder: (context) {
        return _CheckoutSheet(
          cart: _cart,
          products: _products,
          onOrderPlaced: () {
            setState(() => _cart.clear());
            Navigator.pop(context);
          },
        );
      },
    );
  }
}

class _CheckoutSheet extends StatefulWidget {
  final Map<int, int> cart;
  final List<dynamic> products;
  final VoidCallback onOrderPlaced;

  const _CheckoutSheet({required this.cart, required this.products, required this.onOrderPlaced});

  @override
  State<_CheckoutSheet> createState() => _CheckoutSheetState();
}

class _CheckoutSheetState extends State<_CheckoutSheet> {
  bool _isPlacing = false;
  String? _error;

  Future<void> _placeOrder() async {
    setState(() {
      _isPlacing = true;
      _error = null;
    });

    final lines = widget.cart.entries.map((e) => {"product_id": e.key, "quantity": e.value}).toList();
    final orderNumber = "ORD-${DateTime.now().millisecondsSinceEpoch}";

    final response = await ApiClient.post("/orders/place/", {
      "order_number": orderNumber,
      "warehouse_id": 1,
      "lines": lines,
    });

    setState(() => _isPlacing = false);

    if (response.statusCode == 201) {
      widget.onOrderPlaced();
    } else {
      setState(() => _error = "Failed to place order. Please try again.");
    }
  }

  @override
  Widget build(BuildContext context) {
    double total = 0;
    final items = widget.cart.entries.map((entry) {
      final product = widget.products.firstWhere((p) => p["id"] == entry.key);
      final price = double.parse(product["selling_price"]);
      final lineTotal = price * entry.value;
      total += lineTotal;
      return "${product["name"]} x${entry.value} — ₦${lineTotal.toStringAsFixed(2)}";
    }).toList();

    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom, left: 20, right: 20, top: 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text("Your Cart", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          ...items.map((line) => Padding(padding: const EdgeInsets.symmetric(vertical: 4), child: Text(line))),
          const Divider(),
          Text("Total: ₦${total.toStringAsFixed(2)}", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
          ElevatedButton(
            onPressed: _isPlacing ? null : _placeOrder,
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF27AE60), foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 14)),
            child: _isPlacing ? const CircularProgressIndicator(color: Colors.white) : const Text("Place Order"),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}