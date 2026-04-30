from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Ana sayfa direkt mesaj oluşturma olsun
    path("", views.mesaj_olustur, name="mesaj_olustur"),

    # Login / Logout
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Register
    path("register/", views.register_view, name="register"),
]


