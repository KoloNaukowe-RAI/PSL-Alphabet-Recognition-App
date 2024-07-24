import os
from PIL import Image


current_dir = os.path.dirname(os.path.abspath(__file__))
folder_path = os.path.join(current_dir, "static", "images_to_display")


def process_images(folder_path):
    if not os.path.exists(folder_path):
        print(f"Ścieżka {folder_path} nie istnieje.")
        return

    for filename in os.listdir(folder_path):
        if filename.endswith(".png"):
            file_path = os.path.join(folder_path, filename)
            with Image.open(file_path) as img:
                img = img.resize((400, 400))
                img.save(file_path)
                print(f"Przetworzony obraz: {filename}")


process_images(folder_path)