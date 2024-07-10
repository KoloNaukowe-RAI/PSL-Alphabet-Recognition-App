import numpy as np
import os
import firebase_admin
from firebase_admin import credentials, db

# Initialize the Firebase Admin SDK
#cred = credentials.Certificate('../firebase-adminsdk.json')
#with open('../database_url.txt', 'r') as file:
#    database_url = file.read()
#firebase_admin.initialize_app(cred, {
#    'databaseURL': database_url
#})

#print(database_url)

def rotate_point(point, origin, rotation):
    # Convert rotation to radians
    rotation = np.deg2rad(rotation)

    # Translate point back to origin
    point = point - origin

    # Rotation matrix
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(rotation[0]), -np.sin(rotation[0])],
                   [0, np.sin(rotation[0]), np.cos(rotation[0])]])

    Ry = np.array([[np.cos(rotation[1]), 0, np.sin(rotation[1])],
                   [0, 1, 0],
                   [-np.sin(rotation[1]), 0, np.cos(rotation[1])]])

    Rz = np.array([[np.cos(rotation[2]), -np.sin(rotation[2]), 0],
                   [np.sin(rotation[2]), np.cos(rotation[2]), 0],
                   [0, 0, 1]])

    R = np.dot(Rz, np.dot(Ry, Rx))

    # Rotate your point
    rotated_point = np.dot(R, point)

    # Translate point back
    rotated_point = rotated_point + origin

    return rotated_point

def data_augmentation(path_to_data, path_to_labels, number_of_augmented_samples=10, min_rotation=-5, max_rotation=5, min_scale=0.9, max_scale=1.1):
    # Load the data
    data = np.load(path_to_data)
    labels = np.load(path_to_labels)

    # Augment the data
    augmented_data = []
    augmented_labels = []
    number_of_samples = data.shape[0]
    for i in range(number_of_samples):
        print("Currently augmenting sample: ", i + 1, "/", number_of_samples)

        # Add the original data
        augmented_data.append(data[i])
        augmented_labels.append(labels[i])

        # Generate random rotation and scale
        rotation = np.random.uniform(min_rotation, max_rotation, (number_of_augmented_samples, 3))
        scale = np.random.uniform(min_scale, max_scale, number_of_augmented_samples)

        # Iterate over the number of augmented samples and augment the data
        for j in range(number_of_augmented_samples):
            data_to_augment = np.copy(data[i])

            # Iterate over each frame
            for k in range(data_to_augment.shape[0]):
                # Get the coordinates of the first point (the first point won't be changed)
                first = data_to_augment[k, 0, :]

                # Iterate over each point in the frame
                for l in range(1, data_to_augment.shape[1]):
                    # Rescale and rotate the point
                    data_to_augment[k, l, :] += (data_to_augment[k, l, :] - first[:]) * (-1+scale[j])
                    data_to_augment[k, l, :] = rotate_point(data_to_augment[k, l, :], first[:], rotation[j])

            # Calculate min and max values and add translation
            min_x = np.min(data_to_augment[:, :, 0])
            max_x = np.max(data_to_augment[:, :, 0])
            min_y = np.min(data_to_augment[:, :, 1])
            max_y = np.max(data_to_augment[:, :, 1])
            min_z = np.min(data_to_augment[:, :, 2])
            max_z = np.max(data_to_augment[:, :, 2])

            translation_x = np.random.uniform(-min_x, 1 - max_x)
            translation_y = np.random.uniform(-min_y, 1 - max_y)
            translation_z = np.random.uniform(-min_z, 1 - max_z)
            data_to_augment[:, :, 0] += translation_x
            data_to_augment[:, :, 1] += translation_y
            data_to_augment[:, :, 2] += translation_z

            # Append the augmented data
            augmented_data.append(data_to_augment)
            augmented_labels.append(labels[i])

    # Convert lists to numpy arrays
    augmented_data = np.array(augmented_data)
    augmented_labels = np.array(augmented_labels)

    # Return the augmented data
    return augmented_data, augmented_labels

def save_to_firebase(augmented_data, augmented_labels):
    ref = db.reference('augmented_data')

    for i in range(augmented_data.shape[0]):
        data_entry = {
            'id': str(i),
            'label': str(augmented_labels[i]),
            'data': augmented_data[i].tolist()
        }
        ref.push(data_entry)
        print("Saved sample ", i, " to Firebase")

if __name__ == '__main__':
    path_to_data = os.path.join( '..', 'PL_Sign_Language_Letters_Recognition', 'data_for_models', '24_07_01_17_41_19', 'recorded_data.npy')
    path_to_labels = os.path.join( '..', 'PL_Sign_Language_Letters_Recognition', 'data_for_models', '24_07_01_17_41_19',
                                'labels.npy')
    augmented_data, augmented_labels = data_augmentation(path_to_data, path_to_labels)
    print(augmented_data.shape)

    path_to_save_data = os.path.join( '..', 'PL_Sign_Language_Letters_Recognition', 'data_for_models', '24_07_01_17_41_19', 'augmented_data.npy')
    path_to_save_labels = os.path.join( '..', 'PL_Sign_Language_Letters_Recognition', 'data_for_models', '24_07_01_17_41_19', 'augmented_labels.npy')
    np.save(path_to_save_data, augmented_data)
    np.save(path_to_save_labels, augmented_labels)

    #save_to_firebase(augmented_data, augmented_labels)