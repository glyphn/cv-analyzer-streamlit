# modules/ocr_processor.py
import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
import pdf2image
import docx2txt
import zipfile
from concurrent.futures import ProcessPoolExecutor
import logging

custom_config = r'--oem 3 --psm 1'
class OCRProcessor:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.supported_formats = self.config['app']['supported_formats']
        self.psm_mode = config.get('ocr', {}).get('psm_mode', 3)
        
        # Configure Tesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
        
    def preprocess_image(self, image):
        """Apply preprocessing steps to improve OCR quality"""
        # Convert to grayscale if it's a color image
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Deskewing (straighten tilted text)
        if self.config['ocr']['preprocessing']['deskew']:
            coords = np.column_stack(np.where(gray > 0))
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            (h, w) = gray.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        # Denoising
        if self.config['ocr']['preprocessing']['denoise']:
            gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Adaptive thresholding for better contrast
        if self.config['ocr']['preprocessing']['adaptive_threshold']:
            gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Binarization for clearer text boundaries
        if self.config['ocr']['preprocessing']['binarization']:
            _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # TODO: Multi-column detection and table segmentation logic would go here
        # These are more complex and would require additional CV operations
        
        return gray
        
    def extract_text_from_image(self, image, langs="eng+ind"):
        """Extract text from an image using Tesseract OCR"""
        # Preprocess the image
        processed_img = self.preprocess_image(image)
        
        # Extract text using tesseract with specified languages
        # Use a default PSM mode of 6 (assume a single uniform block of text) if not specified
        try:
            psm_mode = int(self.config['ocr']['psm_mode'])
            if not (0 <= psm_mode <= 13):
                self.logger.warning(f"Invalid PSM mode {psm_mode}, using default mode 6")
                psm_mode = 6
        except (KeyError, ValueError, TypeError):
            self.logger.warning("PSM mode not properly configured, using default mode 6")
            psm_mode = 6
        
        custom_config = f'--psm {psm_mode} -l {langs}'
        
        text = pytesseract.image_to_string(processed_img, config=custom_config)
        
        # Get bounding boxes for entities (will be used for annotation)
        boxes = pytesseract.image_to_data(processed_img, config=custom_config, output_type=pytesseract.Output.DICT)
        
        # Calculate average confidence, handling empty results
        confidence_values = [int(conf) for conf in boxes['conf'] if conf != '-1']
        avg_confidence = np.mean(confidence_values) if confidence_values else 0
        
        return {
            'text': text,
            'boxes': boxes,
            'ocr_confidence': avg_confidence,
            'processed_image': processed_img
        }
    
    def process_pdf(self, file_path):
        """Process a PDF file and extract text using OCR"""
        # Convert PDF to images
        dpi = self.config['ocr']['dpi']
        images = pdf2image.convert_from_path(file_path, dpi=dpi)
        
        results = []
        for i, img in enumerate(images):
            # Convert PIL Image to OpenCV format
            open_cv_image = np.array(img) 
            open_cv_image = open_cv_image[:, :, ::-1].copy()  # Convert RGB to BGR
            
            # Process the image
            page_result = self.extract_text_from_image(open_cv_image)
            page_result['page_num'] = i + 1
            results.append(page_result)
            
        # Combine results from all pages
        full_text = "\n\n".join([page['text'] for page in results])
        avg_confidence = np.mean([page['ocr_confidence'] for page in results])
        
        return {
            'text': full_text,
            'pages': results,
            'ocr_confidence': avg_confidence,
            'num_pages': len(images)
        }
    
    def process_docx(self, file_path):
        """Extract text from a DOCX file"""
        # For DOCX we can extract text directly without OCR
        text = docx2txt.process(file_path)
        return {
            'text': text,
            'ocr_confidence': 100.0,  # Direct extraction, not OCR
            'num_pages': None  # Can't easily determine pages in DOCX
        }
    
    def process_image(self, file_path):
        """Process image files (PNG, JPG)"""
        img = cv2.imread(file_path)
        result = self.extract_text_from_image(img)
        result['num_pages'] = 1
        return result
    
    def process_file(self, file_path):
        """Process a single file based on its extension"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')
        
        if ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {ext}")
        
        if ext == 'pdf':
            return self.process_pdf(file_path)
        elif ext == 'docx':
            return self.process_docx(file_path)
        elif ext in ['png', 'jpg', 'jpeg']:
            return self.process_image(file_path)
        elif ext == 'zip':
            return self.process_zip(file_path)
    
    def process_zip(self, zip_path):
        """Extract and process all files from a ZIP archive"""
        temp_dir = "temp_extraction"
        os.makedirs(temp_dir, exist_ok=True)
        
        file_results = []
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
            # Process each file in the archive
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    _, ext = os.path.splitext(file)
                    ext = ext.lower().lstrip('.')
                    
                    if ext in self.supported_formats and ext != 'zip':  # Avoid nested ZIPs
                        try:
                            result = self.process_file(file_path)
                            result['filename'] = file
                            file_results.append(result)
                        except Exception as e:
                            self.logger.error(f"Error processing {file}: {str(e)}")
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(temp_dir)
        
        return file_results
    
    def process_bulk(self, file_paths):
        """Process multiple files in parallel"""
        num_workers = self.config['app']['parallel_workers']
        
        results = {}
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            future_to_path = {executor.submit(self.process_file, path): path for path in file_paths}
            for future in future_to_path:
                path = future_to_path[future]
                try:
                    results[path] = future.result()
                except Exception as e:
                    self.logger.error(f"Error processing {path}: {str(e)}")
                    results[path] = {'error': str(e)}
        
        return results