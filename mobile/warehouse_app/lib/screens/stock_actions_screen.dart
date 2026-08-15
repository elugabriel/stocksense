import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared/api_client.dart';

class StockActionsScreen extends StatefulWidget {
  const StockActionsScreen({super.key});

  @override
  State<StockActionsScreen> createState() => _StockActionsScreenState();
}

enum StockAction { add, receive, returnStock, transfer, damage, count }

class _StockActionsScreenState extends State<StockActionsScreen> {
  StockAction _selectedAction = StockAction.add;
  bool _isLoading = false;
  String? _message;
  bool _isError = false;

  final _productIdController = TextEditingController();
  final _warehouseIdController = TextEditingController();
  final _sourceWarehouseController = TextEditingController();
  final _destWarehouseController = TextEditingController();
  final _batchIdController = TextEditingController();
  final _lotNumberController = TextEditingController();
  final _quantityController = TextEditingController();
  final _unitCostController = TextEditingController();
  final _vendorRefController = TextEditingController();
  final _reasonController = TextEditingController();
  final _countedQtyController = TextEditingController();
  final _notesController = TextEditingController();

  String _returnDirection = "to_vendor";
  String _reasonCode = "damage";

  Map<String, String> get _endpoints => {
        "add": "/stock/add/",
        "receive": "/stock/receive/",
        "return": "/stock/return/",
        "transfer": "/stock/transfer/",
        "damage": "/stock/remove-damaged/",
        "count": "/stock/physical-count/",
      };

