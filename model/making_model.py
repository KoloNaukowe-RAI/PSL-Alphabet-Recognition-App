import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.layers import Input, LSTM, BatchNormalization, Dense, Dropout
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, accuracy_score
import time
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

class SignLanguageModel:
    def __init__(self, data_dir, log_dir="Logs", model_dir="models"):
        self.data_dir = data_dir
        self.log_dir = log_dir
        self.model_dir = model_dir
        self.model = None
        self.history = None
        self.label_dict = None
        self.reverse_label_dict = None
        self.input_shape = (60, 21*3)

    def load_data(self):
        labels = np.load(os.path.join(self.data_dir, "augmented_labels.npy"))
        recorded_data = np.load(os.path.join(self.data_dir, "augmented_data.npy"))
        num_classes = len(set(labels))
        self.label_dict = {label: i for i, label in enumerate(sorted(set(labels)))}
        self.reverse_label_dict = {i: label for label, i in self.label_dict.items()} 
        
        labels_categorical = tf.keras.utils.to_categorical([self.label_dict[label] for label in labels])
        
        X_train, X_temp, y_train, y_temp = train_test_split(recorded_data, labels_categorical, test_size=0.2, random_state=None, stratify=labels_categorical)
        X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=None, stratify=y_temp)

        X_train = X_train.reshape(-1, 60, 21*3)
        X_val = X_val.reshape(-1, 60, 21*3)
        X_test = X_test.reshape(-1, 60, 21*3)
        
        return X_train, X_val, X_test, y_train, y_val, y_test, num_classes

    def build_model(self, num_classes):
        input_layer = Input(shape=self.input_shape)
        bn1 = BatchNormalization()(input_layer)
        lstm1 = LSTM(64, activation='relu', return_sequences=True)(bn1)
        dropout1 = Dropout(0.2)(lstm1)
        lstm2 = LSTM(64, activation='relu')(dropout1)
        dropout2 = Dropout(0.2)(lstm2)
        dense1 = Dense(64, activation='relu')(dropout2)
        dropout3 = Dropout(0.2)(dense1)
        dense2 = Dense(64, activation='relu')(dropout3)
        dropout4 = Dropout(0.2)(dense2)
        output_layer = Dense(num_classes, activation='softmax')(dropout4)
        model = Model(inputs=input_layer, outputs=output_layer)

        custom_adam = Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-07)
        model.compile(loss='categorical_crossentropy', optimizer=custom_adam, metrics=['categorical_accuracy'])
        model.summary()
        return model

    def train(self, X_train, y_train, X_val, y_val, num_classes):
        self.model = self.build_model(num_classes)
        tb_callback = TensorBoard(log_dir=self.log_dir)
        early_stopping_callback = EarlyStopping(monitor='val_categorical_accuracy', patience=5, restore_best_weights=True)
        reduce_lr_callback = ReduceLROnPlateau(monitor='val_categorical_accuracy', factor=0.2, patience=3, min_lr=0.0001)
        self.history = self.model.fit(X_train, y_train, epochs=41, batch_size=256, validation_data=(X_val, y_val), callbacks=[tb_callback, early_stopping_callback, reduce_lr_callback])

    def evaluate(self, X_test, y_test):
        loss, accuracy = self.model.evaluate(X_test, y_test)
        print("Test Loss:", loss)
        print("Test Accuracy:", accuracy)
        return loss, accuracy

    def evaluate_plot(self, X_test, y_test):
        y_test_argmax = np.argmax(y_test, axis=1)
        y_pred = self.model.predict(X_test)
        y_pred_argmax = np.argmax(y_pred, axis=1)
        
        conf_matrix = confusion_matrix(y_test_argmax, y_pred_argmax)
        acc_score = accuracy_score(y_test_argmax, y_pred_argmax)
        print("Accuracy Score:", acc_score)

        axis_labels = [self.reverse_label_dict[i] for i in range(len(self.reverse_label_dict))]

        fig, ax = plt.subplots(1, 2, figsize=(15, 6))
        sns.heatmap(conf_matrix, annot=True, fmt='d', ax=ax[0], cmap='Blues', xticklabels=axis_labels, yticklabels=axis_labels)
        ax[0].set_title('Confusion Matrix')
        ax[0].set_xlabel('Predicted Labels')
        ax[0].set_ylabel('True Labels')
        
        ax[1].plot(self.history.history['categorical_accuracy'], label='Training Accuracy', linestyle='--')
        ax[1].plot(self.history.history['val_categorical_accuracy'], label='Validation Accuracy', linestyle='--')
        ax[1].set_title('Training and Validation Loss & Accuracy')
        ax[1].set_xlabel('Epochs')
        ax[1].legend()

        plt.tight_layout()
        plt.show()

    def save_model(self):
        t = time.localtime()
        current_time = time.strftime("%y_%m_%d_%H_%M_%S", t)
        self.model.save(os.path.join(self.model_dir, current_time+".h5"))

data_dir = "data_for_models/24_07_17_15_33_35"
data_dir = os.path.join( '..', 'PL_Sign_Language_Letters_Recognition', 'data_for_models', '24_07_17_15_33_35')

if __name__ == '__main__':
    print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))
    sign_language_model = SignLanguageModel(data_dir)
    X_train, X_val, X_test, y_train, y_val, y_test, num_classes = sign_language_model.load_data()
    sign_language_model.train(X_train, y_train, X_val, y_val, num_classes)
    loss, accuracy = sign_language_model.evaluate(X_test, y_test)
    sign_language_model.evaluate_plot(X_test, y_test)  
    sign_language_model.save_model()
