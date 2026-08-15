import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared/api_client.dart';

class BarcodeScanScreen extends StatefulWidget {
  const BarcodeScanScreen({super.key});

  @override
  State<BarcodeScanScreen> createState() => _BarcodeScanScreenState();
}

class _BarcodeScanScreenState extends State<BarcodeScanScreen> {
  bool _isLoading = false;
  Map<String, dynamic>? _product;
  String? _error;
  bool _scanned = false;
  MobileScannerController? _controller;

  @override
  void initState() {
    super.initState();
    _controller = MobileScannerController(
      detectionSpeed: DetectionSpeed.normal,
      facing: CameraFacing.back,
    );
    print("Scanner controller created");
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _onDetect(BarcodeCapture capture) async {
    print("onDetect fired — ${capture.barcodes.length} barcode(s) in this frame");
    for (final b in capture.barcodes) {
      print("  format=${b.format}, rawValue=${b.rawValue}");
    }

    if (_scanned) {
      print("Already scanned, ignoring this detection");
      return;
    }
    if (capture.barcodes.isEmpty) return;

    final barcode = capture.barcodes.first.rawValue;
    if (barcode == null) {
      print("Detected barcode has null rawValue — could not decode value");
      return;
    }

    setState(() {
      _scanned = true;
      _isLoading = true;
      _error = null;
      _product = null;
    });

    print("Looking up product for barcode: $barcode");
    final response = await ApiClient.get("/products/lookup/?barcode=$barcode");
    print("API response status: ${response.statusCode}, body: ${response.body}");

    setState(() {
      _isLoading = false;
      if (response.statusCode == 200) {
        _product = jsonDecode(response.body);
      } else {
        _error = "No product found for barcode: $barcode";
      }
    });
  }

  void _scanAgain() {
    setState(() {
      _scanned = false;
      _product = null;
      _error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Scan Barcode"),
        backgroundColor: const Color(0xFF1A2634),
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          Expanded(
            flex: 3,
            child: _scanned
                ? Container(
                    color: Colors.black,
                    child: const Center(
                      child: Icon(Icons.check_circle, color: Colors.greenAccent, size: 60),
                    ),
                  )
                : MobileScanner(controller: _controller, onDetect: _onDetect),
          ),
          Expanded(
            flex: 2,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              color: const Color(0xFFF4F5F7),
              child: _buildResultArea(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultArea() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(_error!, style: const TextStyle(color: Colors.red), textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: _scanAgain, child: const Text("Scan Again")),
        ],
      );
    }
    if (_product != null) {
      return SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_product!["name"], style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            Text("SKU: ${_product!["sku"]}", style: const TextStyle(color: Colors.grey)),
            const SizedBox(height: 12),
            Text("Cost Price: ₦${_product!["cost_price"]}"),
            Text("Selling Price: ₦${_product!["selling_price"]}"),
            Text("Reorder Level: ${_product!["reorder_level"]}"),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: _scanAgain, child: const Text("Scan Next Item")),
          ],
        ),
      );
    }
    return const Center(child: Text("Point the camera at a barcode to scan."));
  }
}