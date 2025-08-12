# modules/exporter.py
import json
import csv
import os
import logging
import pandas as pd
from typing import Dict, Any, List, Optional
import base64
from io import BytesIO
from datetime import datetime
import fitz  # PyMuPDF for PDF annotations
import cv2
import numpy as np

class Exporter:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def export_results(self, data: Dict[str, Any], format: str, output_path: Optional[str] = None) -> Any:
        """Export results in the specified format"""
        if format.lower() == 'json':
            return self.export_json(data, output_path)
        elif format.lower() == 'csv':
            return self.export_csv(data, output_path)
        elif format.lower() == 'xlsx':
            return self.export_excel(data, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def export_json(self, data: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export results as JSON"""
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            self.logger.info(f"Exported JSON to {output_path}")
            return {"success": True, "path": output_path}
        else:
            return data
    
    def export_csv(self, data: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export results as CSV"""
        # Flatten nested data structure
        flattened = self._flatten_data_for_export(data)
        
        if output_path:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=flattened.keys())
                writer.writeheader()
                writer.writerow(flattened)
            self.logger.info(f"Exported CSV to {output_path}")
            return {"success": True, "path": output_path}
        else:
            # For Streamlit, return CSV data as string
            output = BytesIO()
            df = pd.DataFrame([flattened])
            csv_data = df.to_csv(index=False)
            return {
                "success": True, 
                "data": csv_data,
                "filename": f"cv_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
    
    def export_excel(self, data: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export results as Excel file"""
        # Flatten nested data structure
        flattened = self._flatten_data_for_export(data)
        
        # Create Excel file with multiple sheets
        if output_path:
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                # Main sheet with overview
                pd.DataFrame([flattened]).to_excel(writer, sheet_name='Overview', index=False)
                
                # Separate sheets for more detailed information
                if 'extracted_info' in data:
                    # Skills sheet
                    if 'skills' in data['extracted_info'] and data['extracted_info']['skills']:
                        skills_df = pd.DataFrame({'Skill': data['extracted_info']['skills']})
                        skills_df.to_excel(writer, sheet_name='Skills', index=False)
                    
                    # Education sheet
                    if 'education' in data['extracted_info'] and data['extracted_info']['education']:
                        edu_df = pd.DataFrame(data['extracted_info']['education'])
                        edu_df.to_excel(writer, sheet_name='Education', index=False)
                    
                    # Work Experience sheet
                    if 'work_experience' in data['extracted_info'] and data['extracted_info']['work_experience']:
                        exp_df = pd.DataFrame(data['extracted_info']['work_experience'])
                        exp_df.to_excel(writer, sheet_name='Work_Experience', index=False)
            
            self.logger.info(f"Exported Excel to {output_path}")
            return {"success": True, "path": output_path}
        else:
            # For Streamlit, return Excel data as bytes
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Main sheet with overview
                pd.DataFrame([flattened]).to_excel(writer, sheet_name='Overview', index=False)
                
                # Separate sheets for more detailed information
                if 'extracted_info' in data:
                    # Skills sheet
                    if 'skills' in data['extracted_info'] and data['extracted_info']['skills']:
                        skills_df = pd.DataFrame({'Skill': data['extracted_info']['skills']})
                        skills_df.to_excel(writer, sheet_name='Skills', index=False)
                    
# modules/exporter.py (continued)
                    # Education sheet
                    if 'education' in data['extracted_info'] and data['extracted_info']['education']:
                        edu_df = pd.DataFrame(data['extracted_info']['education'])
                        edu_df.to_excel(writer, sheet_name='Education', index=False)
                    
                    # Work Experience sheet
                    if 'work_experience' in data['extracted_info'] and data['extracted_info']['work_experience']:
                        exp_df = pd.DataFrame(data['extracted_info']['work_experience'])
                        exp_df.to_excel(writer, sheet_name='Work_Experience', index=False)
            
            excel_data = output.getvalue()
            return {
                "success": True, 
                "data": excel_data,
                "filename": f"cv_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            }
    
    def _flatten_data_for_export(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested data structure for export to tabular formats"""
        flattened = {}
        
        # File metadata
        if 'filename' in data:
            flattened['Filename'] = data['filename']
        
        if 'language' in data:
            flattened['Language'] = 'English' if data['language'] == 'eng' else 'Bahasa Indonesia'
            flattened['Language Confidence'] = data.get('language_confidence', '')
        
        # Extract personal information
        if 'extracted_info' in data and 'personal_info' in data['extracted_info']:
            personal_info = data['extracted_info']['personal_info']
            flattened['Name'] = personal_info.get('name', '')
            flattened['Email'] = personal_info.get('email', '')
            flattened['Phone'] = personal_info.get('phone', '')
            flattened['Address'] = personal_info.get('address', '')
        
        # Skills as comma-separated list
        if 'extracted_info' in data and 'skills' in data['extracted_info']:
            flattened['Skills'] = ', '.join(data['extracted_info'].get('skills', []))
        
        # Languages as comma-separated list
        if 'extracted_info' in data and 'languages' in data['extracted_info']:
            flattened['Languages'] = ', '.join(data['extracted_info'].get('languages', []))
        
        # Certifications as comma-separated list
        if 'extracted_info' in data and 'certifications' in data['extracted_info']:
            flattened['Certifications'] = ', '.join(data['extracted_info'].get('certifications', []))
        
        # Summary
        if 'extracted_info' in data and 'summary' in data['extracted_info']:
            flattened['Summary'] = data['extracted_info'].get('summary', '')
        
        # Education - first institution only
        if 'extracted_info' in data and 'education' in data['extracted_info'] and data['extracted_info']['education']:
            first_edu = data['extracted_info']['education'][0]
            flattened['Education Institution'] = first_edu.get('institution', '')
            flattened['Education Degree'] = first_edu.get('degree', '')
            flattened['Education Dates'] = ', '.join(first_edu.get('dates', []))
        
        # Work Experience - first experience only
        if 'extracted_info' in data and 'work_experience' in data['extracted_info'] and data['extracted_info']['work_experience']:
            first_exp = data['extracted_info']['work_experience'][0]
            flattened['Experience Company'] = first_exp.get('company', '')
            flattened['Experience Title'] = first_exp.get('title', '')
            flattened['Experience Dates'] = ', '.join(first_exp.get('dates', []))
        
        # Confidence scores
        if 'extracted_info' in data and 'confidence_scores' in data['extracted_info']:
            confidence = data['extracted_info']['confidence_scores']
            flattened['Overall Confidence'] = confidence.get('overall', '')
            flattened['Personal Info Confidence'] = confidence.get('personal_info', '')
            flattened['Skills Confidence'] = confidence.get('skills', '')
        
        return flattened
    
    def export_annotated_pdf(self, original_pdf_path: str, data: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        """
        Create an annotated PDF with bounding boxes for extracted entities
        """
        try:
            # Open the PDF
            pdf_document = fitz.open(original_pdf_path)
            
            # Entities to highlight with different colors
            entities_to_highlight = {
                'name': (1, 0, 0),       # Red
                'email': (0, 0, 1),      # Blue
                'phone': (0, 0.5, 0),    # Green
                'skills': (0.5, 0, 0.5), # Purple
                'dates': (1, 0.5, 0),    # Orange
                'education': (0, 0.5, 0.5), # Teal
                'work': (0.5, 0.5, 0)    # Olive
            }
            
            # Get entity positions from data
            # This would come from OCR results that include bounding boxes
            # For this implementation, we'll use a simplified approach
            
            # For each page in the PDF
            for page_idx in range(len(pdf_document)):
                page = pdf_document[page_idx]
                
                # Example: Search for entities and add annotations
                # This is a simplified version - in a real implementation,
                # you would use the actual bounding boxes from OCR
                
                # Personal info
                if 'extracted_info' in data and 'personal_info' in data['extracted_info']:
                    personal_info = data['extracted_info']['personal_info']
                    
                    # Find and highlight name
                    if personal_info.get('name'):
                        instances = page.search_for(personal_info['name'])
                        for inst in instances:
                            highlight = page.add_rect_annot(inst)
                            highlight.set_colors(stroke=entities_to_highlight['name'])
                            highlight.update()
                    
                    # Find and highlight email
                    if personal_info.get('email'):
                        instances = page.search_for(personal_info['email'])
                        for inst in instances:
                            highlight = page.add_rect_annot(inst)
                            highlight.set_colors(stroke=entities_to_highlight['email'])
                            highlight.update()
                    
                    # Find and highlight phone
                    if personal_info.get('phone'):
                        instances = page.search_for(personal_info['phone'])
                        for inst in instances:
                            highlight = page.add_rect_annot(inst)
                            highlight.set_colors(stroke=entities_to_highlight['phone'])
                            highlight.update()
                
                # Highlight skills
                if 'extracted_info' in data and 'skills' in data['extracted_info']:
                    for skill in data['extracted_info']['skills']:
                        instances = page.search_for(skill)
                        for inst in instances:
                            highlight = page.add_rect_annot(inst)
                            highlight.set_colors(stroke=entities_to_highlight['skills'])
                            highlight.update()
            
            # Add a legend to the first page
            first_page = pdf_document[0]
            
            # Calculate position for legend (bottom left)
            page_rect = first_page.rect
            legend_x = 50
            legend_y = page_rect.height - 100
            
            # Add legend title
            first_page.insert_text((legend_x, legend_y), 
                                  "Entity Annotations Legend",
                                  fontsize=12, fontname="Helvetica-Bold")
            
            # Add legend items
            y_offset = 15
            for entity, color in entities_to_highlight.items():
                y_pos = legend_y + y_offset
                # Draw color box
                rect = fitz.Rect(legend_x, y_pos, legend_x + 10, y_pos + 10)
                first_page.draw_rect(rect, color=color, fill=color)
                # Add label
                first_page.insert_text((legend_x + 15, y_pos + 7), 
                                      entity.capitalize(),
                                      fontsize=9, fontname="Helvetica")
                y_offset += 15
            
            # Save the annotated PDF
            pdf_document.save(output_path)
            pdf_document.close()
            
            self.logger.info(f"Exported annotated PDF to {output_path}")
            return {"success": True, "path": output_path}
            
        except Exception as e:
            self.logger.error(f"Error creating annotated PDF: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def export_bulk_results(self, results: List[Dict[str, Any]], format: str, output_path: str) -> Dict[str, Any]:
        """Export results from bulk processing"""
        if format.lower() == 'json':
            return self.export_bulk_json(results, output_path)
        elif format.lower() == 'csv':
            return self.export_bulk_csv(results, output_path)
        elif format.lower() == 'xlsx':
            return self.export_bulk_excel(results, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def export_bulk_json(self, results: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
        """Export bulk results as JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        self.logger.info(f"Exported bulk results as JSON to {output_path}")
        return {"success": True, "path": output_path}
    
    def export_bulk_csv(self, results: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
        """Export bulk results as CSV"""
        # Flatten each result
        flattened_results = [self._flatten_data_for_export(result) for result in results]
        
        # Create DataFrame and export
        df = pd.DataFrame(flattened_results)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        self.logger.info(f"Exported bulk results as CSV to {output_path}")
        return {"success": True, "path": output_path}
    
    def export_bulk_excel(self, results: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
        """Export bulk results as Excel with multiple sheets"""
        # Flatten each result for main summary sheet
        flattened_results = [self._flatten_data_for_export(result) for result in results]
        
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Main summary sheet
            pd.DataFrame(flattened_results).to_excel(writer, sheet_name='Summary', index=False)
            
            # Extract all skills across all resumes
            all_skills = set()
            for result in results:
                if 'extracted_info' in result and 'skills' in result['extracted_info']:
                    all_skills.update(result['extracted_info']['skills'])
            
            # Create skills frequency sheet
            skill_counts = {}
            for skill in all_skills:
                count = sum(1 for result in results if 
                           'extracted_info' in result and 
                           'skills' in result['extracted_info'] and 
                           skill in result['extracted_info']['skills'])
                skill_counts[skill] = count
            
            skills_df = pd.DataFrame([{'Skill': k, 'Count': v} for k, v in skill_counts.items()])
            skills_df.sort_values('Count', ascending=False, inplace=True)
            skills_df.to_excel(writer, sheet_name='Skills_Frequency', index=False)
            
            # Create education sheet
            edu_data = []
            for result in results:
                if 'extracted_info' in result and 'education' in result['extracted_info']:
                    filename = result.get('filename', 'Unknown')
                    for edu in result['extracted_info']['education']:
                        edu_row = {
                            'Filename': filename,
                            'Name': result['extracted_info']['personal_info'].get('name', ''),
                            'Institution': edu.get('institution', ''),
                            'Degree': edu.get('degree', ''),
                            'Field': edu.get('field', ''),
                            'Dates': ', '.join(edu.get('dates', []))
                        }
                        edu_data.append(edu_row)
            
            if edu_data:
                pd.DataFrame(edu_data).to_excel(writer, sheet_name='Education', index=False)
            
            # Create work experience sheet
            exp_data = []
            for result in results:
                if 'extracted_info' in result and 'work_experience' in result['extracted_info']:
                    filename = result.get('filename', 'Unknown')
                    for exp in result['extracted_info']['work_experience']:
                        exp_row = {
                            'Filename': filename,
                            'Name': result['extracted_info']['personal_info'].get('name', ''),
                            'Company': exp.get('company', ''),
                            'Title': exp.get('title', ''),
                            'Dates': ', '.join(exp.get('dates', []))
                        }
                        exp_data.append(exp_row)
            
            if exp_data:
                pd.DataFrame(exp_data).to_excel(writer, sheet_name='Work_Experience', index=False)
        
        self.logger.info(f"Exported bulk results as Excel to {output_path}")
        return {"success": True, "path": output_path}