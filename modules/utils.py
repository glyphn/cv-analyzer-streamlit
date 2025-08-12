# modules/utils.py
import os
import re
import logging
import yaml
import hashlib
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import cv2
import numpy as np

class Utils:
    @staticmethod
    def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
        """Set up logging configuration"""
        logger = logging.getLogger("cv_analyzer")
        logger.setLevel(logging.INFO)
        
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Create file handler if log_file specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    @staticmethod
    def load_config(config_path: str = 'config.yaml') -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        return config
    
    @staticmethod
    def create_temp_directory() -> str:
        """Create a temporary directory for processing files"""
        temp_dir = os.path.join(tempfile.gettempdir(), f"cv_analyzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    @staticmethod
    def generate_file_hash(file_path: str) -> str:
        """Generate a hash for a file to use as a cache key"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(65536)  # Read in 64k chunks
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Get lowercase file extension without dot"""
        _, ext = os.path.splitext(file_path)
        return ext.lower().lstrip('.')
    
    @staticmethod
    def is_supported_format(file_path: str, supported_formats: List[str]) -> bool:
        """Check if file has a supported format"""
        ext = Utils.get_file_extension(file_path)
        return ext in supported_formats
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage (works on Linux)"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss / (1024 * 1024),  # RSS in MB
                'vms': memory_info.vms / (1024 * 1024)   # VMS in MB
            }
        except ImportError:
            return {'error': 'psutil not available'}
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def cleanup_text(text: str) -> str:
        """Clean up text by removing extra whitespace, etc."""
        if not text:
            return ""
            
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove non-printable characters
        text = re.sub(r'[^\x20-\x7E\n\t\r]', '', text)
        
        # Remove excessive newlines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    def detect_image_orientation(image: np.ndarray) -> float:
        """
        Detect the orientation angle of text in an image
        Returns the angle in degrees
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find all contours
        contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        angles = []
        
        # Calculate orientation for each contour
        for contour in contours:
            if cv2.contourArea(contour) < 100:  # Skip small contours
                continue
                
            # Fit ellipse to contour
            try:
                (_, _), (_, _), angle = cv2.fitEllipse(contour)
                angles.append(angle)
            except:
                continue
        
        # If we found angles, return the median
        if angles:
            median_angle = np.median(angles)
            # Normalize angle to -45 to 45 degrees
            if median_angle > 45 and median_angle <= 90:
                median_angle = median_angle - 90
            elif median_angle > 90 and median_angle <= 135:
                median_angle = median_angle - 90
            elif median_angle > 135:
                median_angle = median_angle - 180
                
            return median_angle
        
        return 0.0  # Default: no rotation
    
    @staticmethod
    def translate_language_name(lang_code: str, ui_lang_code: str) -> str:
        """Translate language code to human-readable name in the UI language"""
        translations = {
            'eng': {
                'eng': 'English',
                'ind': 'Indonesian'
            },
            'ind': {
                'eng': 'Bahasa Inggris',
                'ind': 'Bahasa Indonesia'
            }
        }
        
        return translations.get(ui_lang_code, {}).get(lang_code, lang_code)
    
    @staticmethod
    def merge_dictionaries(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge two dictionaries
        If there are conflicts, values from dict2 take precedence
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Utils.merge_dictionaries(result[key], value)
            else:
                result[key] = value
                
        return result