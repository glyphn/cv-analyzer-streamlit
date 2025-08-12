# modules/date_normalizer.py
import re
import datetime
from typing import Optional, Dict, List, Any
import logging

class DateNormalizer:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Date formats for different languages
        self.date_formats = {
            'eng': [
                # Month name formats
                r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[,.\s]+(\d{1,2})[,.\s]+(\d{4})',
                r'(\d{1,2})[,.\s]+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[,.\s]+(\d{4})',
                # Numeric formats
                r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',  # DD/MM/YYYY or MM/DD/YYYY
                r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})',  # YYYY/MM/DD
                # Year only
                r'\b(20\d{2})\b',  # Just year (20xx)
                r'\b(19\d{2})\b',  # Just year (19xx)
                # Special terms
                r'(?:Present|Current|Now)',  # Present/Current indicators
            ],
            'ind': [
                # Indonesian month names
                r'(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)[,.\s]+(\d{1,2})[,.\s]+(\d{4})',
                r'(\d{1,2})[,.\s]+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)[,.\s]+(\d{4})',
                # Numeric formats (same as English)
                r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
                r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})',
                # Year only
                r'\b(20\d{2})\b',
                r'\b(19\d{2})\b',
                # Special terms in Indonesian
                r'(?:Sekarang|Saat ini)',  # Present/Current indicators
            ]
        }
        
        # Month name mappings
        self.month_names = {
            'eng': {
                'jan': 1, 'january': 1,
                'feb': 2, 'february': 2,
                'mar': 3, 'march': 3,
                'apr': 4, 'april': 4,
                'may': 5,
                'jun': 6, 'june': 6,
                'jul': 7, 'july': 7,
                'aug': 8, 'august': 8,
                'sep': 9, 'september': 9,
                'oct': 10, 'october': 10,
                'nov': 11, 'november': 11,
                'dec': 12, 'december': 12
            },
            'ind': {
                'januari': 1,
                'februari': 2,
                'maret': 3,
                'april': 4,
                'mei': 5,
                'juni': 6,
                'juli': 7,
                'agustus': 8,
                'september': 9,
                'oktober': 10,
                'november': 11,
                'desember': 12
            }
        }
        
        # Present indicators
        self.present_indicators = {
            'eng': ['present', 'current', 'now', 'ongoing'],
            'ind': ['sekarang', 'saat ini', 'hingga kini', 'sampai sekarang']
        }
    
    def extract_dates(self, text: str, lang_code: str) -> List[Dict[str, Any]]:
        """Extract all dates from text and normalize them"""
        if not text:
            return []
            
        # Get appropriate date formats for the language
        formats = self.date_formats.get(lang_code, self.date_formats['eng'])
        
        dates = []
        for pattern in formats:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_text = match.group(0)
                try:
                    normalized = self.normalize_date(date_text, lang_code)
                    if normalized:
                        dates.append({
                            'original': date_text,
                            'normalized': normalized,
                            'is_present': self.is_present_indicator(date_text, lang_code),
                            'position': match.span()
                        })
                except Exception as e:
                    self.logger.warning(f"Error normalizing date '{date_text}': {str(e)}")
        
        return dates
    
    def normalize_date(self, date_text: str, lang_code: str) -> Optional[str]:
        """Convert a date string to ISO format (YYYY-MM-DD)"""
        if self.is_present_indicator(date_text, lang_code):
            return datetime.datetime.now().strftime('%Y-%m-%d')
            
        # Check for year only
        year_match = re.search(r'\b(19|20)\d{2}\b', date_text)
        if year_match and len(date_text.strip()) <= 5:  # Just the year with possible whitespace
            return f"{year_match.group(0)}-01-01"  # Default to January 1st
        
        # Try to parse month names
        month_names = self.month_names.get(lang_code, self.month_names['eng'])
        for month_name, month_num in month_names.items():
            if month_name in date_text.lower():
                # Extract day and year
                day_match = re.search(r'\b(\d{1,2})\b', date_text)
                year_match = re.search(r'\b(19|20)\d{2}\b', date_text)
                
                if year_match:
                    year = year_match.group(0)
                    day = day_match.group(0) if day_match else '1'
                    # Ensure day is valid
                    day = min(int(day), 28)  # Simple validation (avoid invalid days)
                    return f"{year}-{month_num:02d}-{day:02d}"
        
        # Try numeric formats
        # DD/MM/YYYY or MM/DD/YYYY (ambiguous, we'll assume MM/DD/YYYY for English, DD/MM/YYYY for others)
        slash_match = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', date_text)
        if slash_match:
            if lang_code == 'eng':  # Assume MM/DD/YYYY for English
                month, day, year = slash_match.groups()
            else:  # Assume DD/MM/YYYY for others
                day, month, year = slash_match.groups()
            
            # Basic validation
            month = min(int(month), 12)
            day = min(int(day), 28)  # Simple validation
            
            return f"{year}-{month:02d}-{day:02d}"
        
        # YYYY/MM/DD format
        iso_match = re.search(r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', date_text)
        if iso_match:
            year, month, day = iso_match.groups()
            # Basic validation
            month = min(int(month), 12)
            day = min(int(day), 28)  # Simple validation
            
            return f"{year}-{month:02d}-{day:02d}"
        
        return None
    
    def is_present_indicator(self, text: str, lang_code: str) -> bool:
        """Check if the text indicates current/present time"""
        indicators = self.present_indicators.get(lang_code, self.present_indicators['eng'])
        return any(indicator in text.lower() for indicator in indicators)
    
    def extract_date_range(self, text: str, lang_code: str) -> Dict[str, Any]:
        """
        Extract start and end dates from text (e.g., "January 2019 - Present")
        Returns a dictionary with start_date and end_date in ISO format
        """
        dates = self.extract_dates(text, lang_code)
        
        if not dates:
            return {'start_date': None, 'end_date': None}
        
        # If only one date found, use it as the start date
        if len(dates) == 1:
            is_present = dates[0]['is_present']
            if is_present:
                return {'start_date': None, 'end_date': dates[0]['normalized']}
            else:
                return {'start_date': dates[0]['normalized'], 'end_date': None}
        
        # Sort dates by position in text
        dates.sort(key=lambda x: x['position'][0])
        
        # Try to find a range pattern (e.g., "2019 - 2020" or "Jan 2019 - Present")
        for i in range(len(dates) - 1):
            # Check if there's a dash or 'to' between consecutive dates
            between_text = text[dates[i]['position'][1]:dates[i+1]['position'][0]]
            if '-' in between_text or 'to' in between_text.lower() or 'hingga' in between_text.lower():
                return {
                    'start_date': dates[i]['normalized'],
                    'end_date': dates[i+1]['normalized']
                }
        
        # If no clear range found, use the first and last dates
        return {
            'start_date': dates[0]['normalized'],
            'end_date': dates[-1]['normalized']
        }