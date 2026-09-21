# StockSense Mobile

Flutter workspace for the two StockSense mobile apps, plus the Dart
package they share.

```
mobile/
├── shared/          # stocksense_shared — API client, auth, models
├── warehouse_app/    # staff app (barcode scan, stock actions, alerts)
└── customer_app/     # public app (catalog, availability, orders)
```

`warehouse_app` and `customer_app` each depend on `shared` via a local
path dependency (`stocksense_shared: {path: ../shared}`), so a change
to the API client or a model lands in both apps at once.

## One-time setup

This scaffold was written by hand (no Flutter SDK was available in
the environment that generated it), so the native platform folders
that `flutter create` normally generates — `android/`, `ios/`, etc. —
don't exist yet. Generate them per app before you run anything:

```bash
cd mobile/shared && flutter create --template=package .
cd ../warehouse_app && flutter create --org com.stocksense --project-name warehouse_app .
cd ../customer_app && flutter create --org com.stocksense --project-name customer_app .
```

`flutter create .` on a directory that already has a `pubspec.yaml`
and `lib/` only fills in what's missing (platform folders, gradle
files, etc.) — it won't overwrite the files in this scaffold.

Then, from each of `shared/`, `warehouse_app/`, `customer_app/`:

```bash
flutter pub get
```

## Running an app

Point it at your Django backend with `--dart-define` (defaults to
`http://10.0.2.2:8000/api/v1`, the Android emulator's alias for the
host's `127.0.0.1` — override for a real device, iOS simulator, or a
deployed backend):

```bash
cd mobile/warehouse_app
flutter run --dart-define=STOCKSENSE_API_BASE_URL=http://192.168.1.20:8000/api/v1
```

Same pattern for `mobile/customer_app`.

## Current status

- **shared**: `ApiClient` (bearer-token attach + 401 refresh retry),
  `LoginService`/`TokenStorage`, and `Product`/`StockMovement`/`Sale`
  models — all wired to real endpoints under `stocksense/*/urls.py`.
- **warehouse_app**: login and barcode-scan-to-product-lookup are
  fully wired (`/products/lookup/`); movement history and alerts list
  from their real endpoints. The six stock-action forms
  (add/receive/return/transfer/remove-damaged/physical-count) are
  stubbed as a menu — each just needs a form screen POSTing to the
  endpoint already listed in `stock_actions_screen.dart`.
- **customer_app**: catalog and stock availability are fully wired.
  Cart, order history, and B2B reorder are functional client-side,
  but the backend has no cart/order/customer-identity model yet — see
  the doc comments in `cart_screen.dart` and `order_history_screen.dart`
  for exactly what's missing before checkout and "my orders" can be
  real.
