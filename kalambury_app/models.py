from django.db import models

class Feedback(models.Model):
    name = models.CharField(max_length=15)
    email = models.EmailField()
    gender = models.CharField(max_length=10)
    ratingBefore = models.IntegerField()
    ratingAfter = models.IntegerField()
    message = models.TextField(max_length=100)

    def __str__(self):
        return self.name
