from django.urls import path
from . import views

app_name = "mesajlar"

urlpatterns = [
    path("", views.ana_sayfa, name="ana_sayfa"),
    path("mesaj-olustur/", views.mesaj_olustur, name="mesaj_olustur"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("m/<uuid:token>/", views.mesaj_ac, name="mesaj_ac"),
    path("mesaj/<int:pk>/", views.mesaj_detay, name="mesaj_detay"),
]

