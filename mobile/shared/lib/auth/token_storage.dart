import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Persists the JWT access/refresh token pair in the platform secure
/// store (Keychain on iOS, Keystore-backed EncryptedSharedPreferences
/// on Android) — never in plain SharedPreferences.
class TokenStorage {
  TokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _accessKey = 'stocksense_access_token';
  static const _refreshKey = 'stocksense_refresh_token';

  final FlutterSecureStorage _storage;

  Future<void> saveTokens({required String access, required String refresh}) async {
    await Future.wait([
      _storage.write(key: _accessKey, value: access),
      _storage.write(key: _refreshKey, value: refresh),
    ]);
  }

  Future<void> saveAccessToken(String access) =>
      _storage.write(key: _accessKey, value: access);

  Future<String?> readAccessToken() => _storage.read(key: _accessKey);

  Future<String?> readRefreshToken() => _storage.read(key: _refreshKey);

  Future<bool> hasSession() async => (await readAccessToken()) != null;

  Future<void> clear() async {
    await Future.wait([
      _storage.delete(key: _accessKey),
      _storage.delete(key: _refreshKey),
    ]);
  }
}
