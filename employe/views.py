from django.shortcuts import render, redirect

from employe.forms import EmployeForm
from employe.models import Employe

tmp_base = "employe/"
def dashmin(request):

    context = {
        "page_title": "Analytics"
    }
    return render(request, "dashboard.html", context)


def employe(request):
    form = EmployeForm()
    context = {
        "form": form,
        "page_title": "Employés"
    }
    return render(request, tmp_base + "add_employe.html", context)


def add_employe(request):
    if request.method == "POST":
        form_employe = EmployeForm(request.POST)
        if form_employe.is_valid():
            first_name = form_employe.cleaned_data['first_name']
            last_name = form_employe.cleaned_data['last_name']
            email = form_employe.cleaned_data['email']
            empploye = Employe.objects.create_user(first_name=first_name, last_name=last_name, email=email)
            empploye.save()

    return redirect("employe")
