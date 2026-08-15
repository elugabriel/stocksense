import 'package:flutter/material.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const CustomerApp());
}

class CustomerApp extends StatelessWidget {
  const CustomerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'StockSense Shop',
      theme: ThemeData(
        primaryColor: const Color(0xFF27AE60),
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF27AE60)),
        useMaterial3: true,
      ),
      home: const LoginScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}