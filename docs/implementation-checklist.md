# NJSmartStock — Implementation Checklist

Development log of the full system (Django backend, FastAPI AI engine, web
frontend, Flutter mobile apps), phase by phase, from project start to the
current state. Checked items are committed and working; the final section
lists what's done locally but not yet committed.

**Stack:** Django + DRF + Channels/Daphne (ASGI) on PostgreSQL, Redis
(Memurai on Windows) for WebSockets/Celery, `simple_history` for audit
trails, a FastAPI microservice for forecasting/ML, a vanilla JS/HTML/CSS
frontend, and two Flutter apps (warehouse staff + customer) sharing a
`stocksense_shared` Dart package.

---

## Phase 0–5: Foundations
*(env setup, auth, RBAC, PostgreSQL/Redis, core models, real-time sync — 2026-07-26)*

- [x] Project scaffolding, `.gitignore`, split settings (`base.py` / `dev.py` / `prod.py`)
- [x] PostgreSQL + Redis wired in; Channels/Daphne ASGI app with a `routing.py` for WebSockets
- [x] `accounts` app: custom user model, JWT auth (`rest_framework_simplejwt`), role-based access control
- [x] Core domain models: `Product`, `Warehouse`, `Batch`, `StockTransfer`, `StockAdjustment`, `StockMovement` — all with `simple_history` historical tracking
- [x] Core REST endpoints and serializers for the above (`core/views.py`, `core/urls.py`)
- [x] Real-time stock sync groundwork over WebSockets

## Phase 6: Stock Update Module
*(2026-07-26)*

- [x] Stock **add**, **receive**, **return**, **transfer**, **damage removal** endpoints
- [x] **Physical count** endpoint
- [x] Serializer/validation coverage for each movement type (`core/serializers.py`, `core/views.py`)

## Frontend bootstrap
*(2026-07-27 → 2026-07-28)*

- [x] Login page
- [x] Dashboard page wired to live stock data
- [x] Product creation form
- [x] Movement history view
- [x] Warehouse/category endpoints exposed to the frontend
- [x] Edit/delete on products
- [x] Fixed navbar-overlap layout bug on dashboard/products pages

## Phase 7: Smart Inventory Alerts
*(2026-07-29)*

- [x] Alert detection triggers and `Alert` model
- [x] `alerts/services.py` detection logic (low stock, expiry, etc.)
- [x] Web alerts dashboard (`frontend/alerts.html`, `frontend/js/alerts.js`)
- [x] Email notification path
- [x] SMS scaffolding (Twilio dependency present)

## Phase 8: Vendor Management
*(2026-07-29)*

- [x] `Vendor` and `PurchaseOrder` models (+ history)
- [x] Vendor performance scoring
- [x] Cost trend tracking
- [x] Vendor REST endpoints and serializers

## Phase 9: Sales Management
*(2026-07-29)*

- [x] `Sale` / `SaleLine` models
- [x] Sales reporting endpoints
- [x] Overstock detection (`alerts/services.py` + `alerts/views.py`)

## Phase 10: AI Engine
*(2026-07-29)*

- [x] Standalone FastAPI service under `ai-engine/`
- [x] Forecasting models for demand
- [x] K-Means clustering for vendor segmentation
- [x] Model selection logic
- [x] Reorder recommendation endpoint(s)
- [x] `sales/services.py` bridge feeding data to the AI engine

## Phase 11: Financial Analytics
*(2026-08-01)*

- [x] Profit margin reporting
- [x] Batch-level unit cost tracking (migration + model field)
- [x] FIFO / weighted-average stock valuation (`core/services.py`)
- [x] Forecasted revenue endpoints (`sales/services.py`, `sales/views.py`)

## Phase 12: BI Dashboard
*(2026-08-02)*

- [x] Role-aware dashboard views
- [x] Configurable KPIs (`DashboardPreference` model + migration)
- [x] Forecast-vs-actual reporting
- [x] Warehouse and branch performance comparisons

## Frontend build-out
*(2026-08-04 → 2026-08-09)*

- [x] User management UI, dashboard wired to the role-aware backend endpoint
- [x] Vendors and Purchase Orders pages
- [x] POS-style sales page: barcode scanning, cart, printable receipt
- [x] Dashboard styling polish; fixed KPI-panel destruction bug; consolidated `dashboard.css`
- [x] AI Forecasting UI; fixed location-scoping permission bug; fixed AI Engine CORS
- [x] Warehouse/branch performance comparison UI
- [x] Sticky navbar with live alert-count badge

## Phase 13: AI Decision Support
*(2026-08-09)*

- [x] Product discontinuation detection
- [x] Best-vendor selection logic
- [x] Order-quantity optimization
- [x] Scheduled performance summaries (Celery beat task)
- [x] AI Decision Support UI: discontinuation candidates, best-vendor picks, order optimizer, performance summary

## Phase 14: Mobile + Customer-Facing Backend
*(2026-08-15)*

- [x] Role-based navigation across the frontend
- [x] Tablet-responsive CSS
- [x] `Order` / `OrderLine` models (+ history) and endpoints
- [x] Customer registration and product-catalog backend
- [x] **Warehouse app** (Flutter): barcode scan, dashboard, login, stock actions, alerts — scaffolded incl. native Windows runner
- [x] **Customer app** (Flutter): catalog, login, order history — scaffolded
- [x] `stocksense_shared` Dart package: shared API client, auth, models

---

## Phase 15 (in progress — not yet committed)

Working-tree changes on top of Phase 14, not yet in a commit:

- [x] **NJSmartStock rebrand** — all user-facing text renamed from "StockSense"; Python package/settings module deliberately left as `stocksense`
- [x] **GBP currency formatting** everywhere via `formatMoney()` (`frontend/js/api.js`, `mobile/shared/lib/api_client.dart`)
- [x] **Demo data seeding**: `seed_demo` management command (`core/management/commands/seed_demo.py`) — UK-based branches/warehouses (London, Manchester, Birmingham, Leeds), ~26 products, ~60 days of sales, demo logins for all roles (`demo1234`)
- [x] Branch/location model gains a `country` field (new migration `0013_branch_country_...`)
- [ ] New `frontend/js/locations-data.js` — not yet wired/verified end-to-end
- [x] Auth rate limiting (`RateLimitedTokenObtainPairView`, 5/min/IP) added, disabled in dev via `RATELIMIT_ENABLE = False`
- [~] Assorted fixes across `sales/views.py`, `sales/urls.py`, `alerts/services.py`, `alerts/tasks.py`, `core/models.py`, `core/serializers.py`, `ai-engine/app/main.py`, and matching frontend/mobile screens — **in progress, not yet committed or fully verified**

### Outstanding / not yet started

- [ ] Commit and phase-label the current working-tree changes above
- [ ] End-to-end verification of the `locations-data.js` + branch-country feature
- [ ] SMS alert delivery beyond scaffolding (Twilio integration is present but not confirmed live)
- [ ] Mobile apps: no evidence of a full run/build pass beyond scaffolding (README notes native folders were hand-written without a Flutter SDK in the generating environment)
