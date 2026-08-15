import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiClient {
  static const String baseUrl = "http://127.0.0.1:8000/api/v1";

  static Future<String?> getAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString("access_token");
  }

  static Future<String?> getRefreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString("refresh_token");
  }

  static Future<void> saveTokens(String access, String refresh) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString("access_token", access);
    await prefs.setString("refresh_token", refresh);
  }

  static Future<void> clearTokens() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove("access_token");
    await prefs.remove("refresh_token");
  }

  static Future<bool> login(String username, String password) async {
    final response = await http.post(
      Uri.parse("$baseUrl/auth/login/"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"username": username, "password": password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await saveTokens(data["access"], data["refresh"]);
      return true;
    }
    return false;
  }

  static Future<bool> refreshAccessToken() async {
    final refresh = await getRefreshToken();
    if (refresh == null) return false;

    final response = await http.post(
      Uri.parse("$baseUrl/auth/token/refresh/"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"refresh": refresh}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString("access_token", data["access"]);
      return true;
    }
    return false;
  }

  static Future<http.Response> get(String endpoint) async {
    return _authenticatedRequest("GET", endpoint);
  }

  static Future<http.Response> post(String endpoint, Map<String, dynamic> body) async {
    return _authenticatedRequest("POST", endpoint, body: body);
  }

  static Future<http.Response> patch(String endpoint, Map<String, dynamic> body) async {
    return _authenticatedRequest("PATCH", endpoint, body: body);
  }

  static Future<http.Response> _authenticatedRequest(
    String method,
    String endpoint, {
    Map<String, dynamic>? body,
  }) async {
    String? token = await getAccessToken();
    var response = await _sendRequest(method, endpoint, token, body);

    if (response.statusCode == 401) {
      final refreshed = await refreshAccessToken();
      if (refreshed) {
        token = await getAccessToken();
        response = await _sendRequest(method, endpoint, token, body);
      }
    }

    return response;
  }

  static Future<http.Response> _sendRequest(
    String method,
    String endpoint,
    String? token,
    Map<String, dynamic>? body,
  ) async {
    final uri = Uri.parse("$baseUrl$endpoint");
    final headers = {
      "Content-Type": "application/json",
      if (token != null) "Authorization": "Bearer $token",
    };

    switch (method) {
      case "POST":
        return http.post(uri, headers: headers, body: jsonEncode(body));
      case "PATCH":
        return http.patch(uri, headers: headers, body: jsonEncode(body));
      default:
        return http.get(uri, headers: headers);
    }
  }

  static Future<bool> register({
    required String username,
    required String email,
    required String password,
    required String firstName,
    required String phone,
  }) async {
    final response = await http.post(
      Uri.parse("$baseUrl/auth/register/"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "username": username,
        "email": email,
        "password": password,
        "first_name": firstName,
        "phone": phone,
      }),
    );
    return response.statusCode == 201;
  }
}