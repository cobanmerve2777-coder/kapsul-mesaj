from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Mesaj


@login_required(login_url="login")
def mesaj_olustur(request):
    if request.method == "POST":
        baslik = request.POST.get("baslik")
        icerik = request.POST.get("icerik")
        acilma_tarihi = request.POST.get("acilma_tarihi")

        if baslik and icerik and acilma_tarihi:
            Mesaj.objects.create(
                gonderen=request.user,
                baslik=baslik,
                icerik=icerik,
                acilma_tarihi=acilma_tarihi
            )

            messages.success(
                request,
                "Mesaj başarıyla kapsüle eklendi 🔒 Açılma tarihinde görünecek."
            )

            return redirect("mesaj_olustur")

    return render(request, "mesajlar/mesaj_olustur.html")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if not username or not password1 or not password2:
            messages.error(request, "Tüm alanları doldur.")
            return redirect("register")

        if password1 != password2:
            messages.error(request, "Şifreler uyuşmuyor.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Bu kullanıcı adı zaten alınmış.")
            return redirect("register")

        user = User.objects.create_user(username=username, password=password1)
        login(request, user)
        return redirect("mesaj_olustur")

    return render(request, "registration/register.html")








