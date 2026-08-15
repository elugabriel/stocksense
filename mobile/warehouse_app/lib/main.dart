import 'package:flutter/material.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const WarehouseApp());
}

class WarehouseApp extends StatelessWidget {
  const WarehouseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'StockSense Warehouse',
      theme: ThemeData(
        primaryColor: const Color(0xFF1A2634),
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1A2634)),
        useMaterial3: true,
      ),
      home: const LoginScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}