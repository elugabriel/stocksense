import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared/api_client.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  bool _isLoading = true;
  String? _error;
  List<dynamic> _alerts = [];

  @override
  void initState() {
    super.initState();
    _loadAlerts();
  }

  Future<void> _loadAlerts() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    final response = await ApiClient.get("/alerts/?resolved=false");

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final list = data is Map && data.containsKey("results") ? data["results"] : data;
      setState(() {
        _alerts = list;
        _isLoading = false;
      });
    } else {
      setState(() {
        _error = "Failed to load alerts.";
        _isLoading = false;
      });
    }
  }

  Future<void> _resolveAlert(int id) async {
    final response = await ApiClient.post("/alerts/$id/resolve/", {});
    if (response.statusCode == 200) {
      _loadAlerts();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Failed to resolve alert.")),
      );
    }
  }

  Color _severityColor(String severity) {
    switch (severity) {
      case "critical":
        return Colors.red;
      case "warning":
        return Colors.orange;
      default:
        return Colors.blue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Alerts"),
        backgroundColor: const Color(0xFF1A2634),
        foregroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadAlerts),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : _alerts.isEmpty
                  ? const Center(child: Text("No active alerts. All clear!"))
                  : RefreshIndicator(
                      onRefresh: _loadAlerts,
                      child: ListView.separated(
                        padding: const EdgeInsets.all(12),
                        itemCount: _alerts.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (context, index) {
                          final a = _alerts[index];
                          final severity = a["severity"] ?? "info";
                          final color = _severityColor(severity);

                          return Padding(
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  margin: const EdgeInsets.only(top: 4, right: 12),
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: color.withOpacity(0.15),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Text(
                                    severity.toUpperCase(),
                                    style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold),
                                  ),
                                ),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(a["message"] ?? "", style: const TextStyle(fontSize: 14)),
                                      const SizedBox(height: 4),
                                      TextButton(
                                        style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: Size.zero),
                                        onPressed: () => _resolveAlert(a["id"]),
                                        child: const Text("Resolve"),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}