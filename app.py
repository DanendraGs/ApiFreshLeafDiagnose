from flask import Flask, request, jsonify
import numpy as np
import tensorflow as tf
import firebase_admin
from firebase_admin import credentials, firestore
from io import BytesIO
from prevention_data import disease_prevention  # Import prevention data

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate('key-firestore.json')  # Path to your service account key
firebase_admin.initialize_app(cred)
db = firestore.client()

# Load the H5 model
model = tf.keras.models.load_model('model.h5')

# Get input shape from the model
input_shape = model.input_shape  # Example: (None, 224, 224, 3)
expected_height, expected_width, expected_channels = input_shape[1:]

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Server FreshLeafDiagnose Sedang Berjalan"})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get the image from the request
        img_file = request.files['image']
        img_bytes = img_file.read()

        # Resize the image to match model input shape
        img = tf.keras.preprocessing.image.load_img(
            BytesIO(img_bytes),
            target_size=(expected_height, expected_width)
        )
        img_array = tf.keras.preprocessing.image.img_to_array(img) / 255.0  # Normalize
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension

        # Predict with the model
        predictions = model.predict(img_array)

        # Log predictions for debugging
        print("Predictions:", predictions)

        # Determine the predicted class
        predicted_class_index = np.argmax(predictions, axis=1)[0]

        # Get class names from disease prevention data
        class_names = list(disease_prevention.keys())

        if predicted_class_index >= len(class_names):
            return jsonify({"error": "Predicted class index is out of range."}), 400

        result_class = class_names[predicted_class_index]
        print("Predicted Class:", result_class)  # Log predicted class

        # Extract plant name and disease from the result_class
        if "___" in result_class:
            plant_name, disease_name = result_class.split("___")
            plant_name = plant_name.replace("_", " ")
        else:
            plant_name = result_class.replace("_", " ")
            disease_name = "healthy"

        # Prepare response based on prediction
        if disease_name == "healthy":
            response = {"message": "Tanaman anda sehat", "plant": plant_name}
        else:
            # Check if the predicted class exists in disease prevention data
            disease_info = disease_prevention.get(result_class)
            if not disease_info:
                return jsonify({"error": f"Predicted class '{result_class}' not found in prevention data."}), 400

            response = {
                "plant": plant_name,
                "disease": disease_info["disease"],
                "prevention": disease_info["prevention"]
            }

        # Save prediction data to Firestore
        db.collection('predictions').add({
            "plant": plant_name,
            "disease": disease_info["disease"] if disease_name != "healthy" else "healthy",
            "response": response
        })

        return jsonify(response)

    except Exception as e:
        print("Error:", str(e))  # Log error for debugging
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
