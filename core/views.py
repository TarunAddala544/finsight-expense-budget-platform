from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncMonth
import calendar
from datetime import date
from django.db.models import Sum
from datetime import date
from django.http import HttpResponse
import csv

from .forms import ExpenseForm, BudgetForm
from .models import Expense, Budget


@login_required(login_url='/accounts/login/')
def dashboard(request):
    today = date.today()

    # ---------------- DEFAULTS (CRITICAL FIX) ---------------- #
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))
    selected_month_name = date(selected_year, selected_month, 1).strftime('%B')

    # ---------------- EXPENSES ---------------- #
    expenses = Expense.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    )

    # ---------------- BUDGETS ---------------- #
    budgets = Budget.objects.filter(user=request.user)
    budget_data = []

    for budget in budgets:
        spent = (
            expenses
            .filter(category=budget.category)
            .aggregate(total=Sum('amount'))['total'] or 0
        )

        percent_used = (
            (spent / budget.monthly_limit) * 100
            if budget.monthly_limit else 0
        )

        budget_data.append({
            'id': budget.id,
            'category': budget.category.name,
            'limit': budget.monthly_limit,
            'spent': spent,
            'percent_used': round(percent_used, 2),
            'exceeded': spent > budget.monthly_limit,
        })

    # ---------------- MONTHLY CHART ---------------- #
    monthly_chart = (
        Expense.objects
        .filter(user=request.user)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    months = [m['month'].strftime('%b %Y') for m in monthly_chart]
    totals = [float(m['total']) for m in monthly_chart]

    # ---------------- CATEGORY CHART ---------------- #
    category_chart = (
        expenses
        .values('category__name')
        .annotate(total=Sum('amount'))
    )

    cat_labels = [c['category__name'] for c in category_chart]
    cat_totals = [float(c['total']) for c in category_chart]

    # ---------------- AVAILABLE MONTHS ---------------- #
    available_months = (
        Expense.objects
        .filter(user=request.user)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .distinct()
        .order_by('-month')
    )

    # 🔄 Auto-redirect if month is empty after delete
    if not expenses.exists() and available_months:
        latest = available_months[0]['month']
        return redirect(f'/dashboard/?month={latest.month}&year={latest.year}')

    # ---------------- SMART INSIGHTS ---------------- #
    insights = []

    if cat_totals:
        max_index = cat_totals.index(max(cat_totals))
        insights.append(
            f"Your highest spending category this month is {cat_labels[max_index]}."
        )

    for b in budget_data:
        if b['percent_used'] >= 100:
            insights.append(f"You have exceeded your {b['category']} budget.")
        elif b['percent_used'] >= 80:
            insights.append(f"You are close to exceeding your {b['category']} budget.")

    if len(totals) >= 3 and totals[-1] > totals[-2] > totals[-3]:
        insights.append(
            "Your expenses have increased for the last 3 consecutive months."
        )

    # ---------------- RENDER ---------------- #
    return render(
        request,
        'core/dashboard.html',
        {
            'expenses': expenses.order_by('-date'),
            'budget_data': budget_data,
            'months': months,
            'totals': totals,
            'cat_labels': cat_labels,
            'cat_totals': cat_totals,
            'insights': insights,
            'available_months': available_months,
            'selected_month': selected_month,
            'selected_year': selected_year,
            'selected_month_name': selected_month_name,
        }
    )





@login_required(login_url='/accounts/login/')
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm()

    return render(request, 'core/add_expense.html', {'form': form})


@login_required(login_url='/accounts/login/')
def set_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            return redirect('dashboard')
    else:
        form = BudgetForm()

    return render(request, 'core/set_budget.html', {'form': form})


@login_required(login_url='/accounts/login/')
def monthly_summary(request):
    data = (
        Expense.objects
        .filter(user=request.user)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    return render(request, 'core/monthly_summary.html', {'data': data})


@login_required(login_url='/accounts/login/')
def export_expenses_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Category', 'Amount', 'Description'])

    expenses = Expense.objects.filter(user=request.user)

    for e in expenses:
        writer.writerow([
            e.date,
            e.category.name,
            e.amount,
            e.description
        ])

    return response


@login_required(login_url='/accounts/login/')
def delete_expense(request, expense_id):
    expense = get_object_or_404(
        Expense,
        id=expense_id,
        user=request.user
    )

    if request.method == 'POST':
        expense.delete()
        return redirect('dashboard')

    return render(
        request,
        'core/confirm_delete.html',
        {'expense': expense}
    )

@login_required(login_url='/accounts/login/')
def delete_budget(request, budget_id):
    budget = get_object_or_404(
        Budget,
        id=budget_id,
        user=request.user   # 🔐 security
    )

    if request.method == 'POST':
        budget.delete()

    return redirect('dashboard')
