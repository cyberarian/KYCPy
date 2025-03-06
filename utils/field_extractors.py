import re
from datetime import datetime

class FieldExtractor:
    @staticmethod
    def extract_date(text):
        """Extract date with multiple format support"""
        date_patterns = [
            r'(\d{2}-\d{2}-\d{4})',
            r'(\d{2}/\d{2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return datetime.strptime(match.group(1), "%d-%m-%Y").date()
                except ValueError:
                    continue
        return None

    @staticmethod
    def extract_address(text):
        """Extract address with multiple format support"""
        address_patterns = [
            r'Alamat[:\s]+([^\n]+)',
            r'Address[:\s]+([^\n]+)',
            r'(?<=\n)(?:Jl\.|Jalan)\s+[^\n]+'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    # Add more field extractors as needed...
