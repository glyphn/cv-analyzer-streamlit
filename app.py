# app.py
import streamlit as st
import os
import yaml
import tempfile
from pathlib import Path
import pandas as pd
import time
import json
import base64
import uuid
from io import BytesIO

# Import our modules
from modules.ocr_processor import OCRProcessor
from modules.language_detector import LanguageDetector
from modules.nlp_processor import NLPProcessor
from modules.entity_extractor import EntityExtractor

# Load configuration
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Initialize processors
@st.cache_resource
def load_processors():
    ocr = OCRProcessor(config)
    lang_detector = LanguageDetector(config)
    nlp = NLPProcessor(config)
    entity_extractor = EntityExtractor(config)
    return ocr, lang_detector, nlp, entity_extractor

ocr, lang_detector, nlp, entity_extractor = load_processors()

# Streamlit UI
st.set_page_config(
    page_title=config['app']['name'],
    page_icon="📄",
    layout="wide"
)

# Language selection
# Replace with:
ui_lang_code = "eng"
# Localized UI text
ui_text = {
    "eng": {
        "title": "Bilingual CV Document Analyzer",
        "upload_title": "Upload Document",
        "upload_description": "Upload CV/resume files (PDF, DOCX, PNG, JPG) or a ZIP archive containing multiple files",
        "processing_button": "Process Documents",
        "bulk_processing": "Bulk Processing",
        "single_document": "Single Document",
        "detected_language": "Detected Language",
        "confidence": "Confidence",
        "extracted_text": "Extracted Text",
        "extracted_info": "Extracted Information",
        "personal_info": "Personal Information",
        "name": "Name",
        "email": "Email",
        "phone": "Phone",
        "address": "Address",
        "skills": "Skills",
        "education": "Education",
        "work_experience": "Work Experience",
        "languages": "Languages",
        "certifications": "Certifications",
        "summary": "Professional Summary",
# app.py (continued)
        "export_results": "Export Results",
        "export_format": "Export Format",
        "download": "Download",
        "processing": "Processing...",
        "no_files": "No files uploaded",
        "progress": "Progress",
        "results_summary": "Results Summary",
        "filter_by_skills": "Filter by Skills",
        "filter_by_experience": "Filter by Years of Experience",
        "filter_by_language": "Filter by Document Language",
        "search": "Search",
        "edit_extracted": "Edit Extracted Information",
        "save_changes": "Save Changes",
        "cancel": "Cancel"
    },
    
    
}

# Get localized text
def t(key):
    return ui_text[ui_lang_code][key]

# Main app
st.title(t("title"))

# Tabs for single document vs bulk processing
tab1, tab2 = st.tabs([t("single_document"), t("bulk_processing")])

