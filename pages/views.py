from django.shortcuts import render


def about(request):
    return render(request, 'pages/about.html')


def contact(request):
    return render(request, 'pages/contact.html')


def terms(request):
    return render(request, 'pages/terms.html')


def privacy(request):
    return render(request, 'pages/privacy.html')


def cancellation_policy(request):
    return render(request, 'pages/cancellation_policy.html')


def refund_policy(request):
    return render(request, 'pages/refund_policy.html')


def client_rules(request):
    return render(request, 'pages/client_rules.html')


def owner_rules(request):
    return render(request, 'pages/owner_rules.html')
