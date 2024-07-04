

from django.urls import path
from .views import HomeView, StartGameView, ProcessVideoFrameView, LiveCameraFeedView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('start-game/', StartGameView.as_view(), name='start-game'),
    path('process-frame/', ProcessVideoFrameView.as_view(), name='process-frame'),
    path('live-camera-feed/', LiveCameraFeedView.as_view(), name='live_camera_feed'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)