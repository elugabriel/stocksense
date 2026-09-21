import 'package:flutter/material.dart';
import 'package:stocksense_shared/stocksense_shared.dart';

/// In-memory cart shared by [ProductCatalogScreen], [CartScreen], and
/// [B2bReorderScreen].
///
/// NOTE: the backend has no cart/order model yet — `sales.models.Sale`
/// is created in one shot via `POST /api/v1/sales/record/`, which is
/// shaped for staff ringing up a sale (it takes a `warehouse_id`, not
/// a customer identity) rather than a customer-initiated checkout.
/// Wiring "Place Order" below to a real endpoint needs either a new
/// customer-checkout endpoint or changes to `RecordSaleSerializer` —
/// tracked as a TODO, not implemented here.
class Cart extends ChangeNotifier {
  Cart._();
  static final Cart instance = Cart._();

  final Map<int, CartLine> _linesByProductId = {};

  List<CartLine> get lines => List.unmodifiable(_linesByProductId.values);

  double get total => lines.fold(0, (sum, line) => sum + line.subtotal);

  void add(Product product, {int quantity = 1}) {
    final existing = _linesByProductId[product.id];
    _linesByProductId[product.id] = CartLine(
      product: product,
      quantity: (existing?.quantity ?? 0) + quantity,
    );
    notifyListeners();
  }

  void setQuantity(int productId, int quantity) {
    if (quantity <= 0) {
      _linesByProductId.remove(productId);
    } else {
      final existing = _linesByProductId[productId];
      if (existing != null) {
        _linesByProductId[productId] = CartLine(product: existing.product, quantity: quantity);
      }
    }
    notifyListeners();
  }

  void remove(int productId) {
    _linesByProductId.remove(productId);
    notifyListeners();
  }

  void clear() {
    _linesByProductId.clear();
    notifyListeners();
  }
}

class CartLine {
  const CartLine({required this.product, required this.quantity});

  final Product product;
  final int quantity;

  double get subtotal => product.sellingPrice * quantity;
}

class CartScreen extends StatefulWidget {
  const CartScreen({super.key});

  @override
  State<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends State<CartScreen> {
  @override
  void initState() {
    super.initState();
    Cart.instance.addListener(_onCartChanged);
  }

  @override
  void dispose() {
    Cart.instance.removeListener(_onCartChanged);
    super.dispose();
  }

  void _onCartChanged() => setState(() {});

  @override
  Widget build(BuildContext context) {
    final lines = Cart.instance.lines;

    return Scaffold(
      appBar: AppBar(title: const Text('Cart')),
      body: lines.isEmpty
          ? const Center(child: Text('Your cart is empty.'))
          : ListView.builder(
              itemCount: lines.length,
              itemBuilder: (context, index) {
                final line = lines[index];
                return ListTile(
                  leading: IconButton(
                    icon: const Icon(Icons.remove_circle_outline),
                    onPressed: () => Cart.instance.setQuantity(line.product.id, line.quantity - 1),
                  ),
                  title: Text('${line.product.name}  x${line.quantity}'),
                  subtitle: Text('\$${line.product.sellingPrice.toStringAsFixed(2)} each'),
                  trailing: Text('\$${line.subtotal.toStringAsFixed(2)}'),
                );
              },
            ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Total: \$${Cart.instance.total.toStringAsFixed(2)}',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              FilledButton(
                onPressed: lines.isEmpty
                    ? null
                    : () {
                        // TODO: no customer-checkout endpoint exists yet —
                        // see the class doc comment above.
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Checkout isn\'t wired up to the backend yet.')),
                        );
                      },
                child: const Text('Place Order'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
