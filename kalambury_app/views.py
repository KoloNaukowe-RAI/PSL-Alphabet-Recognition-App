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

mp_hands = mp.solutions.hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

logger = logging.getLogger(__name__)

dataset = {
    "Zwierzęta": ["delfin", "dzik", "koń", "kot", "krowa", "małpa", "owca", "pies", "ptak", "ryba", "słoń", "zebra"],
    "Owoce": ["arbuz", "banan", "jabłko", "malina", "pomarańcza", "truskawka"],
    "Warzywa": ["burak", "cebula", "dynia", "sałata", "seler"],
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
        player_name = request.GET.get('player_name', 'Unknown')
        difficulty = request.GET.get('difficulty', 'easy')
        category, word, image_url = self.select_random_category_word_and_image(difficulty)
        cache.set('random_word', word)
        cache.set('player_name', player_name)
        score = cache.get(f'score_{player_name}', 0)

        # Save game session
        GameSession.objects.create(player_name=player_name, word=word)

        return JsonResponse({'category': category, 'word': word, 'image_url': image_url, 'score': score})

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


        shown_letters = cache.get('shown_letters', [])
        letters_to_show = cache.get('letters_to_show', [])
        if len(shown_letters) == len(letters_to_show):
            guessed_word = 'true'
            player_name = cache.get('player_name', 'Unknown')
            score = cache.get(f'score_{player_name}', 0)
            score += 10

            cache.set(f'score_{player_name}', score)

        cache.set(letters_to_show, [])
        cache.set(shown_letters, [])
        #LiveCameraFeedView.clear_buffer()

        score = cache.get(f'score_{player_name}', 0)

        return JsonResponse({'category': category, 'word': word, 'image_url': image_url, 'score': score})

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
    def get(self, request):
        reset_buffer = request.GET.get('reset_buffer', 'false').lower() == 'true'
        if reset_buffer:
            self.clear_buffer()
            print("Buffer cleared")
            return JsonResponse({'status': 'Buffer cleared'})

        try:
            return StreamingHttpResponse(self.generate_frames(VideoCamera()),
                                         content_type="multipart/x-mixed-replace; boundary=frame")
        except Exception as e:
            print("Error in ProcessVideoFrameView.get:", e)
            return JsonResponse({'error': 'Streaming error'}, status=500)

    def generate_frames(self, camera):
        while True:
            frame = camera.get_frame()
            frame_np = np.frombuffer(frame, dtype=np.uint8)
            frame_img = cv2.imdecode(frame_np, cv2.IMREAD_COLOR)
            processed_frame, landmarks = self.process_frame(frame_img)
            data = cache.get('data', [])
            if len(landmarks) > 0:
                data.append(landmarks)
                cache.set('data', data)

            _, jpeg = cv2.imencode('.jpg', processed_frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    def process_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_hands.process(frame_rgb)
        current_landmarks = []
        if results.multi_hand_landmarks:
            hand_to_use = cache.get('handedness')
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Check if the hand matches the selected handedness
                if handedness.classification[0].label == hand_to_use:
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp.solutions.hands.HAND_CONNECTIONS,
                        mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                        mp.solutions.drawing_styles.get_default_hand_connections_style()
                    )

                    for hand_landmark in hand_landmarks.landmark:
                        x = hand_landmark.x
                        if hand_to_use == 'Right':
                            x = -1 * (x - 1)
                        current_landmarks.append(np.array([x, hand_landmark.y, hand_landmark.z]))

        return frame, np.array(current_landmarks)

class ShownLettersView(View):
    def get(self, request):
        letters_to_show = cache.get('letters_to_show', [])
        shown_letters = cache.get('shown_letters', [])
        letters_to_show_string = ''.join(letters_to_show)
        shown_letters_string = ''.join(shown_letters)
        guessed_word = 'false'
        if len(shown_letters) == len(letters_to_show):
            guessed_word = 'true'

        return JsonResponse({'letters_to_show': letters_to_show_string, 'shown_letters': shown_letters_string, 'guessed_word': guessed_word})


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

    # @staticmethod
    # def clear_buffer_static():
    #     cache.set('handedness', '')
    #     cache.set('random_word', '')
    #     cache.set('shown_letters', [])
    #     cache.set('data', [])
    #     cache.set('data_doubled', [])
    #     cache.set('letters_to_show', [])

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
        print(self.letters_to_show)

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
            return StreamingHttpResponse(self.generate_frames(VideoCamera()),
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
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_hands.process(frame_rgb)
        current_landmarks = []
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Check if the hand matches the selected handedness
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
                    cur_landmarks = np.array(current_landmarks)[0:21, :].reshape(3 * 21)
                    self.data.append(cur_landmarks)
                    self.data_doubled.append(cur_landmarks)
                    self.data_doubled.append(cur_landmarks)

        print(self.letters_to_show)
        print(self.shown_letters)

        if len(self.data) >= 30 and len(self.shown_letters) < len(self.letters_to_show):
            self.data_doubled = self.data_doubled[-60:]
            pred_double = self.model.predict(np.expand_dims(self.data_doubled, axis=0))[0]
            for index in np.argwhere(pred_double > 0.33):
                if list(self.label_dict.keys())[index[0]] == self.letters_to_show[len(self.shown_letters)]:
                    self.shown_letters.append(list(self.label_dict.keys())[index[0]])
                    player_name = cache.get('player_name', 'Unknown')
                    score = cache.get(f'score_{player_name}', 0)
                    score += 1  # 1 point for each correctly shown letter
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
                    score += 1  # 1 point for each correctly shown letter
                    cache.set(f'score_{player_name}', score)
                    self.data_doubled = []
                    self.data = []
                    break

        # if len(self.shown_letters) == len(self.letters_to_show):
        #     player_name = cache.get('player_name', 'Unknown')
        #     score = cache.get(f'score_{player_name}', 0)
        #     if len(self.shown_letters) == len(self.letters_to_show):
        #         score += 10  # Bonus points for correctly showing the whole word
        #     cache.set(f'score_{player_name}', score)

        return frame


class LiveFeedLettersView(View):
    def get(self, request):
        update_letters = request.GET.get('update_letters', 'false').lower() == 'true'
        if update_letters:
            shown_letters = cache.get('shown_letters', [])
            return JsonResponse({'shown_letters': shown_letters})
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