from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_naive
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseForbidden

from .models import Mesaj


def ana_sayfa(request):
    return render(request, "mesajlar/ana_sayfa.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("mesajlar:mesaj_olustur")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        email = (request.POST.get("email") or "").strip()
        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""
        next_url = request.POST.get("next") or request.GET.get("next")

        if not username or not email or not password1 or not password2:
            messages.error(request, "Tüm alanları doldur.")
            return render(request, "registration/register.html")

        if password1 != password2:
            messages.error(request, "Şifreler eşleşmiyor.")
            return render(request, "registration/register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Bu kullanıcı adı zaten alınmış.")
            return render(request, "registration/register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Bu e-posta zaten kayıtlı.")
            return render(request, "registration/register.html")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        login(request, user)

        if next_url:
            return redirect(next_url)
        return redirect("mesajlar:mesaj_olustur")

    return render(request, "registration/register.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("mesajlar:mesaj_olustur")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        next_url = request.POST.get("next") or request.GET.get("next")

        if not username or not password:
            messages.error(request, "Kullanıcı adı ve şifre gir.")
            return render(request, "registration/login.html")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if next_url:
                return redirect(next_url)
            return redirect("mesajlar:mesaj_olustur")

        messages.error(request, "Kullanıcı adı veya şifre hatalı.")
        return render(request, "registration/login.html")

    return render(request, "registration/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Çıkış yapıldı.")
    return redirect("mesajlar:ana_sayfa")


@login_required(login_url='/login/')
def mesaj_olustur(request):
    if request.method == "POST":
        baslik = (request.POST.get("baslik") or "").strip()
        alici_email = (request.POST.get("alici_email") or "").strip()
        icerik = (request.POST.get("icerik") or "").strip()
        acilma_tarihi_raw = (request.POST.get("acilma_tarihi") or "").strip()
        foto = request.FILES.get("foto")

        acilma_tarihi = parse_datetime(acilma_tarihi_raw)

        if acilma_tarihi and is_naive(acilma_tarihi):
            acilma_tarihi = make_aware(acilma_tarihi)

        if not baslik or not alici_email or not icerik or not acilma_tarihi:
            messages.error(request, "Tüm alanları doldur.")
            return render(request, "mesajlar/mesaj_olustur.html")

        if acilma_tarihi <= timezone.now():
            messages.error(request, "Açılma tarihi ileri bir zaman olmalı.")
            return render(request, "mesajlar/mesaj_olustur.html")

        mesaj = Mesaj.objects.create(
            gonderen=request.user,
            baslik=baslik,
            alici_email=alici_email,
            icerik=icerik,
            foto=foto,
            acilma_tarihi=acilma_tarihi,
        )

        acilis_linki = request.build_absolute_uri(f"/m/{mesaj.token}/")

        konu = "Size bir Kapsül Mesaj gönderildi"
        icerik_mail = (
            f"Merhaba,\n\n"
            f"Mesaj başlığı: {mesaj.baslik}\n\n"
            f"Mesaja ulaşmak için:\n{acilis_linki}"
        )

        try:
            send_mail(
                subject=konu,
                message=icerik_mail,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[alici_email],
                fail_silently=False,
            )
            messages.success(request, "Mesaj gönderildi.")
        except Exception as e:
            messages.warning(request, f"Mail gönderilemedi: {e}")

        return redirect("mesajlar:mesaj_detay", pk=mesaj.pk)

    return render(request, "mesajlar/mesaj_olustur.html")


@login_required
def mesaj_detay(request, pk):
    mesaj = get_object_or_404(Mesaj, pk=pk)

    if mesaj.gonderen != request.user:
        return HttpResponseForbidden("Yetkin yok.")

    if timezone.now() >= mesaj.acilma_tarihi:
        return render(request, "mesajlar/mesaj_ac.html", {"mesaj": mesaj})

    return render(request, "mesajlar/locked.html", {"mesaj": mesaj})


def mesaj_ac(request, token):
    mesaj = get_object_or_404(Mesaj, token=token)

    if timezone.now() >= mesaj.acilma_tarihi:
        return render(request, "mesajlar/mesaj_ac.html", {"mesaj": mesaj})

    return render(request, "mesajlar/locked.html", {"mesaj": mesaj})
