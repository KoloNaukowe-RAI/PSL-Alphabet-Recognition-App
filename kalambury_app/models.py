from django.db import models

class GameSession(models.Model):
    player_name = models.CharField(max_length=100)
    word = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player_name} - {self.word} ({self.timestamp})"

class Feedback(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    RATING_CHOICES = [(i, str(i)) for i in range(6)]

    name = models.CharField(max_length=15)
    email = models.EmailField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    ratingBefore = models.IntegerField(choices=RATING_CHOICES)
    ratingAfter = models.IntegerField(choices=RATING_CHOICES)
    message = models.TextField(max_length=100)

    def __str__(self):
        return self.name
