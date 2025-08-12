# cli.py
import argparse
import os
import yaml
import logging
import json
import csv
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

# Import our modules
from modules.ocr_processor import OCRProcessor
from modules.language_detector import LanguageDetector
from modules.nlp_processor import NLPProcessor
from modules.entity_extractor import EntityExtractor

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("cv_analyzer.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def process_single_file(file_path, config, language_override=None):
    """Process a single file and return extracted information"""
    try:
        # Initialize processors
        ocr = OCRProcessor(config)
        lang_detector = LanguageDetector(config)
        nlp = NLPProcessor(config)
        entity_extractor = EntityExtractor(config)
        
        # OCR Processing
        ocr_result = ocr.process_file(file_path)
        
        # Language Detection or override
        if language_override and language_override != "auto":
            detected_lang = language_override
            lang_confidence = 1.0
        else:
            lang_result = lang_detector.detect_language(ocr_result['text'])
            detected_lang = lang_result['lang_code']
            lang_confidence = lang_result['confidence']
        
        # NLP Processing
        doc = nlp.process_text(ocr_result['text'], detected_lang)
        
        # Entity Extraction
        extracted_info = entity_extractor.extract_entities(doc, detected_lang)
        
        # Result
        result = {
            'filename': os.path.basename(file_path),
            'language': detected_lang,
            'language_confidence': lang_confidence,
            'extracted_info': extracted_info,
            'ocr_confidence': ocr_result.get('ocr_confidence', 0)
        }
        
        return result
    
    except Exception as e:
        logging.error(f"Error processing {file_path}: {str(e)}")
        return {
            'filename': os.path.basename(file_path),
            'error': str(e)
        }

def export_results(results, output_path, format="json", annotate_pdfs=False):
    """Export results to the specified format"""
    if format.lower() == "json":
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    elif format.lower() == "csv":
        # Flatten the data structure for CSV
        flattened_data = []
        for result in results:
            if 'error' in result:
                continue
                
            personal_info = result['extracted_info']['personal_info']
            row = {
                'Filename': result['filename'],
                'Language': 'English' if result['language'] == 'eng' else 'Bahasa Indonesia',
                'Name': personal_info.get('name', ''),
                'Email': personal_info.get('email', ''),
                'Phone': personal_info.get('phone', ''),
                'Address': personal_info.get('address', ''),
                'Skills': ', '.join(result['extracted_info'].get('skills', [])),
                'Languages': ', '.join(result['extracted_info'].get('languages', [])),
                'Summary': result['extracted_info'].get('summary', ''),
                'Overall Confidence': result['extracted_info']['confidence_scores']['overall']
            }
            flattened_data.append(row)
            
        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if flattened_data:
                writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                writer.writeheader()
                writer.writerows(flattened_data)
    
    elif format.lower() == "xlsx":
        # Create DataFrame from flattened data
        flattened_data = []
        for result in results:
            if 'error' in result:
                continue
                
            personal_info = result['extracted_info']['personal_info']
            row = {
                'Filename': result['filename'],
                'Language': 'English' if result['language'] == 'eng' else 'Bahasa Indonesia',
                'Name': personal_info.get('name', ''),
                'Email': personal_info.get('email', ''),
                'Phone': personal_info.get('phone', ''),
                'Address': personal_info.get('address', ''),
                'Skills': ', '.join(result['extracted_info'].get('skills', [])),
                'Languages': ', '.join(result['extracted_info'].get('languages', [])),
                'Summary': result['extracted_info'].get('summary', ''),
                'Overall Confidence': result['extracted_info']['confidence_scores']['overall']
            }
            flattened_data.append(row)
            
        df = pd.DataFrame(flattened_data)
        
        # Write to Excel with multiple sheets
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Add detailed sheets for education and work experience
            edu_data = []
            exp_data = []
            
            for result in results:
                if 'error' in result:
                    continue
                    
                filename = result['filename']
                
                # Education data
                for edu in result['extracted_info'].get('education', []):
                    edu_row = {
                        'Filename': filename,
                        'Institution': edu.get('institution', ''),
                        'Degree': edu.get('degree', ''),
                        'Field': edu.get('field', ''),
                        'Dates': ', '.join(edu.get('dates', []))
                    }
                    edu_data.append(edu_row)
                
                # Work experience data
                for exp in result['extracted_info'].get('work_experience', []):
                    exp_row = {
                        'Filename': filename,
                        'Company': exp.get('company', ''),
                        'Title': exp.get('title', ''),
                        'Dates': ', '.join(exp.get('dates', []))
                    }
                    exp_data.append(exp_row)
            
            # Write additional sheets
            if edu_data:
                pd.DataFrame(edu_data).to_excel(writer, sheet_name='Education', index=False)
            if exp_data:
                pd.DataFrame(exp_data).to_excel(writer, sheet_name='Work Experience', index=False)
    
    else:
        raise ValueError(f"Unsupported export format: {format}")
    
    logging.info(f"Results exported to {output_path}")
    
    # TODO: Implement annotated PDF export if requested
    if annotate_pdfs:
        logging.info("PDF annotation functionality will be implemented here")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Bilingual CV Document Analyzer CLI')
    parser.add_argument('--mode', choices=['single', 'bulk'], default='single', help='Processing mode')
    parser.add_argument('--input', required=True, help='Input file or directory')
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--model', choices=['en_core_web_trf', 'en_core_web_sm', 'id_core_news_sm'], 
                      help='spaCy model to use')
    parser.add_argument('--ocr', default='tesseract', help='OCR engine to use')
    parser.add_argument('--language', choices=['eng', 'ind', 'auto'], default='auto', 
                      help='Force language or auto-detect')
    parser.add_argument('--annotate-pdfs', action='store_true', help='Create annotated PDFs with bounding boxes')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--format', choices=['json', 'csv', 'xlsx'], default='json', 
                      help='Output format')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging()
    logger.info("Starting CV Document Analyzer CLI")
    
    # Load configuration
    with open(args.config, 'r') as file:
        config = yaml.safe_load(file)
    
    # Override config with command line arguments
    if args.model:
        if 'en_core' in args.model:
            config['nlp']['english']['primary_model'] = args.model
        elif 'id_core' in args.model:
            config['nlp']['indonesian']['primary_model'] = args.model
    
    if args.ocr:
        config['ocr']['engine'] = args.ocr
        
    if args.workers:
        config['app']['parallel_workers'] = args.workers
    
    # Process based on mode
    if args.mode == 'single':
        if not os.path.isfile(args.input):
            logger.error(f"Input file not found: {args.input}")
            return
            
        logger.info(f"Processing single file: {args.input}")
        result = process_single_file(args.input, config, args.language)
        export_results([result], args.output, args.format, args.annotate_pdfs)
        
    elif args.mode == 'bulk':
        if not os.path.isdir(args.input):
            logger.error(f"Input directory not found: {args.input}")
            return
            
        # Get all files in directory
        file_paths = []
        supported_formats = config['app']['supported_formats']
        
        for root, _, files in os.walk(args.input):
            for file in files:
                _, ext = os.path.splitext(file)
                ext = ext.lower().lstrip('.')
                if ext in supported_formats:
                    file_paths.append(os.path.join(root, file))
        
        if not file_paths:
            logger.error(f"No supported files found in {args.input}")
            return
            
        logger.info(f"Found {len(file_paths)} files to process")
        
        # Process files in parallel
        results = []
        num_workers = config['app']['parallel_workers']
        
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(process_single_file, path, config, args.language): path 
                      for path in file_paths}
            
            # Show progress bar
            for future in tqdm(futures, total=len(file_paths), desc="Processing files"):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    path = futures[future]
                    logger.error(f"Error processing {path}: {str(e)}")
        
        # Export results
        export_results(results, args.output, args.format, args.annotate_pdfs)
        
    logger.info("Processing complete")

if __name__ == "__main__":
    main()