  Future<void> _submit() async {
    setState(() {
      _isLoading = true;
      _message = null;
    });

    Map<String, dynamic> body = {};
    String endpoint;

    switch (_selectedAction) {
      case StockAction.add:
        endpoint = _endpoints["add"]!;
        body = {
          "product_id": int.tryParse(_productIdController.text),
          "warehouse_id": int.tryParse(_warehouseIdController.text),
          "lot_number": _lotNumberController.text,
          "quantity": int.tryParse(_quantityController.text),
          if (_unitCostController.text.isNotEmpty) "unit_cost": _unitCostController.text,
        };
        break;
      case StockAction.receive:
        endpoint = _endpoints["receive"]!;
        body = {
          "product_id": int.tryParse(_productIdController.text),
          "warehouse_id": int.tryParse(_warehouseIdController.text),
          "lot_number": _lotNumberController.text,
          "quantity": int.tryParse(_quantityController.text),
          if (_unitCostController.text.isNotEmpty) "unit_cost": _unitCostController.text,
          "vendor_reference": _vendorRefController.text,
        };
        break;
      case StockAction.returnStock:
        endpoint = _endpoints["return"]!;
        body = {
          "product_id": int.tryParse(_productIdController.text),
          "warehouse_id": int.tryParse(_warehouseIdController.text),
          if (_batchIdController.text.isNotEmpty) "batch_id": int.tryParse(_batchIdController.text),
          "quantity": int.tryParse(_quantityController.text),
          "direction": _returnDirection,
          "is_resellable": true,
          "reason": _reasonController.text,
        };
        break;
      case StockAction.transfer:
        endpoint = _endpoints["transfer"]!;
        body = {
          "product_id": int.tryParse(_productIdController.text),
          "batch_id": int.tryParse(_batchIdController.text),
          "source_warehouse_id": int.tryParse(_sourceWarehouseController.text),
          "destination_warehouse_id": int.tryParse(_destWarehouseController.text),
          "quantity": int.tryParse(_quantityController.text),
          "notes": _notesController.text,
        };
        break;
      case StockAction.damage:
        endpoint = _endpoints["damage"]!;
        body = {
          "product_id": int.tryParse(_productIdController.text),
          "warehouse_id": int.tryParse(_warehouseIdController.text),
          "batch_id": int.tryParse(_batchIdController.text),
          "quantity": int.tryParse(_quantityController.text),
          "reason_code": _reasonCode,
          "reason_notes": _reasonController.text,
        };
        break;
      case StockAction.count:
        endpoint = _endpoints["count"]!;
        body = {
          "product_id": int.tryParse(_productIdController.text),
          "warehouse_id": int.tryParse(_warehouseIdController.text),
          "batch_id": int.tryParse(_batchIdController.text),
          "counted_quantity": int.tryParse(_countedQtyController.text),
          "notes": _notesController.text,
        };
        break;
    }

    final response = await ApiClient.post(endpoint, body);
    final data = jsonDecode(response.body);

    setState(() {
      _isLoading = false;
      if (response.statusCode == 200 || response.statusCode == 201) {
        _isError = false;
        _message = data["message"] ?? "Success";
      } else {
        _isError = true;
        _message = data.toString();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Stock Actions"),
        backgroundColor: const Color(0xFF1A2634),
        foregroundColor: Colors.white,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          DropdownButtonFormField<StockAction>(
            initialValue: _selectedAction,
            decoration: const InputDecoration(labelText: "Action", border: OutlineInputBorder()),
            items: const [
              DropdownMenuItem(value: StockAction.add, child: Text("Add New Stock")),
              DropdownMenuItem(value: StockAction.receive, child: Text("Receive from Vendor")),
              DropdownMenuItem(value: StockAction.returnStock, child: Text("Return (Vendor/Customer)")),
              DropdownMenuItem(value: StockAction.transfer, child: Text("Transfer Between Locations")),
              DropdownMenuItem(value: StockAction.damage, child: Text("Remove Damaged/Expired")),
              DropdownMenuItem(value: StockAction.count, child: Text("Physical Count Correction")),
            ],
            onChanged: (val) => setState(() {
              _selectedAction = val!;
              _message = null;
            }),
          ),
          const SizedBox(height: 16),
          ..._buildFieldsForAction(),
          const SizedBox(height: 20),
          if (_message != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(
                _message!,
                style: TextStyle(color: _isError ? Colors.red : Colors.green, fontWeight: FontWeight.w600),
              ),
            ),
          ElevatedButton(
            onPressed: _isLoading ? null : _submit,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF27AE60),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            child: _isLoading ? const CircularProgressIndicator(color: Colors.white) : const Text("Submit"),
          ),
        ],
      ),
    );
  }

  Widget _field(TextEditingController controller, String label, {TextInputType? type}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextField(
        controller: controller,
        keyboardType: type,
        decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
      ),
    );
  }

  List<Widget> _buildFieldsForAction() {
    switch (_selectedAction) {
      case StockAction.add:
        return [
          _field(_productIdController, "Product ID", type: TextInputType.number),
          _field(_warehouseIdController, "Warehouse ID", type: TextInputType.number),
          _field(_lotNumberController, "Lot Number"),
          _field(_quantityController, "Quantity", type: TextInputType.number),
          _field(_unitCostController, "Unit Cost (optional)", type: TextInputType.number),
        ];
      case StockAction.receive:
        return [
          _field(_productIdController, "Product ID", type: TextInputType.number),
          _field(_warehouseIdController, "Warehouse ID", type: TextInputType.number),
          _field(_lotNumberController, "Lot Number"),
          _field(_quantityController, "Quantity", type: TextInputType.number),
          _field(_unitCostController, "Unit Cost (optional)", type: TextInputType.number),
          _field(_vendorRefController, "Vendor Reference"),
        ];
      case StockAction.returnStock:
        return [
          _field(_productIdController, "Product ID", type: TextInputType.number),
          _field(_warehouseIdController, "Warehouse ID", type: TextInputType.number),
          _field(_batchIdController, "Batch ID (optional)", type: TextInputType.number),
          _field(_quantityController, "Quantity", type: TextInputType.number),
          DropdownButtonFormField<String>(
            initialValue: _returnDirection,
            decoration: const InputDecoration(labelText: "Direction", border: OutlineInputBorder()),
            items: const [
              DropdownMenuItem(value: "to_vendor", child: Text("To Vendor")),
              DropdownMenuItem(value: "from_customer", child: Text("From Customer")),
            ],
            onChanged: (val) => setState(() => _returnDirection = val!),
          ),
          const SizedBox(height: 12),
          _field(_reasonController, "Reason"),
        ];
      case StockAction.transfer:
        return [
          _field(_productIdController, "Product ID", type: TextInputType.number),
          _field(_batchIdController, "Batch ID", type: TextInputType.number),
          _field(_sourceWarehouseController, "Source Warehouse ID", type: TextInputType.number),
          _field(_destWarehouseController, "Destination Warehouse ID", type: TextInputType.number),
          _field(_quantityController, "Quantity", type: TextInputType.number),
          _field(_notesController, "Notes"),
        ];
      case StockAction.damage:
        return [
          _field(_productIdController, "Product ID", type: TextInputType.number),
          _field(_warehouseIdController, "Warehouse ID", type: TextInputType.number),
          _field(_batchIdController, "Batch ID", type: TextInputType.number),
          _field(_quantityController, "Quantity", type: TextInputType.number),
          DropdownButtonFormField<String>(
            initialValue: _reasonCode,
            decoration: const InputDecoration(labelText: "Reason Code", border: OutlineInputBorder()),
            items: const [
              DropdownMenuItem(value: "damage", child: Text("Damaged Goods")),
              DropdownMenuItem(value: "expiry", child: Text("Expired Goods")),
              DropdownMenuItem(value: "theft", child: Text("Theft/Loss")),
              DropdownMenuItem(value: "system_error", child: Text("System Error")),
              DropdownMenuItem(value: "other", child: Text("Other")),
            ],
            onChanged: (val) => setState(() => _reasonCode = val!),
          ),
          const SizedBox(height: 12),
          _field(_reasonController, "Reason Notes"),
        ];
      case StockAction.count:
        return [
          _field(_productIdController, "Product ID", type: TextInputType.number),
          _field(_warehouseIdController, "Warehouse ID", type: TextInputType.number),
          _field(_batchIdController, "Batch ID", type: TextInputType.number),
          _field(_countedQtyController, "Counted Quantity", type: TextInputType.number),
          _field(_notesController, "Notes"),
        ];
    }
  }
}