from django.contrib import admin
from .models import Branch, Warehouse, Category, Product, Batch, StockTransfer, StockMovement, StockAdjustment

admin.site.register(Branch)
admin.site.register(Warehouse)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Batch)
admin.site.register(StockTransfer)
admin.site.register(StockMovement)
admin.site.register(StockAdjustment)