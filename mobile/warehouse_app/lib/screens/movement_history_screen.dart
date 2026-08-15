import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared/api_client.dart';

class MovementHistoryScreen extends StatefulWidget {
  const MovementHistoryScreen({super.key});

  @override
  State<MovementHistoryScreen> createState() => _MovementHistoryScreenState();
}

class _MovementHistoryScreenState extends State<MovementHistoryScreen> {
  bool _isLoading = true;
  String? _error;
  List<dynamic> _movements = [];

  @override
  void initState() {
    super.initState();
    _loadMovements();
  }

  Future<void> _loadMovements() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    final response = await ApiClient.get("/movements/");

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final list = data is Map && data.containsKey("results") ? data["results"] : data;
      setState(() {
        _movements = list;
        _isLoading = false;
      });
    } else {
      setState(() {
        _error = "Failed to load movement history.";
        _isLoading = false;
      });
    }
  }

  Color _colorForQuantity(num qty) {
    if (qty > 0) return Colors.green.shade700;
    if (qty < 0) return Colors.red.shade700;
    return Colors.grey;
  }

  String _labelForType(String type) {
    const labels = {
      "received": "Received",
      "sale": "Sale",
      "transfer_out": "Transfer Out",
      "transfer_in": "Transfer In",
      "adjustment": "Adjustment",
      "return": "Return",
      "damage": "Damage",
    };
    return labels[type] ?? type;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Movement History"),
        backgroundColor: const Color(0xFF1A2634),
        foregroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadMovements),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : _movements.isEmpty
                  ? const Center(child: Text("No movements recorded yet."))
                  : RefreshIndicator(
                      onRefresh: _loadMovements,
                      child: ListView.separated(
                        padding: const EdgeInsets.all(12),
                        itemCount: _movements.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (context, index) {
                          final m = _movements[index];
                          final qty = m["quantity"] as num;
                          final date = DateTime.tryParse(m["timestamp"] ?? "");

                          return ListTile(
                            title: Text("${m["product_sku"]} — ${_labelForType(m["movement_type"])}"),
                            subtitle: Text(
                              "${m["warehouse_name"] ?? ""} • ${m["performed_by_username"] ?? "—"}"
                              "${date != null ? " • ${date.toLocal().toString().substring(0, 16)}" : ""}",
                            ),
                            trailing: Text(
                              "${qty > 0 ? "+" : ""}$qty",
                              style: TextStyle(
                                color: _colorForQuantity(qty),
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                              ),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}