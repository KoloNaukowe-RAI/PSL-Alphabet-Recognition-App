
import random
import os
import numpy as np
import cv2
import mediapipe as mp
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from .camera import VideoCamera

dataset = {
    "Zwierzęta": ["Pies", "Kot", "Słoń", "Lew", "Tygrys", "Małpa", "Krowa", "Kura", "Zebra", "Kangur"],
    "Owoce": ["Jabłko", "Banan", "Malina", "Winogrono", "Truskawka", "Ananas", "Mango", "Arbuz", "Agrest"],
    "Kraje": ["Polska", "Niemcy", "Francja", "Anglia", "Hiszpania", "Rosja", "Austria"],
    "Kolory": ["Czerwony", "Niebieski", "Zielony", "Żółty", "Fioletowy", "Pomarańczowy"],
    "Przedmioty": ["Telefon", "Laptop", "Telewizor", "Komoda", "Lampa", "Zegar"],
    "Zawody": ["Lekarz", "Poeta", "Policjant", "Informatyk", "Kucharz", "Kierowca", "Pilot"],
}

mp_hands = mp.solutions.hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

class StartGameView(View):
    def get(self, request):
        category, word = self.select_random_category_and_word()
        return JsonResponse({'category': category, 'word': word})

    def select_random_category_and_word(self):
        category = random.choice(list(dataset.keys()))
        word = random.choice(dataset[category])
        return category, word

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
            return StreamingHttpResponse(self.generate_frames(VideoCamera()), content_type="multipart/x-mixed-replace; boundary=frame")
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
