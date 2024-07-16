from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['name', 'email', 'gender', 'ratingBefore', 'ratingAfter', 'message']
        widgets = {
            'ratingBefore': forms.RadioSelect(choices=Feedback.RATING_CHOICES),
            'ratingAfter': forms.RadioSelect(choices=Feedback.RATING_CHOICES),
        }
