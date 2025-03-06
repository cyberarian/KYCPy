import pytesseract
import cv2
import numpy as np
from PIL import Image
import streamlit as st
from datetime import datetime
import re
import google.generativeai as genai
from utils.ocr_processor import OCRProcessor
from dotenv import load_dotenv
import os
import io
import base64

class HybridDocumentVerifier:
    def __init__(self):
        self.ocr_processor = OCRProcessor()
        # Initialize Gemini
        try:
            # Load environment variables
            load_dotenv()
            
            # Try environment variable first, then fallback to streamlit secrets
            api_key = os.getenv("GEMINI_API_KEY") or st.secrets["api"]["GEMINI_API_KEY"]
            
            if not api_key:
                raise ValueError("Gemini API key not found in environment or secrets")
                
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
            st.success("✓ Gemini Vision initialized successfully")
        except Exception as e:
            st.error(f"Failed to initialize Gemini: {str(e)}")
            raise

    def verify_document(self, uploaded_file, doc_type, customer_data=None):
        """Perform hybrid document verification"""
        try:
            # Convert uploaded file to PIL Image
            image = Image.open(uploaded_file)
            
            # Convert to RGB mode if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array for OpenCV
            img_array = np.array(image)
            
            results = {
                "status": "pending",
                "ocr_results": None,
                "vision_results": None,
                "combined_data": {},
                "confidence_scores": {},
                "verification_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Step 1: OCR Analysis
            with st.spinner("Performing OCR analysis..."):
                results["ocr_results"] = self.ocr_processor.process_document(img_array, doc_type)
                st.success("✓ OCR Analysis completed")

            # Step 2: Gemini Vision Analysis
            with st.spinner("Performing Gemini Vision analysis..."):
                results["vision_results"] = self._analyze_with_gemini(image, doc_type)
                if results["vision_results"]:
                    st.success("✓ Gemini Vision Analysis completed")

            # Step 3: Cross-validate and combine results
            results["combined_data"] = self._combine_and_validate_results(
                results["ocr_results"],
                results["vision_results"],
                doc_type,
                customer_data
            )

            # Set final status
            results["status"] = "completed"
            return results

        except Exception as e:
            st.error(f"Verification error: {str(e)}")
            results["status"] = "failed"
            return results

    def _analyze_with_gemini(self, image, doc_type):
        """Analyze document using Gemini Vision"""
        try:
            # Convert PIL image to bytes for Gemini
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()

            # Prepare prompt based on document type
            prompt = self._get_document_prompt(doc_type)
            
            # Create content parts
            content = {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64.b64encode(img_byte_arr).decode('utf-8')
                    }}
                ]
            }
            
            # Generate content with image
            response = self.model.generate_content(content)
            
            return {
                "text": response.text,
                "confidence": 0.95,
                "model": "gemini-2.0-flash-exp",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            st.error(f"Gemini Vision Error: {str(e)}")
            return None

    def _get_document_prompt(self, doc_type):
        """Get specialized prompt for document type"""
        if doc_type == "ID Card (KTP)":
            return """Analyze this Indonesian ID Card (KTP) and extract:
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
            
        return "Please analyze this document and extract all relevant identification information."

    def _combine_and_validate_results(self, ocr_results, vision_results, doc_type, customer_data):
        """Enhanced combination and validation of results"""
        combined = {
            "extracted_fields": {},
            "validation_scores": {},
            "matches": {},
            "verification_status": "unverified"
        }

        if doc_type == "ID Card (KTP)":
            # Extract and validate NIK
            nik_ocr = ocr_results.get("parsed_data", {}).get("nik")
            nik_vision = self._extract_field_from_vision(vision_results, "NIK")
            combined["extracted_fields"]["nik"] = nik_ocr if nik_ocr else nik_vision

            # Extract and validate Name
            name_ocr = ocr_results.get("parsed_data", {}).get("name")
            name_vision = self._extract_field_from_vision(vision_results, "Name")
            combined["extracted_fields"]["name"] = name_ocr if name_ocr else name_vision

            # Validate against customer data if available
            if customer_data:
                combined["matches"] = self._validate_against_customer(
                    combined["extracted_fields"],
                    customer_data
                )

        # Calculate confidence scores
        combined["validation_scores"] = self._calculate_confidence_scores(
            ocr_results,
            vision_results,
            combined["matches"]
        )

        # Set verification status
        combined["verification_status"] = self._determine_verification_status(
            combined["validation_scores"],
            combined["matches"]
        )

        return combined

    def _extract_field_from_vision(self, vision_results, field_name):
        """Extract specific field from vision analysis"""
        if not vision_results or not vision_results.get("text"):
            return None

        text = vision_results["text"].lower()
        if field_name.lower() == "nik":
            match = re.search(r'nik[:\s]*(\d{16})', text)
            return match.group(1) if match else None
        elif field_name.lower() == "name":
            match = re.search(r'nama[:\s]*([^\n]+)', text)
            return match.group(1).strip().upper() if match else None
        return None

    def _combine_analyses(self, ocr_results, vision_results, doc_type, customer_data):
        """Combine and validate OCR and Vision results"""
        combined = {
            "ocr_data": ocr_results.get("parsed_data", {}),
            "vision_analysis": vision_results.get("text", "") if vision_results else "",
            "extracted_data": {},
            "verification_scores": {},
            "verification_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Extract and combine data based on document type
        if doc_type == "ID Card (KTP)":
            combined["extracted_data"] = self._extract_ktp_data(ocr_results, vision_results)
        
        # Calculate verification scores
        combined["verification_scores"] = self._calculate_verification_scores(
            combined["extracted_data"],
            customer_data,
            ocr_results.get("confidence", 0),
            vision_results.get("confidence", 0) if vision_results else 0
        )

        return combined

    def _enhance_results(self, ocr_results, vision_results, doc_type):
        """Enhance results by combining OCR and vision analysis"""
        enhanced = {
            "extracted_text": ocr_results.get("raw_text", ""),
            "structured_data": {},
            "confidence_scores": {}
        }

        if doc_type == "ID Card (KTP)":
            # Combine NIK detection
            nik_ocr = self.ocr_processor.extract_nik(ocr_results.get("raw_text", ""))
            nik_vision = self._extract_nik_from_vision(vision_results.get("extracted_text", ""))
            
            enhanced["structured_data"]["nik"] = nik_ocr if nik_ocr else nik_vision
            enhanced["confidence_scores"]["nik"] = 1.0 if nik_ocr == nik_vision else 0.5
            
            # Similar enhancement for other fields...

        return enhanced

    def _validate_results(self, enhanced_results, customer_data, doc_type):
        """Validate enhanced results against customer data"""
        validation = {
            "matches": {},
            "overall_confidence": 0.0,
            "verification_status": "Unverified"
        }

        if not customer_data:
            return validation

        # Perform field-by-field validation
        if doc_type == "ID Card (KTP)":
            nik_match = enhanced_results["structured_data"].get("nik") == customer_data.get("nik")
            name_match = self._calculate_name_similarity(
                enhanced_results["structured_data"].get("name", ""),
                customer_data.get("full_name", "")
            )
            
            validation["matches"] = {
                "nik": nik_match,
                "name": name_match > 0.8
            }
            
            # Calculate overall confidence
            confidence_scores = [
                1.0 if nik_match else 0.0,
                name_match
            ]
            validation["overall_confidence"] = sum(confidence_scores) / len(confidence_scores)
            
            # Set verification status
            if validation["overall_confidence"] > 0.8:
                validation["verification_status"] = "Verified"
            elif validation["overall_confidence"] > 0.5:
                validation["verification_status"] = "Manual Review Required"
            else:
                validation["verification_status"] = "Failed"

        return validation

    def _cross_validate_results(self, ocr_results, vision_results, doc_type, customer_data):
        """Cross-validate OCR and Vision model results"""
        # Calculate confidence scores
        ocr_confidence = ocr_results.get("confidence", 0) / 100
        vision_confidence = vision_results.get("confidence", 0)
        
        # Cross-validation logic
        validation_scores = {
            "text_extraction": max(ocr_confidence, vision_confidence),
            "data_validation": self._validate_extracted_data(
                ocr_results.get("parsed_data", {}),
                vision_results.get("extracted_text", ""),
                customer_data,
                doc_type
            ),
            "format_compliance": self._verify_document_format(ocr_results, doc_type)
        }
        
        # Calculate overall confidence
        validation_scores["overall"] = np.mean(list(validation_scores.values()))
        
        return {
            "ocr_data": ocr_results.get("parsed_data", {}),
            "vision_analysis": vision_results.get("extracted_text", ""),
            "confidence_scores": validation_scores,
            "verification_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _get_fallback_results(self):
        """Provide fallback results in case of failure"""
        return {
            "ocr_data": {},
            "vision_analysis": "Analysis failed",
            "confidence_scores": {
                "text_extraction": 0,
                "data_validation": 0,
                "format_compliance": 0,
                "overall": 0
            },
            "verification_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _validate_extracted_data(self, extracted_data, vision_text, customer_data, doc_type):
        """Validate extracted data against customer data"""
        if not customer_data or not extracted_data:
            return 0.5
            
        matches = []
        
        if doc_type == "ID Card (KTP)":
            if extracted_data.get("nik") == customer_data.get("nik"):
                matches.append(1.0)
            if extracted_data.get("name") and customer_data.get("full_name"):
                name_similarity = self._calculate_name_similarity(
                    extracted_data["name"],
                    customer_data["full_name"]
                )
                matches.append(name_similarity)
                
        return np.mean(matches) if matches else 0.5

    def _calculate_name_similarity(self, name1, name2):
        """Calculate similarity between two names"""
        if not name1 or not name2:
            return 0
            
        name1 = name1.lower().split()
        name2 = name2.lower().split()
        
        matches = sum(1 for n1 in name1 if any(n1 in n2 for n2 in name2))
        return matches / max(len(name1), len(name2))

    def _verify_document_format(self, ocr_results, doc_type):
        """Verify document format compliance"""
        # Implement format verification logic
        return 0.9  # Default score

    def _get_timestamp(self):
        """Get current timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _calculate_confidence_scores(self, ocr_results, vision_results, matches):
        """Calculate confidence scores for the verification process"""
        scores = {
            "ocr_confidence": ocr_results.get("confidence", 0) / 100 if ocr_results else 0,
            "vision_confidence": vision_results.get("confidence", 0) if vision_results else 0,
            "field_match": sum(matches.values()) / len(matches) if matches else 0,
            "overall": 0.0
        }
        
        # Calculate overall score
        weights = {
            "ocr_confidence": 0.3,
            "vision_confidence": 0.4,
            "field_match": 0.3
        }
        
        scores["overall"] = sum(
            scores[key] * weight
            for key, weight in weights.items()
        )
        
        return scores

    def _extract_ktp_data(self, ocr_results, vision_results):
        """Extract KTP-specific data from OCR and vision results"""
        ktp_data = {}
        
        # Get data from OCR
        if ocr_results and "parsed_data" in ocr_results:
            ktp_data.update(ocr_results["parsed_data"])
        
        # Get data from vision if OCR data is missing
        if vision_results and "text" in vision_results:
            if "nik" not in ktp_data or not ktp_data["nik"]:
                ktp_data["nik"] = self._extract_field_from_vision(vision_results, "NIK")
            if "name" not in ktp_data or not ktp_data["name"]:
                ktp_data["name"] = self._extract_field_from_vision(vision_results, "Name")
        
        return ktp_data

    def _determine_verification_status(self, validation_scores, matches):
        """Determine verification status based on scores and matches"""
        # Calculate overall validation score
        scores = validation_scores.copy()
        overall_score = scores.get("overall", 0)
        
        # Calculate match score
        match_score = sum(matches.values()) / len(matches) if matches else 0
        
        # Combine scores with weights
        final_score = (overall_score * 0.7) + (match_score * 0.3)
        
        # Determine status based on final score
        if final_score >= 0.8:
            return "Verified"
        elif final_score >= 0.5:
            return "Manual Review Required"
        else:
            return "Failed"

    def _validate_against_customer(self, extracted_fields, customer_data):
        """Validate extracted fields against customer data"""
        matches = {}
        
        # Compare NIK
        if "nik" in extracted_fields and "nik" in customer_data:
            matches["nik"] = extracted_fields["nik"] == customer_data["nik"]
            
        # Compare Name using similarity
        if "name" in extracted_fields and "full_name" in customer_data:
            name_similarity = self._calculate_name_similarity(
                extracted_fields["name"],
                customer_data["full_name"]
            )
            matches["name"] = name_similarity > 0.8
            
        return matches
