import os

# THIS MUST COME BEFORE IMPORT TENSORFLOW
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import tensorflow as tf
import numpy as np
from PIL import Image
from django.conf import settings

# --- NEW: Import the official ResNet50 translator ---
from tensorflow.keras.applications.resnet50 import preprocess_input

# Built-in Local Database for instant cure recommendations
DISEASE_DATABASE = {
    'Tomato___Early_blight': {
        'natural': 'Prune infected lower leaves. Apply copper-based organic soap or neem oil.',
        'chemical': 'Apply fungicides containing chlorothalonil or mancozeb.'
    },
    'Potato___Late_blight': {
        'natural': 'Destroy all infected plants immediately. Ensure good airflow and avoid overhead watering.',
        'chemical': 'Use systemic fungicides like mefenoxam or propamocarb.'
    },
    'Corn_(maize)___Common_rust_': {
        'natural': 'Plant rust-resistant varieties. Dust with sulfur powder early in the season.',
        'chemical': 'Apply fungicides containing azoxystrobin or pyraclostrobin at the first sign of pustules.'
    },
    'Apple___Apple_scab': {
        'natural': 'Rake and destroy fallen leaves to reduce spores. Apply organic neem oil.',
        'chemical': 'Use fungicides like captan or myclobutanil.'
    },
    'Tomato___healthy': {'natural': 'Plant is perfectly healthy!', 'chemical': 'None required.'},
    'Potato___healthy': {'natural': 'Plant is perfectly healthy!', 'chemical': 'None required.'},
    'Corn_(maize)___healthy': {'natural': 'Plant is perfectly healthy!', 'chemical': 'None required.'},
    'Apple___healthy': {'natural': 'Plant is perfectly healthy!', 'chemical': 'None required.'},
}


def predict_with_cnn(image_path):
    try:
        # 1. Load your new ResNet50 Model
        model_path = os.path.join(settings.BASE_DIR, 'RESNET50_PLANT_DISEASE.h5')
        model = tf.keras.models.load_model(model_path, compile=False)

        # 2. Preprocess the image
        # Force RGB format to prevent PNG transparency crashes
        img = Image.open(image_path).convert('RGB').resize((224, 224))

        # Convert to array (Notice we DO NOT divide by 255.0 anymore!)
        img_array = np.array(img, dtype=np.float32)
        img_array = np.expand_dims(img_array, axis=0)

        # Apply ResNet50's exact mathematical formatting
        img_array = preprocess_input(img_array)

        # 3. Get Predictions
        predictions = model.predict(img_array)[0]

        # 4. The exact 38 PlantVillage classes in alphabetical order
        classes = [
            'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy',
            'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew', 'Cherry_(including_sour)___healthy',
            'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Corn_(maize)___Common_rust_',
            'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy', 'Grape___Black_rot',
            'Grape___Esca_(Black_Measles)', 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy',
            'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot', 'Peach___healthy',
            'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy', 'Potato___Early_blight',
            'Potato___Late_blight', 'Potato___healthy', 'Raspberry___healthy', 'Soybean___healthy',
            'Squash___Powdery_mildew', 'Strawberry___Leaf_scorch', 'Strawberry___healthy',
            'Tomato___Bacterial_spot', 'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold',
            'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite', 'Tomato___Target_Spot',
            'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus', 'Tomato___healthy'
        ]

        # 5. Calculate Confidence Probability
        result_index = np.argmax(predictions)
        disease_name = classes[result_index]
        confidence_percentage = float(predictions[result_index] * 100)

        # 6. Lookup the cures
        # If the specific disease isn't in our dictionary yet, provide a fallback message
        cures = DISEASE_DATABASE.get(disease_name, {
            'natural': 'Specific organic cure pending. Please consult the Gemini AI tool for detailed natural remedies.',
            'chemical': 'Specific chemical cure pending. Please consult the Gemini AI tool for detailed pesticide recommendations.'
        })

        # Format the name to look nice for the user (e.g., "Tomato Early Blight")
        clean_name = disease_name.replace('___', ' - ').replace('_', ' ')

        # 7. Return the data dictionary
        return {
            'status': 'success',
            'disease': clean_name,
            'confidence': round(confidence_percentage, 2),
            'cures': cures
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f"Local AI Error: {str(e)}"
        }
# 3. Gemini AI Prediction
import json
from google import genai
from PIL import Image


def predict_with_gemini(image_path):
    # Ensure your key is pasted correctly here
    client = genai.Client(api_key="AIzaSyACGdnCl8T_rHunJ1x2_CBBgrGJmYBliJM")

    try:
        img = Image.open(image_path)
        model_id = "gemini-2.5-flash"

        # --- UPGRADED PROMPT ---
        # Now forcing Gemini to extract the plant's common and scientific names!
        prompt = """
        You are an expert agricultural plant pathologist. Analyze this plant image.

        Respond ONLY with a valid JSON object. Do NOT include markdown formatting like ```json.
        The JSON must have these exact 6 keys:
        "plant_name": "Common name of the plant (e.g., Tomato, Apple)",
        "biological_name": "Scientific/Biological name of the plant (e.g., Solanum lycopersicum)",
        "disease_name": "Exact Name of the disease (or 'Healthy Plant')",
        "confidence": A high-accuracy confidence percentage number (e.g., 98.5),
        "natural_cure": "A highly detailed, step-by-step organic and natural treatment plan.",
        "chemical_cure": "A highly detailed chemical pesticide recommendation."
        """

        response = client.models.generate_content(
            model=model_id,
            contents=[prompt, img]
        )

        # Clean the response in case Gemini accidentally adds markdown code blocks
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3].strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:-3].strip()

        # Convert the text into a Python Dictionary
        ai_data = json.loads(raw_text)

        # --- UPGRADED RETURN DICTIONARY ---
        # Now passing the plant identity back to your view!
        return {
            'status': 'success',
            'plant_name': ai_data.get('plant_name', 'Unknown Plant'),
            'biological_name': ai_data.get('biological_name', 'Unknown'),
            'disease': ai_data.get('disease_name', 'Unknown Diagnosis'),
            'confidence': float(ai_data.get('confidence', 95.0)),
            'cures': {
                'natural': ai_data.get('natural_cure', 'No natural cure provided.'),
                'chemical': ai_data.get('chemical_cure', 'No chemical cure provided.')
            }
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f"Gemini API Error: {str(e)}"
        }