from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ExpenseCategory, Expense


@admin.register(ExpenseCategory) 
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'school')
    list_filter = ('school',)
    search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date', 'payment_status', 'school')
    list_filter = ('category', 'payment_status', 'school')
    search_fields = ('description',)
    date_hierarchy = 'date'
