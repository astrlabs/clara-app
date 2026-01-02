import google.generativeai as genai
import os
from clara_app.constants import API_KEY

if API_KEY:
    genai.configure(api_key=API_KEY)
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")
else:
    print("No API key found.")
