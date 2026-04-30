import uuid
from django.db import models
from django.contrib.auth.models import User

class Mesaj(models.Model):
    gonderen = models.ForeignKey(User, on_delete=models.CASCADE)
    alici_email = models.EmailField()
    baslik = models.CharField(max_length=200)
    icerik = models.TextField()
    acilma_tarihi = models.DateTimeField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    mail_gonderildi = models.BooleanField(default=False)
    acildi = models.BooleanField(default=False)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.baslik





