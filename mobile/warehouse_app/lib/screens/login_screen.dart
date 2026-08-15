import 'package:flutter/material.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("StockSense Warehouse"),
        backgroundColor: const Color(0xFF1A2634),
        foregroundColor: Colors.white,
      ),
      body: const Center(
        child: Text("Login successful! Dashboard screen coming next."),
      ),
    );
  }
}