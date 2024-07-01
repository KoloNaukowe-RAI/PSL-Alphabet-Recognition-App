import numpy as np
import os
import firebase_admin
from firebase_admin import credentials, db

def load_data_from_db():
    # Initialize the Firebase Admin SDK
    cred = credentials.Certificate('../firebase-adminsdk.json')
    with open('../database_url.txt', 'r') as file:
        database_url = file.read()
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url
    })

    # Load the data
    data = db.reference('augmented_data').get()

    return data

# def load_data_from_db():
#     # Initialize the Firebase Admin SDK
#     cred = credentials.Certificate('../firebase-adminsdk.json')
#     with open('../database_url.txt', 'r') as file:
#         database_url = file.read().strip()
#     firebase_admin.initialize_app(cred, {
#         'databaseURL': database_url
#     })
#
#     ids_to_query = ['0', '1', '2']
#     all_data = []
#
#     # Perform queries for each id
#     ref = db.reference('augmented_data')
#     for id_val in ids_to_query:
#         query = ref.order_by_child('id').equal_to(id_val)
#         data = query.get()
#         if data:
#             all_data.append(data)
#
#     return all_data


if __name__ == '__main__':
    all_data = load_data_from_db()

    if all_data:
        labels = []
        data_array = []

        for data in all_data:
            for key, value in data.items():
                labels.append(value['label'])
                data_array.append(value['data'])

        # Convert lists to numpy arrays
        labels = np.array(labels)
        data_array = np.array(data_array)

        path_to_data = './data.npy'
        path_to_labels = './labels.npy'
        np.save(path_to_data, data_array)
        np.save(path_to_labels, labels)

        print("Labels:", labels)
        print("Data shape:", data_array.shape)
    else:
        print("No data found.")