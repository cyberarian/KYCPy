import os
from groq import Groq
from PIL import Image
import base64
import io
import streamlit as st
from config.config import get_env_variable

class GroqVisionClient:
    def __init__(self):
        api_key = get_env_variable("GROQ_API_KEY")
        if not api_key:
            api_key = st.secrets.get("GROQ_API_KEY")
        
        if not api_key:
            raise Exception("Groq API key not found in environment variables or secrets")
            
        self.client = Groq(api_key=api_key)
        
    def analyze_document(self, image, customer_data=None, context=None):
        """Analyze document using LLaMA vision model"""
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Prepare the prompt
        system_prompt = """You are an expert document analyzer for KYC verification.
        Analyze the document image and extract relevant information.
        If customer data is provided, verify if the information matches."""

        if context:
            system_prompt += f"\nDocument Context: {context}"
        
        user_prompt = "Analyze this document and extract key information like name, ID number, date of birth, and address."
        if customer_data:
            user_prompt += f"\nVerify if it matches: {str(customer_data)}"
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image", "image": f"data:image/jpeg;base64,{img_str}"}
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")
