from groq import Groq
import streamlit as st
import base64
import io
from PIL import Image
from datetime import datetime
import os

class GroqVisionClient:
    def __init__(self):
        try:
            # Try getting API key from different sources
            api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("No Groq API key found")
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.2-11b-vision-preview"
            st.success("✓ Groq Vision Client initialized successfully")
        except Exception as e:
            st.error(f"Failed to initialize Groq client: {str(e)}")
            raise

    def analyze_document(self, image, doc_type=None):
        """Analyze document using Llama vision through Groq"""
        try:
            # Show analysis progress
            with st.spinner("Analyzing document with Groq Vision..."):
                # Convert and process image
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                # Get appropriate prompt for document type
                system_prompt = self._get_document_prompt(doc_type)
                
                # Make API call
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": "Please analyze this document and verify its authenticity."},
                                {"type": "image", "image": f"data:image/jpeg;base64,{img_str}"}
                            ]
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )
                
                return {
                    "text": response.choices[0].message.content,
                    "confidence": 0.95,
                    "model": self.model,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

        except Exception as e:
            st.error(f"Groq Vision Analysis Error: {str(e)}")
            return None

    def _get_document_prompt(self, doc_type):
        """Get specialized prompt for document type"""
        if (doc_type == "ID Card (KTP)"):
            return """You are an expert document analyzer for KYC verification.
            Analyze this Indonesian ID Card (KTP) and extract:
            - NIK (16-digit number)
            - Full Name
            - Place and Date of Birth
            - Address details
            - Other KTP information
            Also verify:
            - Document authenticity markers
            - Photo area presence
            - Overall document quality
            Return in a clear, structured format."""
        
        # Add other document type prompts as needed
        return "Please analyze this document and extract all relevant identification information."

def test_groq_connection():
    """Test Groq API connection"""
    try:
        api_key = st.secrets["GROQ_API_KEY"]
        client = Groq(api_key=api_key)
        # Simple test request
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.1,
            max_tokens=10
        )
        st.success("✅ Groq connection successful!")
        return True
    except Exception as e:
        st.error(f"❌ Groq connection failed: {str(e)}")
        return False

def verify_groq_setup():
    """Verify Groq API setup"""
    try:
        api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
        if not api_key:
            st.error("❌ Groq API key not found")
            return False
            
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{"role": "user", "content": "Test connection"}],
            temperature=0.1,
            max_tokens=10
        )
        st.success("✅ Groq connection verified")
        return True
    except Exception as e:
        st.error(f"❌ Groq connection failed: {str(e)}")
        return False
