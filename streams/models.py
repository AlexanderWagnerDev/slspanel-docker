# streams/models.py
from django.db import models

class Configuration(models.Model):
    language = models.CharField(max_length=10, default='en')

    def __str__(self):
        return f"Config({self.language})"