from django.shortcuts import render


def dashmin(request):
    return render(request, "dashboard.html")
