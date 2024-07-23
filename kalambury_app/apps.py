from django.apps import AppConfig
from keras.models import load_model
from django.core.cache import cache
import numpy as np
import os
import json

class KalamburyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kalambury_app'

    model_path = "./model/24_07_17_16_40_44_FINAL.h5"
    model = load_model(model_path)
    cache.set('model', model)

    cache.set('random_word', None)
    cache.set('handedness', 'Left')
    cache.set('letters_to_show', [])
    cache.set('shown_letters', [])

    with open(os.path.join("./model", "label_dict.json"), 'r', encoding='utf-8') as file:
        # Load the data from the file
        labels = json.load(file)
        cache.set('labels', labels)


