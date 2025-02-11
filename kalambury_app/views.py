import random
import numpy as np
import cv2
import mediapipe as mp
import os
import logging

from django.shortcuts import render, redirect
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .models import GameSession, Feedback
from .forms import FeedbackForm
from .camera import VideoCamera
import qrcode
from io import BytesIO
import base64
import time

mp_hands = mp.solutions.hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
camera = VideoCamera()
logger = logging.getLogger(__name__)
dataset = {
    "Zwierzęta": ["antylopa", "delfin", "dzik", "flaming", "koń", "kot", "krokodyl", "krowa", "leniwiec", "małpa", "niedźwiedź", "owca", "panda", "pies", "pingwin", "ptak", "ryba", "słoń", "szynszyl", "zebra"],
    "Owoce": ["ananas", "arbuz", "banan", "brzoskwinia", "cytryna", "jabłko", "kokos", "limonka", "malina", "pomarańcza", "śliwka", "truskawka", "winogrono"],
    "Warzywa": ["burak", "cebula", "cukinia", "dynia", "kalafior", "ogórek", "papryka", "pomidor", "sałata", "seler"],
    "Zawody": ["fryzjer", "kelner", "lekarz"]
}


class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')


class SignsView(View):
    def get(self, request):
        return render(request, 'signs.html')


class StartGameView(View):
    def get(self, request):
        player_name = cache.get('player_name', 'Unknown')
        difficulty = request.GET.get('difficulty', 'easy')
        handedness = request.GET.get('hand', 'Left')
        category, word, image_url = self.select_random_category_word_and_image(difficulty)
        cache.set('random_word', word)

        # Update the game session with a new word
        game_session = GameSession.objects.filter(player_name=player_name).last()
        if game_session:
            game_session.word = word
            game_session.save()

        cache.set(f'score_{player_name}', 0)
        cache.set('letters_to_show', [])
        cache.set('shown_letters', [])
        if handedness == 'left':
            cache.set('handedness', "Right")
        else:
            cache.set('handedness', "Left")
        print("Game reset")

        return JsonResponse({'category': category, 'word': word, 'image_url': image_url, 'score': 0})

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

class ResetGameView(View):
    def get(self, request):
        player_name = cache.get('player_name', 'Unknown')
        difficulty = request.GET.get('difficulty', 'easy')
        category, word, image_url = self.select_random_category_word_and_image(difficulty)
        cache.set('random_word', word)

        # Update the game session with a new word
        game_session = GameSession.objects.filter(player_name=player_name).last()
        if game_session:
            game_session.word = word
            game_session.save()

        cache.set('letters_to_show', [])
        cache.set('shown_letters', [])
        print("Game reset")

        return JsonResponse({'category': category, 'word': word, 'image_url': image_url, 'score': 0})

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

# Kalman Filter
class CV_KF:
    def __init__(self, n_points):
        self.n_points_ = n_points
        self.kfs = [self.init_kalman() for _ in range(n_points)]

    def init_kalman(self):
        kf = cv2.KalmanFilter(6, 3)
        kf.transitionMatrix = np.eye(6, dtype=np.float32)
        kf.measurementMatrix = np.zeros((3, 6), np.float32)
        kf.processNoiseCov = np.eye(6, dtype=np.float32) * 1e-4

        kf.measurementMatrix[0, 0] = 1
        kf.measurementMatrix[1, 1] = 1
        kf.measurementMatrix[2, 2] = 1
        kf.transitionMatrix[0, 3] = 1
        kf.transitionMatrix[1, 4] = 1
        kf.transitionMatrix[2, 5] = 1

        return kf

    def update_dt(self, dt):
        for kf in self.kfs:
            kf.transitionMatrix[0, 3] = dt * 1000
            kf.transitionMatrix[1, 4] = dt * 1000
            kf.transitionMatrix[2, 5] = dt * 1000

    def predict(self, points):
        preds = []
        for i, point in enumerate(points):
            if i >= self.n_points_:
                break
            input_point = np.float32(point)
            self.kfs[i].correct(input_point)
            prediction = self.kfs[i].predict()
            preds.append(prediction[:3].flatten())
        return preds

