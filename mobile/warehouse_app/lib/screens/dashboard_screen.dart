import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared/api_client.dart';
import 'login_screen.dart';
import 'barcode_scan_screen.dart';
import 'stock_actions_screen.dart';
import 'movement_history_screen.dart';
import 'alerts_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _alertCount = 0;

  @override
  void initState() {
    super.initState();
    _loadAlertCount();
  }

  Future<void> _loadAlertCount() async {
    final response = await ApiClient.get("/alerts/?resolved=false");
    print("Alert count API status: ${response.statusCode}, body: ${response.body}");
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final list = data is Map && data.containsKey("results") ? data["results"] : data;
      print("Parsed alert count: ${list.length}");
      if (mounted) setState(() => _alertCount = list.length);
    }
  }

  Future<void> _logout(BuildContext context) async {
    await ApiClient.clearTokens();
    if (context.mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const LoginScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4F5F7),
      appBar: AppBar(
        title: const Text("StockSense Warehouse"),
        backgroundColor: const Color(0xFF1A2634),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => _logout(context),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadAlertCount,
        child: GridView.count(
          padding: const EdgeInsets.all(20),
          crossAxisCount: 2,
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          children: [
            _DashboardTile(
              icon: Icons.qr_code_scanner,
              label: "Scan Barcode",
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const BarcodeScanScreen())),
            ),
            _DashboardTile(
              icon: Icons.inventory_2,
              label: "Stock Actions",
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const StockActionsScreen())),
            ),
            _DashboardTile(
              icon: Icons.history,
              label: "Movement History",
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MovementHistoryScreen())),
            ),
            _DashboardTile(
              icon: Icons.notifications,
              label: "Alerts",
              badgeCount: _alertCount,
              onTap: () async {
                await Navigator.push(context, MaterialPageRoute(builder: (_) => const AlertsScreen()));
                _loadAlertCount();
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _DashboardTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final int badgeCount;

  const _DashboardTile({
    required this.icon,
    required this.label,
    required this.onTap,
    this.badgeCount = 0,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(12),
      elevation: 1,
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Stack(
          children: [
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, size: 42, color: const Color(0xFF1A2634)),
                const SizedBox(height: 10),
                Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
              ],
            ),
            if (badgeCount > 0)
              Positioned(
                top: 8,
                right: 8,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.red,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.white, width: 1.5),
                  ),
                  child: Text(
                    badgeCount > 99 ? "99+" : "$badgeCount",
                    style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}