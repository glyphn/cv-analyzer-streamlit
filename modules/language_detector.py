# modules/language_detector.py
import langdetect
from langdetect import DetectorFactory
import logging

# Set seed for deterministic language detection
DetectorFactory.seed = 0

class LanguageDetector:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.supported_languages = self.config['app']['supported_languages']
        
    def detect_language(self, text):
        """
        Detect if text is in English or Bahasa Indonesia
        Returns language code and confidence
        """
        if not text or len(text.strip()) < 10:
            # Default to English if text is too short to detect reliably
            return {"lang_code": "eng", "confidence": 0.5}
        
        try:
            # Get language probabilities
            lang_probs = langdetect.detect_langs(text)
            
            # Find highest probability language
            top_lang = lang_probs[0]
            lang_code = top_lang.lang
            confidence = top_lang.prob
            
            # Map ISO 639-1 codes to our supported language codes
            lang_mapping = {
                'en': 'eng',  # English
            }
            
            detected_lang = lang_mapping.get(lang_code, 'eng')  # Default to English if mapping not found
            
            # Verify it's in our supported languages
            if detected_lang not in self.supported_languages:
                detected_lang = 'eng'  # Default to English
                confidence = 0.5
                
            return {
                "lang_code": detected_lang,
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error(f"Language detection error: {str(e)}")
            # Default to English on error
            return {"lang_code": "eng", "confidence": 0.5}
    
    def get_primary_language(self, text):
        """Return just the language code for the detected language"""
        result = self.detect_language(text)
        return result["lang_code"]