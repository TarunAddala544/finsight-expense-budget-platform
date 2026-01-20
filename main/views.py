from django.shortcuts import render, redirect

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # name-based redirect
    return render(request, 'pages/landing.html')
