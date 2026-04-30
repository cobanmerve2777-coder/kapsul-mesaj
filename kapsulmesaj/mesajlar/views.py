from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.timezone import get_current_timezone
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseForbidden

from datetime import datetime
import base64
import uuid
from django.core.files.base import ContentFile

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

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)

        return redirect("mesajlar:mesaj_olustur")

    return render(request, "registration/register.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("mesajlar:mesaj_olustur")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        if not username or not password:
            messages.error(request, "Kullanıcı adı ve şifre gir.")
            return render(request, "registration/login.html")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
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
        baslik = request.POST.get("baslik", "").strip()
        alici_email = request.POST.get("alici_email", "").strip()
        icerik = request.POST.get("icerik", "").strip()
        acilma_tarihi_raw = request.POST.get("acilma_tarihi", "").strip()
        foto = request.FILES.get("foto")

        # 🎤 SES
        audio_data = request.POST.get("audio_data")
        audio_file = None

        if audio_data and "base64," in audio_data:
            try:
                format, audio_str = audio_data.split(";base64,")

                if "audio/webm" in format:
                    ext = "webm"
                elif "audio/mp4" in format:
                    ext = "mp4"
                elif "audio/mpeg" in format:
                    ext = "mp3"
                else:
                    ext = "webm"

                file_name = f"{uuid.uuid4()}.{ext}"

                audio_file = ContentFile(
                    base64.b64decode(audio_str),
                    name=file_name
                )
            except Exception as e:
                print("AUDIO ERROR:", e)

        # 🔥 TARİH FIX (ASIL OLAY BURASI)
        try:
            naive_dt = datetime.fromisoformat(acilma_tarihi_raw)

            tz = get_current_timezone()
            acilma_tarihi = timezone.make_aware(naive_dt, tz)

        except:
            acilma_tarihi = None

        # ✅ validation
        if not baslik or not alici_email or not icerik or not acilma_tarihi:
            messages.error(request, "Tüm alanları doldur.")
            return render(request, "mesajlar/mesaj_olustur.html")

        # 🔥 KARŞILAŞTIRMA FIX
        if acilma_tarihi <= timezone.localtime():
            messages.error(request, "Açılma tarihi ileri bir zaman olmalı.")
            return render(request, "mesajlar/mesaj_olustur.html")

        # 💾 kayıt
        mesaj = Mesaj.objects.create(
            gonderen=request.user,
            baslik=baslik,
            alici_email=alici_email,
            icerik=icerik,
            foto=foto,
            audio=audio_file,
            acilma_tarihi=acilma_tarihi,
        )

        # 📧 mail
        acilis_linki = request.build_absolute_uri(f"/m/{mesaj.token}/")

        try:
            send_mail(
                subject="Size bir Kapsül Mesaj gönderildi",
                message=(
                    f"{request.user.username} sana bir kapsül mesaj bıraktı!\n\n"
                    f"Başlık: {mesaj.baslik}\n\n"
                    f"Açmak için:\n{acilis_linki}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[alici_email],
                fail_silently=False,
            )
            messages.success(request, "Mesaj ve mail gönderildi 🚀")
        except Exception as e:
            print("MAIL ERROR:", e)
            messages.error(request, "Mail gönderilemedi.")

        return redirect("mesajlar:mesaj_detay", pk=mesaj.pk)

    return render(request, "mesajlar/mesaj_olustur.html")


@login_required
def mesaj_detay(request, pk):
    mesaj = get_object_or_404(Mesaj, pk=pk)

    if mesaj.gonderen != request.user:
        return HttpResponseForbidden("Yetkin yok.")

    if timezone.localtime() >= mesaj.acilma_tarihi:
        return render(request, "mesajlar/mesaj_ac.html", {"mesaj": mesaj})

    return render(request, "mesajlar/locked.html", {"mesaj": mesaj})


def mesaj_ac(request, token):
    mesaj = get_object_or_404(Mesaj, token=token)

    if timezone.localtime() >= mesaj.acilma_tarihi:
        return render(request, "mesajlar/mesaj_ac.html", {"mesaj": mesaj})

    return render(request, "mesajlar/locked.html", {"mesaj": mesaj})