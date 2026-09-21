import 'dart:convert';

import '../api_client.dart';
import 'token_storage.dart';

/// Wraps the SimpleJWT endpoints registered in `stocksense/urls.py`:
/// `POST /api/v1/auth/login/` and `POST /api/v1/auth/token/refresh/`
/// (the latter is handled internally by [ApiClient] on 401s).
class LoginService {
  LoginService(this._apiClient, {TokenStorage? tokenStorage})
      : _tokenStorage = tokenStorage ?? TokenStorage();

  final ApiClient _apiClient;
  final TokenStorage _tokenStorage;

  /// Logs in with username/password. Returns true and persists the
  /// access/refresh token pair on success; returns false on invalid
  /// credentials (a 401 from the token endpoint).
  Future<bool> login({required String username, required String password}) async {
    final response = await _apiClient.post(
      '/auth/login/',
      body: {'username': username, 'password': password},
    );

    if (response.statusCode != 200) return false;

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    await _tokenStorage.saveTokens(
      access: data['access'] as String,
      refresh: data['refresh'] as String,
    );
    return true;
  }

  Future<void> logout() => _tokenStorage.clear();

  Future<bool> isLoggedIn() => _tokenStorage.hasSession();
}
