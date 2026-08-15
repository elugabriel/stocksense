import 'package:flutter/material.dart';
import 'package:shared/api_client.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _username = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _firstName = TextEditingController();
  final _password = TextEditingController();
  bool _isLoading = false;
  String? _message;
  bool _isError = false;

  Future<void> _handleRegister() async {
    setState(() {
      _isLoading = true;
      _message = null;
    });

    final success = await ApiClient.register(
      username: _username.text.trim(),
      email: _email.text.trim(),
      password: _password.text,
      firstName: _firstName.text.trim(),
      phone: _phone.text.trim(),
    );

    setState(() {
      _isLoading = false;
      _isError = !success;
      _message = success ? "Account created! You can now log in." : "Registration failed. Try a different username.";
    });

    if (success) {
      await Future.delayed(const Duration(seconds: 1));
      if (mounted) Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Create Account"), backgroundColor: const Color(0xFF27AE60), foregroundColor: Colors.white),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(controller: _username, decoration: const InputDecoration(labelText: "Username", border: OutlineInputBorder())),
            const SizedBox(height: 12),
            TextField(controller: _firstName, decoration: const InputDecoration(labelText: "First Name", border: OutlineInputBorder())),
            const SizedBox(height: 12),
            TextField(controller: _email, decoration: const InputDecoration(labelText: "Email", border: OutlineInputBorder())),
            const SizedBox(height: 12),
            TextField(controller: _phone, decoration: const InputDecoration(labelText: "Phone", border: OutlineInputBorder())),
            const SizedBox(height: 12),
            TextField(controller: _password, obscureText: true, decoration: const InputDecoration(labelText: "Password", border: OutlineInputBorder())),
            const SizedBox(height: 20),
            if (_message != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(_message!, style: TextStyle(color: _isError ? Colors.red : Colors.green), textAlign: TextAlign.center),
              ),
            ElevatedButton(
              onPressed: _isLoading ? null : _handleRegister,
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF27AE60), foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 14)),
              child: _isLoading ? const CircularProgressIndicator(color: Colors.white) : const Text("Register"),
            ),
          ],
        ),
      ),
    );
  }
}