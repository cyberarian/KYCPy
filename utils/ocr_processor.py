import pytesseract
import cv2
import numpy as np
from PIL import Image
import streamlit as st
from datetime import datetime
import re

class OCRProcessor:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        # Enhanced OCR configuration
        self.custom_config = r'--oem 3 --psm 6 -l ind+eng --dpi 300'

    def extract_nik(self, text):
        """Extract NIK with advanced pattern matching"""
        if not text:
            return None
            
        nik_patterns = [
            r'\b\d{16}\b',  # Basic 16-digit pattern
            r'NIK[:\s]*(\d{16})',  # NIK label pattern
            r'(?:^|\s)(\d{6}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{6})(?:$|\s)'  # Structured NIK pattern
        ]
        
        for pattern in nik_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1) if len(match.groups()) > 0 else match.group(0)
        return None

    def extract_name(self, text):
        """Extract name with advanced pattern matching"""
        if not text:
            return None
            
        name_patterns = [
            r'Nama[:\s]+([^\n]+)',
            r'Name[:\s]+([^\n]+)',
            r'(?<=\n)([A-Z][A-Z\s]+)(?=\n)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def process_document(self, image, doc_type):
        """Process document and return structured data"""
        results = {
            "raw_text": "",
            "parsed_data": {},
            "confidence": 0,
            "debug_info": {}
        }
        
        try:
            preprocessed_images = self._preprocess_image(image)
            best_result = self._extract_best_text(preprocessed_images)
            
            results["raw_text"] = best_result["text"]
            results["confidence"] = best_result["confidence"]
            
            # Parse data based on document type
            if doc_type == "ID Card (KTP)":
                parsed_data = {
                    "nik": self.extract_nik(best_result["text"]),
                    "name": self.extract_name(best_result["text"]),
                    # ... other fields ...
                }
                results["parsed_data"] = parsed_data
            
            return results
            
        except Exception as e:
            st.error(f"OCR Processing Error: {str(e)}")
            return results

    def _preprocess_image(self, image):
        """Advanced image preprocessing pipeline"""
        img_array = np.array(image)
        preprocessed = []

        # Basic grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        preprocessed.append(gray)

        # Adaptive thresholding
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        preprocessed.append(adaptive)

        # Denoising + Otsu's thresholding
        denoised = cv2.fastNlMeansDenoising(gray)
        _, otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed.append(otsu)

        # Deskewing if needed
        try:
            coords = np.column_stack(np.where(gray > 0))
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = 90 + angle
            center = tuple(np.array(gray.shape[1::-1]) / 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            deskewed = cv2.warpAffine(gray, matrix, gray.shape[1::-1], flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            preprocessed.append(deskewed)
        except Exception as e:
            st.warning(f"Deskewing failed: {str(e)}")

        return preprocessed

    def _extract_best_text(self, preprocessed_images):
        """Extract text from preprocessed images and return best result"""
        best_result = {"text": "", "confidence": 0}
        
        for img in preprocessed_images:
            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                
                # Calculate confidence
                valid_confidences = [float(conf) for conf in data['conf'] if conf != '-1']
                if valid_confidences:
                    confidence = sum(valid_confidences) / len(valid_confidences)
                    
                    # Get text
                    text = " ".join([word for word in data['text'] if word.strip()])
                    
                    if confidence > best_result["confidence"]:
                        best_result = {
                            "text": text,
                            "confidence": confidence
                        }
            except Exception as e:
                st.warning(f"OCR extraction error: {str(e)}")
                continue
                
        return best_result

    def _extract_text(self, image):
        """Extract text with multiple configurations"""
        results = {
            "raw_text": "",
            "confidence": 0,
            "blocks": [],
            "debug_info": {}
        }

        try:
            # Default configuration
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, 
                                           config=self.custom_config)
            
            # Extract text blocks with confidence
            high_conf_blocks = []
            for i, conf in enumerate(data['conf']):
                if conf > 0:  # Valid confidence value
                    text = data['text'][i].strip()
                    if text:
                        high_conf_blocks.append({
                            'text': text,
                            'conf': float(conf),
                            'bbox': (data['left'][i], data['top'][i], 
                                   data['width'][i], data['height'][i]),
                            'line_num': data['line_num'][i]
                        })

            # Sort blocks by vertical position for proper reading order
            high_conf_blocks.sort(key=lambda x: (x['line_num'], x['bbox'][0]))
            
            # Combine text with proper spacing
            text_lines = {}
            for block in high_conf_blocks:
                line_num = block['line_num']
                if line_num not in text_lines:
                    text_lines[line_num] = []
                text_lines[line_num].append(block['text'])

            # Join lines with proper spacing
            results["raw_text"] = "\n".join([" ".join(line) for line in text_lines.values()])
            
            # Calculate confidence scores
            valid_confidences = [block['conf'] for block in high_conf_blocks]
            results["confidence"] = np.mean(valid_confidences) if valid_confidences else 0
            results["blocks"] = high_conf_blocks

            # Add debug information
            results["debug_info"] = {
                "total_blocks": len(high_conf_blocks),
                "avg_confidence": results["confidence"],
                "recognized_chars": len(results["raw_text"]),
                "processing_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            st.error(f"OCR Error: {str(e)}")
            results["debug_info"]["error"] = str(e)

        return results

    def _display_debug_info(self, results):
        """Display debug information for OCR results"""
        with st.expander("OCR Debug Information"):
            st.write("OCR Processing Details:")
            st.write(f"- Total text blocks: {results['debug_info'].get('total_blocks', 0)}")
            st.write(f"- Average confidence: {results['debug_info'].get('avg_confidence', 0):.2f}%")
            st.write(f"- Recognized characters: {results['debug_info'].get('recognized_chars', 0)}")
            st.write(f"- Processing time: {results['debug_info'].get('processing_time', 'N/A')}")
            
            if "error" in results["debug_info"]:
                st.error(f"Error during processing: {results['debug_info']['error']}")

    def _parse_document_data(self, text, doc_type):
        """Parse document-specific data from OCR results"""
        if not text:
            return {}
            
        text = text.lower()
        
        if doc_type == "ID Card (KTP)":
            return self._parse_ktp_data(text)
        elif doc_type == "Tax ID (NPWP)":
            return self._parse_npwp_data(text)
        elif doc_type == "Passport":
            return self._parse_passport_data(text)
        else:
            return self._parse_generic_data(text)

    def _parse_ktp_data(self, text):
        """Parse KTP-specific data"""
        data = {
            "nik": None,
            "name": None,
            "birth_info": None,
            "gender": None,
            "address": None,
            "rt_rw": None,
            "religion": None,
            "marital_status": None,
            "occupation": None
        }
        
        # Find NIK (16 digits) using the extract_nik method
        data["nik"] = self.extract_nik(text)
        
        # Find name using the extract_name method
        data["name"] = self.extract_name(text)
        
        # Find birth info
        birth_match = re.search(r'lahir[:\s]+([^\n]+)', text)
        if birth_match:
            data["birth_info"] = birth_match.group(1).strip()
        
        # Find gender
        if "laki-laki" in text or "pria" in text:
            data["gender"] = "LAKI-LAKI"
        elif "perempuan" in text or "wanita" in text:
            data["gender"] = "PEREMPUAN"
        
        # Find address
        address_match = re.search(r'alamat[:\s]+([^\n]+)', text)
        if address_match:
            data["address"] = address_match.group(1).strip()
        
        # Find RT/RW
        rt_rw_match = re.search(r'\b(?:rt|rt/rw)[:\s]+(\d+/\d+)\b', text)
        if rt_rw_match:
            data["rt_rw"] = rt_rw_match.group(1)
        
        return data

    def _parse_npwp_data(self, text):
        """Parse NPWP-specific data"""
        data = {
            "npwp_number": None,
            "name": None,
            "address": None
        }
        
        # Find NPWP number (XX.XXX.XXX.X-XXX.XXX format)
        npwp_match = re.search(r'\b\d{2}.\d{3}.\d{3}.\d{1}-\d{3}.\d{3}\b', text)
        if npwp_match:
            data["npwp_number"] = npwp_match.group()
        
        # Find name using the extract_name method
        data["name"] = self.extract_name(text)
        
        # Find address
        address_match = re.search(r'alamat[:\s]+([^\n]+)', text)
        if address_match:
            data["address"] = address_match.group(1).strip()
        
        return data

    def _parse_passport_data(self, text):
        """Parse Passport-specific data"""
        data = {
            "passport_number": None,
            "name": None,
            "nationality": None,
            "date_of_birth": None,
            "date_of_issue": None,
            "date_of_expiry": None
        }
        
        # Find passport number
        passport_match = re.search(r'[A-Z]\d{7}', text)
        if passport_match:
            data["passport_number"] = passport_match.group()
        
        # Find name using the extract_name method
        data["name"] = self.extract_name(text)
        
        # Find nationality
        nationality_match = re.search(r'nationality[:\s]+([^\n]+)', text, re.IGNORECASE)
        if nationality_match:
            data["nationality"] = nationality_match.group(1).strip()
        
        # Find dates using patterns
        dob_match = re.search(r'birth[:\s]+([0-9]{1,2}\s+[a-z]{3,}\s+[0-9]{4}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{4})', text, re.IGNORECASE)
        if dob_match:
            data["date_of_birth"] = dob_match.group(1).strip()
            
        issue_match = re.search(r'issue[:\s]+([0-9]{1,2}\s+[a-z]{3,}\s+[0-9]{4}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{4})', text, re.IGNORECASE)
        if issue_match:
            data["date_of_issue"] = issue_match.group(1).strip()
            
        expiry_match = re.search(r'expiry[:\s]+([0-9]{1,2}\s+[a-z]{3,}\s+[0-9]{4}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{4})', text, re.IGNORECASE)
        if expiry_match:
            data["date_of_expiry"] = expiry_match.group(1).strip()
        
        return data

    def _parse_generic_data(self, text):
        """Parse generic document data"""
        return {
            "text": text,
            # Fixed: removed reference to undefined 'blocks' variable
            "extracted_text": text.strip() if text else ""
        }