class LiveCameraFeedView(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = cache.get('model')
        self.random_word = cache.get('random_word')
        self.shown_letters = []
        self.data = []
        self.data_doubled = []
        self.letters_to_show = []
        self.word_to_signs()
        self.handedness = cache.get('handedness')
        self.label_dict = cache.get('labels')
        self.kf = CV_KF(21)
        self.prev_time = time.time()

    def __del__(self):
        del self.camera
        print("Camera released")

    def get_cached_data(self):
        self.letters_to_show = cache.get('letters_to_show', [])
        self.shown_letters = cache.get('shown_letters', [])
        self.data_doubled = []
        for val in self.data:
            self.data_doubled.append(val)
            self.data_doubled.append(val)
        self.handedness = cache.get('handedness')
        if not self.letters_to_show:
            self.data = []
            self.data_doubled = []
            self.random_word = cache.get('random_word')
            self.word_to_signs()
            cache.set('letters_to_show', self.letters_to_show)

    def word_to_signs(self):
        word = self.random_word
        if word is None:
            return
        word_len = len(word)
        i = 0
        while i < word_len:
            if i < word_len - 1:
                if word[i] == 'c':
                    if word[i + 1] == 'h':
                        self.letters_to_show.append('ch')
                        i += 1
                    elif word[i + 1] == 'z':
                        self.letters_to_show.append('cz')
                        i += 1
                    else:
                        self.letters_to_show.append(word[i])
                elif word[i] == 'r':
                    if word[i + 1] == 'z':
                        self.letters_to_show.append('rz')
                        i += 1
                    else:
                        self.letters_to_show.append(word[i])
                elif word[i] == 's':
                    if word[i + 1] == 'z':
                        self.letters_to_show.append('sz')
                        i += 1
                    else:
                        self.letters_to_show.append(word[i])
                else:
                    self.letters_to_show.append(word[i])
            else:
                self.letters_to_show.append(word[i])
            i += 1

    def get(self, request):
        reset_buffer = request.GET.get('reset_buffer', 'false').lower() == 'true'
        if reset_buffer:
            return JsonResponse({'status': 'Buffer cleared'})

        try:
            return StreamingHttpResponse(self.generate_frames(camera),
                                         content_type="multipart/x-mixed-replace; boundary=frame")
        except Exception as e:
            print("Error in LiveCameraFeedView.get:", e)
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
        self.get_cached_data()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_hands.process(frame_rgb)
        current_landmarks = []
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                if handedness.classification[0].label == self.handedness:
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp.solutions.hands.HAND_CONNECTIONS,
                        mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                        mp.solutions.drawing_styles.get_default_hand_connections_style()
                    )

                    for hand_landmark in hand_landmarks.landmark:
                        x = hand_landmark.x
                        if self.handedness == 'Right':
                            x = -1 * (x - 1)
                        current_landmarks.append(np.array([x, hand_landmark.y, hand_landmark.z]))

                    # Stabilize the points using Kalman Filter
                    current_time = time.time()
                    dt = current_time - self.prev_time
                    self.prev_time = current_time
                    self.kf.update_dt(dt)
                    stabilized_landmarks = self.kf.predict(current_landmarks)

                    cur_landmarks = np.array(stabilized_landmarks)[0:21, :].reshape(3 * 21)
                    self.data.append(cur_landmarks)
                    self.data_doubled.append(cur_landmarks)
                    self.data_doubled.append(cur_landmarks)

        if len(self.data) >= 30 and len(self.shown_letters) < len(self.letters_to_show):
            self.data_doubled = self.data_doubled[-60:]
            pred_double = self.model.predict(np.expand_dims(self.data_doubled, axis=0))[0]
            for index in np.argwhere(pred_double > 0.33):
                if list(self.label_dict.keys())[index[0]] == self.letters_to_show[len(self.shown_letters)]:
                    self.shown_letters.append(list(self.label_dict.keys())[index[0]])
                    player_name = cache.get('player_name', 'Unknown')
                    score = cache.get(f'score_{player_name}', 0)
                    score += 1
                    if len(self.shown_letters) == len(self.letters_to_show):
                        score += 10
                    cache.set(f'score_{player_name}', score)
                    cache.set('shown_letters', self.shown_letters)
                    self.data_doubled = []
                    self.data = []
                    break

        if len(self.data) >= 60 and len(self.shown_letters) < len(self.letters_to_show):
            self.data = self.data[-60:]
            pred = self.model.predict(np.expand_dims(self.data, axis=0))[0]
            for index in np.argwhere(pred > 0.33):
                if list(self.label_dict.keys())[index[0]] == self.letters_to_show[len(self.shown_letters)]:
                    self.shown_letters.append(list(self.label_dict.keys())[index[0]])
                    cache.set('shown_letters', self.shown_letters)
                    player_name = cache.get('player_name', 'Unknown')
                    score = cache.get(f'score_{player_name}', 0)
                    score += 1
                    if len(self.shown_letters) == len(self.letters_to_show):
                        score += 10
                    cache.set(f'score_{player_name}', score)
                    self.data_doubled = []
                    self.data = []
                    break

        return frame

class HandednessUpdateView(View):
    def get(self, request):
        handedness = request.GET.get('hand', 'Left')
        if handedness == 'left':
            cache.set('handedness', "Right")
        else:
            cache.set('handedness', "Left")
        return JsonResponse({'handedness': handedness})

class LiveFeedLettersView(View):
    def get(self, request):
        update_letters = request.GET.get('update_letters', 'false').lower() == 'true'
        if update_letters:
            shown_letters = cache.get('shown_letters', [])
            player_name = cache.get('player_name', 'Unknown')
            score = cache.get(f'score_{player_name}', 0)
            return JsonResponse({'shown_letters': shown_letters, 'score': score})
        return JsonResponse({'error': 'Invalid request'}, status=400)


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