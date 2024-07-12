import random
import numpy as np
import cv2
import mediapipe as mp
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from .camera import VideoCamera
import os
from django.conf import settings
import qrcode
from io import BytesIO
import base64
from django.views.generic.edit import FormView
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import FeedbackForm

def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('feedback_thanks'))
    else:
        form = FeedbackForm()
    return render(request, 'feedback.html', {'form': form})

def feedback_thanks_view(request):
    return render(request, 'feedback_thanks.html')
    
class QRCodeView(View):
    def get(self, request):
        qr_text = "Twórcy dziękują Ci za grę w kalambury"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_text)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return render(request, 'qr_code.html', {'qr_code': img_str})

dataset = {
    "Zwierzęta": ["delfin", "dzik", "koń", "kot", "krowa", "małpa", "owca", "pies", "ptak", "ryba", "słoń", "zebra"],
    "Owoce": ["arbuz", "banan", "jabłko", "malina", "pomarańcza", "truskawka"],
    "Warzywa": ["burak", "cebula", "dynia", "sałata", "seler"],
    "Zawody": ["fryzjer", "kelner", "lekarz"]
}

mp_hands = mp.solutions.hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)


class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

class SignsView(View):
    def get(self, request):
        return render(request, 'signs.html')

class StartGameView(View):
    def get(self, request):
        difficulty = request.GET.get('difficulty', 'easy')
        category, word, image_url = self.select_random_category_word_and_image(difficulty)
        return JsonResponse({'category': category, 'word': word, 'image_url': image_url})

    def select_random_category_word_and_image(self, difficulty):
        filtered_dataset = self.filter_by_difficulty(difficulty)
        category = random.choice(list(filtered_dataset.keys()))
        word = random.choice(filtered_dataset[category])
        image_url = self.get_image_url(word)
        return category, word, image_url

    def filter_by_difficulty(self, difficulty):
        if difficulty == 'easy':
            max_length = 5
        elif difficulty == 'medium':
            max_length = 8
        else:
            max_length = 12

        filtered_dataset = {
            category: [word for word in words if len(word) <= max_length]
            for category, words in dataset.items()
        }
        return {k: v for k, v in filtered_dataset.items() if v}

    def get_image_url(self, word):
        image_path = os.path.join(settings.STATIC_URL, 'images_to_display', f'{word}.png')
        return image_path

class ProcessVideoFrameView(View):
    def post(self, request):
        frame_data = request.FILES['frame'].read()
        np_frame = np.frombuffer(frame_data, dtype=np.uint8)
        img = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

        result_img, landmarks = self.process_frame(img)
        _, img_encoded = cv2.imencode('.jpg', result_img)
        response = {
            'image': img_encoded.tobytes(),
            'landmarks': landmarks
        }
        return JsonResponse(response)

    def process_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_hands.process(frame_rgb)
        landmarks = []
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                landmarks.append([[landmark.x, landmark.y, landmark.z] for landmark in hand_landmarks.landmark])
        return frame, landmarks


class LiveCameraFeedView(View):
    def get(self, request):
        try:
            return StreamingHttpResponse(self.generate_frames(VideoCamera()),
                                         content_type="multipart/x-mixed-replace; boundary=frame")
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Streaming error'}, status=500)

    def generate_frames(self, camera):
        while True:
            frame = camera.get_frame()
            frame_np = np.frombuffer(frame, dtype=np.uint8)
            frame_img = cv2.imdecode(frame_np, cv2.IMREAD_COLOR)
            processed_frame = self.process_frame(frame_img)
            _, jpeg = cv2.imencode('.jpg', processed_frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    def process_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_hands.process(frame_rgb)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
        return frame
