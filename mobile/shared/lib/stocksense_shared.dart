/// Barrel file — import this single file from either app to get the
/// full shared surface (API client, auth, models).
library stocksense_shared;

export 'api_client.dart';
export 'auth/login_service.dart';
export 'auth/token_storage.dart';
export 'models/product.dart';
export 'models/stock_movement.dart';
export 'models/sale.dart';
