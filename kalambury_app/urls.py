from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    HomeView, SignsView, StartGameView, ProcessVideoFrameView,
    LiveCameraFeedView, feedback_view, feedback_thanks_view, QRCodeView, ResetGameView
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('signs/', SignsView.as_view(), name='signs'),
    path('start-game/', StartGameView.as_view(), name='start_game'),
    path('process-frame/', ProcessVideoFrameView.as_view(), name='process_frame'),
    path('live-camera-feed/', LiveCameraFeedView.as_view(), name='live_camera_feed'),
    path('feedback/', feedback_view, name='feedback'),
    path('feedback-thanks/', feedback_thanks_view, name='feedback_thanks'),
    path('qr_code/', QRCodeView.as_view(), name='qr_code'),
    path('reset-game/', ResetGameView.as_view(), name='reset_game'),  # Added path
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
