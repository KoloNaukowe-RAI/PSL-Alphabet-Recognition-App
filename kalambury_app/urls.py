

from django.urls import path
from .views import HomeView, StartGameView, ProcessVideoFrameView, LiveCameraFeedView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('start-game/', StartGameView.as_view(), name='start_game'),
    path('live-camera-feed/', LiveCameraFeedView.as_view(), name='live_camera_feed'),
]
