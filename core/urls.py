from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),   # 👈 MAIN dashboard
    path('add-expense/', views.add_expense, name='add_expense'),
    path('set-budget/', views.set_budget, name='set_budget'),
    path('monthly-summary/', views.monthly_summary, name='monthly_summary'),
    path('export-csv/', views.export_expenses_csv, name='export_csv'),
    path('delete-expense/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    path('delete-budget/<int:budget_id>/', views.delete_budget, name='delete_budget'),

]