# Single Document Processing
with tab1:
    st.header(t("upload_title"))
    st.write(t("upload_description"))
    
    uploaded_file = st.file_uploader(
    "Upload your CV/resume", 
    type=config['app']['supported_formats'],
    accept_multiple_files=False,
    label_visibility="collapsed"  # Options: "visible", "hidden", or "collapsed"
)
    
    if uploaded_file is not None:
        # Create a temp file
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if st.button(t("processing_button")):
            with st.spinner(t("processing")):
                # Process the file
                try:
                    # OCR Processing
                    ocr_result = ocr.process_file(temp_path)
                    
                    # Language Detection
                    lang_result = lang_detector.detect_language(ocr_result['text'])
                    detected_lang = lang_result['lang_code']
                    lang_confidence = lang_result['confidence']
                    
                    # NLP Processing
                    doc = nlp.process_text(ocr_result['text'], detected_lang)
                    
                    # Entity Extraction
                    extracted_info = entity_extractor.extract_entities(doc, detected_lang)
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader(t("extracted_text"))
                        st.text_area(
                            "Extracted Text", 
                            value=ocr_result['text'], 
                            height=400,
                            label_visibility="collapsed"  # Options: "visible", "hidden", or "collapsed"
                        )
                        
                        st.subheader(t("detected_language"))
                        if detected_lang == "eng":
                            st.write("English")
                        else:
                            st.write("Bahasa Indonesia")
                            
                        st.write(f"{t('confidence')}: {lang_confidence:.2f}")
                        
                    with col2:
                        st.subheader(t("extracted_info"))
                        
                        # Personal Info
                        st.markdown(f"**{t('personal_info')}**")
                        personal_info = extracted_info['personal_info']
                        st.write(f"{t('name')}: {personal_info['name']}")
                        st.write(f"{t('email')}: {personal_info['email']}")
                        st.write(f"{t('phone')}: {personal_info['phone']}")
                        st.write(f"{t('address')}: {personal_info['address']}")
                        
                        # Skills
                        st.markdown(f"**{t('skills')}**")
                        if extracted_info['skills']:
                            for skill in extracted_info['skills']:
                                st.write(f"- {skill}")
                        else:
                            st.write("None detected")
                            
                        # Education
                        st.markdown(f"**{t('education')}**")
                        if extracted_info['education']:
                            for edu in extracted_info['education']:
                                st.write(f"- {edu['institution']}")
                                if edu['degree']:
                                    st.write(f"  {edu['degree']}")
                                if edu['dates']:
                                    st.write(f"  {' - '.join(edu['dates'])}")
                        else:
                            st.write("None detected")
                            
                        # Work Experience
                        st.markdown(f"**{t('work_experience')}**")
                        if extracted_info['work_experience']:
                            for exp in extracted_info['work_experience']:
                                st.write(f"- {exp['company']}")
                                if exp['title']:
                                    st.write(f"  {exp['title']}")
                                if exp['dates']:
                                    st.write(f"  {' - '.join(exp['dates'])}")
                        else:
                            st.write("None detected")
                        
                        # Languages
                        st.markdown(f"**{t('languages')}**")
                        if extracted_info['languages']:
                            for lang in extracted_info['languages']:
                                st.write(f"- {lang}")
                        else:
                            st.write("None detected")
                            
                        # Certifications
                        st.markdown(f"**{t('certifications')}**")
                        if extracted_info['certifications']:
                            for cert in extracted_info['certifications']:
                                st.write(f"- {cert}")
                        else:
                            st.write("None detected")
                        
                        # Summary
                        if extracted_info['summary']:
                            st.markdown(f"**{t('summary')}**")
                            st.write(extracted_info['summary'])
                    
                    # Edit button
                    if st.button(t("edit_extracted")):
                        st.session_state.editing = True
                        st.session_state.current_data = extracted_info
                        st.experimental_rerun()
                    
                    # Export options
                    st.subheader(t("export_results"))
                    export_format = st.selectbox(
                        t("export_format"),
                        options=["JSON", "CSV", "XLSX"]
                    )
                    
                    if export_format == "JSON":
                        json_str = json.dumps(extracted_info, indent=2)
                        b64 = base64.b64encode(json_str.encode()).decode()
                        href = f'<a href="data:file/json;base64,{b64}" download="cv_results.json">{t("download")} JSON</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        
                    elif export_format == "CSV":
                        # Flatten nested data for CSV
                        data = {
                            "Name": personal_info['name'],
                            "Email": personal_info['email'],
                            "Phone": personal_info['phone'],
                            "Address": personal_info['address'],
                            "Skills": ", ".join(extracted_info['skills']),
                            "Languages": ", ".join(extracted_info['languages']),
                            "Certifications": ", ".join(extracted_info['certifications']),
                            "Summary": extracted_info['summary']
                        }
                        df = pd.DataFrame([data])
                        csv = df.to_csv(index=False)
                        b64 = base64.b64encode(csv.encode()).decode()
                        href = f'<a href="data:file/csv;base64,{b64}" download="cv_results.csv">{t("download")} CSV</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        
                    elif export_format == "XLSX":
                        # Create Excel file
                        data = {
                            "Name": [personal_info['name']],
                            "Email": [personal_info['email']],
                            "Phone": [personal_info['phone']],
                            "Address": [personal_info['address']],
                            "Skills": [", ".join(extracted_info['skills'])],
                            "Languages": [", ".join(extracted_info['languages'])],
                            "Summary": [extracted_info['summary']]
                        }
                        df = pd.DataFrame(data)
                        
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, sheet_name="CV_Data", index=False)
                            
                            # Write education to separate sheet
                            if extracted_info['education']:
                                edu_df = pd.DataFrame(extracted_info['education'])
                                edu_df.to_excel(writer, sheet_name="Education", index=False)
                                
                            # Write work experience to separate sheet
                            if extracted_info['work_experience']:
                                exp_df = pd.DataFrame(extracted_info['work_experience'])
                                exp_df.to_excel(writer, sheet_name="Experience", index=False)
                        
                        b64 = base64.b64encode(output.getvalue()).decode()
                        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="cv_results.xlsx">{t("download")} XLSX</a>'
                        st.markdown(href, unsafe_allow_html=True)
                
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
                    
                finally:
                    # Clean up temp file
                    os.remove(temp_path)
                    os.rmdir(temp_dir)

