from django.shortcuts import render


def auth_login(request):
    return render(request, "ui/mockups/auth/login.html", {})


def auth_register(request):
    return render(request, "ui/mockups/auth/register.html", {})


def auth_await_verification(request):
    email = request.GET.get("email", "casey@example.com")
    return render(request, "ui/mockups/auth/await_verification.html", {"email": email})


def auth_verify_email(request):
    state = request.GET.get("state", "success")
    if state not in ("success", "expired", "already_verified", "invalid"):
        state = "success"
    return render(request, "ui/mockups/auth/verify_email.html", {"state": state})


def auth_await_approval(request):
    email = request.GET.get("email", "casey@example.com")
    return render(request, "ui/mockups/auth/await_approval.html", {"email": email})


def auth_forgot_password(request):
    sent = bool(request.GET.get("sent"))
    return render(request, "ui/mockups/auth/forgot_password.html", {"sent": sent})


def auth_reset_password(request):
    state = request.GET.get("state", "form")
    return render(request, "ui/mockups/auth/reset_password.html", {"state": state})
