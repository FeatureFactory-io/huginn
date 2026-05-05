from django.shortcuts import render


def auth_login(request):
    return render(request, "ui/mockups/auth/login.html", {})