# Bulk Processing
with tab2:
    st.header(t("bulk_processing"))
    st.write(t("upload_description"))
    
    uploaded_files = st.file_uploader(
        "Upload Your Documents", 
        type=config['app']['supported_formats'],
        accept_multiple_files=False,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        if st.button(t("processing_button"), key="bulk_process"):
            # Create temp directory for files
            temp_dir = tempfile.mkdtemp()
            file_paths = []
            
            # Save uploaded files
            for uploaded_file in uploaded_files:
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                file_paths.append(temp_path)
            
            # Progress bar
            progress_bar = st.progress(0)
            progress_text = st.empty()
            
            # Results storage
            all_results = []
            
            # Process each file
            for i, file_path in enumerate(file_paths):
                try:
                    # Update progress
                    progress = (i) / len(file_paths)
                    progress_bar.progress(progress)
                    progress_text.text(f"{t('processing')} {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")
                    
                    # Process file
                    ocr_result = ocr.process_file(file_path)
                    
                    # Language Detection
                    lang_result = lang_detector.detect_language(ocr_result['text'])
                    detected_lang = lang_result['lang_code']
                    
                    # NLP Processing
                    doc = nlp.process_text(ocr_result['text'], detected_lang)
                    
                    # Entity Extraction
                    extracted_info = entity_extractor.extract_entities(doc, detected_lang)
                    
                    # Add file info
                    result = {
                        'filename': os.path.basename(file_path),
                        'language': detected_lang,
                        'language_confidence': lang_result['confidence'],
                        'extracted_info': extracted_info
                    }
                    
                    all_results.append(result)
                    
                except Exception as e:
                    st.error(f"Error processing {os.path.basename(file_path)}: {str(e)}")
            
            # Complete progress
            progress_bar.progress(1.0)
            progress_text.text(f"{t('processing')} {len(file_paths)}/{len(file_paths)}")
            
            # Display results summary
            st.subheader(t("results_summary"))
            
            # Prepare DataFrame for display
            summary_data = []
            for result in all_results:
                personal_info = result['extracted_info']['personal_info']
                summary_data.append({
                    'Filename': result['filename'],
                    'Name': personal_info['name'],
                    'Language': 'English' if result['language'] == 'eng' else 'Bahasa Indonesia',
                    'Email': personal_info['email'],
                    'Phone': personal_info['phone'],
                    'Skills Count': len(result['extracted_info']['skills']),
                    'Skills': ', '.join(result['extracted_info']['skills'][:5]) + ('...' if len(result['extracted_info']['skills']) > 5 else ''),
                    'Education': len(result['extracted_info']['education']),
                    'Experience': len(result['extracted_info']['work_experience']),
                    'Confidence': result['extracted_info']['confidence_scores']['overall']
                })
            
            df = pd.DataFrame(summary_data)
            
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Get all skills across all CVs
                all_skills = set()
                for result in all_results:
                    all_skills.update(result['extracted_info']['skills'])
                
                selected_skills = st.multiselect(
                    t("filter_by_skills"),
                    options=sorted(list(all_skills))
                )
            
            with col2:
                lang_filter = st.selectbox(
                    t("filter_by_language"),
                    options=["All", "English"]
                )
            
            with col3:
                search_term = st.text_input(t("search"))
            
            # Apply filters
            filtered_df = df.copy()
            
            if selected_skills:
                mask = filtered_df['Skills'].apply(lambda x: any(skill in x for skill in selected_skills))
                filtered_df = filtered_df[mask]
                
            if lang_filter != "All":
                filtered_df = filtered_df[filtered_df['Language'] == lang_filter]
                
            if search_term:
                # Search across multiple columns
                search_mask = (
                    filtered_df['Name'].str.contains(search_term, case=False, na=False) |
                    filtered_df['Email'].str.contains(search_term, case=False, na=False) |
                    filtered_df['Skills'].str.contains(search_term, case=False, na=False)
                )
                filtered_df = filtered_df[search_mask]
            
            # Display filtered results
            st.dataframe(filtered_df)
            
            # Export options
            st.subheader(t("export_results"))
            export_format = st.selectbox(
                t("export_format"),
                options=["CSV", "XLSX", "JSON"],
                key="bulk_export_format"
            )
            
            if export_format == "CSV":
                csv = filtered_df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="cv_analysis_results.csv">{t("download")} CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
                
            elif export_format == "XLSX":
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    filtered_df.to_excel(writer, sheet_name="Summary", index=False)
                    
                    # Add detailed sheets for each CV
                    for i, result in enumerate(all_results):
                        if i < 10:  # Limit to 10 detailed sheets to avoid Excel limits
                            # Personal info
                            personal_df = pd.DataFrame([result['extracted_info']['personal_info']])
                            
                            # Skills
                            skills_df = pd.DataFrame({'Skill': result['extracted_info']['skills']})
                            
                            # Combine into one sheet
                            sheet_name = f"CV_{i+1}"
                            personal_df.to_excel(writer, sheet_name=sheet_name, startrow=0, index=False)
                            skills_df.to_excel(writer, sheet_name=sheet_name, startrow=len(personal_df)+2, index=False)
                
                b64 = base64.b64encode(output.getvalue()).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="cv_analysis_results.xlsx">{t("download")} XLSX</a>'
                st.markdown(href, unsafe_allow_html=True)
                
            elif export_format == "JSON":
                json_str = json.dumps(all_results, indent=2, default=str)
                b64 = base64.b64encode(json_str.encode()).decode()
                href = f'<a href="data:file/json;base64,{b64}" download="cv_analysis_results.json">{t("download")} JSON</a>'
                st.markdown(href, unsafe_allow_html=True)
            
            # Clean up temp files
            for file_path in file_paths:
                os.remove(file_path)
            os.rmdir(temp_dir)
    else:
        st.info(t("no_files"))