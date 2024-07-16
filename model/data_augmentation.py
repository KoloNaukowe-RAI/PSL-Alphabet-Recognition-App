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

def data_augmentation(path_to_dir, number_of_augmented_samples=10, min_rotation=-5, max_rotation=5, min_scale=0.9, max_scale=1.1):
    # Load the data
    data = np.load(os.path.join(path_to_dir, "recorded_data.npy"))
    labels = np.load(os.path.join(path_to_dir, "labels.npy"))
    data_long = np.load(os.path.join(path_to_dir, "recorded_data_long.npy"))
    labels_long = np.load(os.path.join(path_to_dir, "labels_long.npy"))

    # Check if the data has already been augmented and if so, delete it
    if os.path.exists(os.path.join(path_to_dir, 'augmented_data.npy')):
        os.remove(os.path.join(path_to_dir, 'augmented_data.npy'))
        os.remove(os.path.join(path_to_dir, 'augmented_labels.npy'))

    # Augment the data
    augmented_data = []
    augmented_labels = []
    number_of_samples = data.shape[0] + data_long.shape[0]
    data_len = data.shape[0]
    for i in range(number_of_samples):
        print("Currently augmenting sample: ", i + 1, "/", number_of_samples)

        # Add the original data
        if i < data_len:
            augmented_data.append(np.repeat(data[i], 2, axis=0))
            augmented_labels.append(labels[i])
        else:
            augmented_data.append(data_long[i - data_len])
            augmented_labels.append(labels_long[i - data_len])

        # Generate random rotation and scale
        rotation = np.random.uniform(min_rotation, max_rotation, (number_of_augmented_samples, 3))
        scale = np.random.uniform(min_scale, max_scale, number_of_augmented_samples)

        # Iterate over the number of augmented samples and augment the data
        for j in range(number_of_augmented_samples):
            if i < data_len:
                data_to_augment = np.copy(data[i])
            else:
                data_to_augment = np.copy(data_long[i - data_len])

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

            if i < data_len:
                # Duplicate each frame
                data_to_augment = np.repeat(data_to_augment, 2, axis=0)

            # Append the augmented data
            augmented_data.append(data_to_augment)
            augmented_labels.append(labels[i])

        if i % 100 == 1 or i == (number_of_samples - 1) and i != 0:
            # Save the augmented data to the disk to prevent memory issues and make it run faster
            augmented_data_np = np.array(augmented_data)
            augmented_labels_np = np.array(augmented_labels)

            if os.path.exists(os.path.join(path_to_dir, 'augmented_data.npy')):
                all_data = np.load(os.path.join(path_to_dir, 'augmented_data.npy'))
                all_labels = np.load(os.path.join(path_to_dir, 'augmented_labels.npy'))
                all_data = np.concatenate((all_data, augmented_data_np), axis=0)
                all_labels = np.concatenate((all_labels, augmented_labels_np), axis=0)
                np.save(os.path.join(path_to_dir, 'augmented_data.npy'), all_data)
                np.save(os.path.join(path_to_dir, 'augmented_labels.npy'), all_labels)
            else:
                np.save(os.path.join(path_to_dir, 'augmented_data.npy'), augmented_data_np)
                np.save(os.path.join(path_to_dir, 'augmented_labels.npy'), augmented_labels_np)
            augmented_data = []
            augmented_labels = []


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

    #ADD additional '..' if directories dont match or just navigate to designated folder with PL_Sign_Language
    dir_with_data = os.path.join( '..', '..', 'PL_Sign_Language_Letters_Recognition', 'data_for_models', '24_07_16_20_58_47')
    augmented_data, augmented_labels = data_augmentation(dir_with_data)
    print(augmented_data.shape)

    # path_to_save_data = os.path.join(dir_with_data, 'augmented_data.npy')
    # path_to_save_labels = os.path.join(dir_with_data, 'augmented_labels.npy')
    # np.save(path_to_save_data, augmented_data)
    # np.save(path_to_save_labels, augmented_labels)

    #save_to_firebase(augmented_data, augmented_labels)