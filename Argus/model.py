import os
from tensorflow.keras.models import load_model
import tensorflow as tf
import numpy as np


class Model:

  def __init__(self, hitStats):
    self.hitStats = hitStats
    self.prediction = None
    self.loaded_model = None

  def scan(self):
    model_filename = "Argus/enid.h5"
    if os.path.exists(model_filename):
      self.loaded_model = load_model(model_filename)
      array_data = np.array(eval(self.hitStats))
      preprocessed_new_data = array_data.reshape(-1, 8)

      # Make predictions
      predictions = self.loaded_model.predict(preprocessed_new_data)
      
      threshold = 0.44
      binary_predictions = (predictions > threshold).astype(int)
      self.prediction = binary_predictions[0][0]
    else:
      print("Missing Model File and/or Module filename is incorrect!")
