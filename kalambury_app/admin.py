from django.contrib import admin
from .models import Feedback, GameSession

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'gender', 'ratingBefore', 'ratingAfter', 'message')

admin.site.register(Feedback, FeedbackAdmin)

class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('player_name', 'word', 'timestamp')

admin.site.register(GameSession, GameSessionAdmin)
