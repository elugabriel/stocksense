import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared/api_client.dart';

class OrderHistoryScreen extends StatefulWidget {
  const OrderHistoryScreen({super.key});

  @override
  State<OrderHistoryScreen> createState() => _OrderHistoryScreenState();
}

class _OrderHistoryScreenState extends State<OrderHistoryScreen> {
  bool _isLoading = true;
  String? _error;
  List<dynamic> _orders = [];

  @override
  void initState() {
    super.initState();
    _loadOrders();
  }

  Future<void> _loadOrders() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    final response = await ApiClient.get("/orders/mine/");

    if (response.statusCode == 200) {
      setState(() {
        _orders = jsonDecode(response.body);
        _isLoading = false;
      });
    } else {
      setState(() {
        _error = "Failed to load orders.";
        _isLoading = false;
      });
    }
  }

  Color _statusColor(String status) {
    switch (status) {
      case "fulfilled":
        return Colors.green;
      case "confirmed":
        return Colors.blue;
      case "cancelled":
        return Colors.red;
      default:
        return Colors.orange;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("My Orders"), backgroundColor: const Color(0xFF27AE60), foregroundColor: Colors.white),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : _orders.isEmpty
                  ? const Center(child: Text("You haven't placed any orders yet."))
                  : RefreshIndicator(
                      onRefresh: _loadOrders,
                      child: ListView.separated(
                        padding: const EdgeInsets.all(12),
                        itemCount: _orders.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (context, index) {
                          final o = _orders[index];
                          return ExpansionTile(
                            title: Text(o["order_number"]),
                            subtitle: Text("Total: ₦${o["total"]}"),
                            trailing: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(color: _statusColor(o["status"]).withOpacity(0.15), borderRadius: BorderRadius.circular(10)),
                              child: Text(o["status"].toString().toUpperCase(), style: TextStyle(color: _statusColor(o["status"]), fontSize: 11, fontWeight: FontWeight.bold)),
                            ),
                            children: (o["lines"] as List).map<Widget>((line) {
                              return ListTile(
                                dense: true,
                                title: Text("${line["product_name"]} x${line["quantity"]}"),
                                trailing: Text("₦${line["line_total"]}"),
                              );
                            }).toList(),
                          );
                        },
                      ),
                    ),
    );
  }
}