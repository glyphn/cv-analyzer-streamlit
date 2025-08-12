# Bilingual CV Document Analyzer

A powerful, fully offline application for processing, analyzing, and extracting structured information from resumes/CVs in English with Streamlit interface and CLI capabilities.

## Features

- **Document Processing**: Support for PDF, DOCX, PNG, JPG, and ZIP archives
- **High-Accuracy OCR**: Built on Tesseract with preprocessing for optimal text extraction
- **Language Detection**: Automatic detection between supported languages
- **Advanced NLP Processing**: Using spaCy pipelines with transformer models
- **Structured Information Extraction**:
  - Personal Information (name, email, phone, address)
  - Skills (with fuzzy matching)
  - Education History
  - Work Experience
  - Languages
  - Certifications
  - Professional Summary
- **User-Friendly Interface**:
  - Single document or bulk processing
  - Real-time progress tracking
  - Entity visualization
  - Editable extraction results
- **Export Options**:
  - JSON, CSV, XLSX formats
  - Annotated PDFs with entity highlights

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/cv-analyzer-streamlit.git
cd cv-analyzer-streamlit

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install spaCy models
python -m spacy download en_core_web_trf
python -m spacy download en_core_web_sm
```

## Usage

### Streamlit Interface

```bash
streamlit run app.py
```

Navigate to the provided URL (typically http://localhost:8501) to access the application.

### Command Line Interface

```bash
# Process a single file
python cli.py --mode single --input ./path/to/resume.pdf --output ./results.json

# Process multiple files
python cli.py --mode bulk --input ./resumes_folder --output ./results.xlsx --format xlsx

# Additional options
python cli.py --mode bulk --input ./resumes --output ./results.csv --model en_core_web_trf --ocr tesseract --language auto --annotate-pdfs true
```

## Configuration

Edit the `config.yaml` file to customize settings:

```yaml
app:
  name: "CV Document Analyzer"
  supported_formats: ["pdf", "docx", "png", "jpg", "jpeg", "zip"]
  supported_languages: ["eng"]

ocr:
  tesseract:
    psm_mode: 3
    languages: ["eng"]
  engine: "tesseract"
  languages: ["eng"]
  dpi: 300
  oem: 3
  preprocessing:
    deskew: true
    denoise: true
    adaptive_threshold: true
    binarization: true

nlp:
  models:
    english:
      transformer: "en_core_web_trf"
      small: "en_core_web_sm"
  use_transformer: true
```

## Project Structure

```
cv-analyzer-streamlit/
├── app.py                  # Streamlit application
├── cli.py                  # Command line interface
├── config.yaml             # Configuration settings
├── requirements.txt        # Dependencies
├── modules/
│   ├── ocr_processor.py    # OCR processing
│   ├── language_detector.py # Language detection
│   ├── nlp_processor.py    # NLP processing
│   ├── entity_extractor.py # Entity extraction
│   ├── exporter.py         # Result export functionality
│   └── utils.py            # Utility functions
└── data/
    └── skills_dictionary.json # Skills database
```

## Requirements

See [requirements.txt](requirements.txt) for the complete list of dependencies.

## License

[MIT License](LICENSE)

## Contributors

- Your Name

## Acknowledgments

- This project uses [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text extraction
- NLP processing powered by [spaCy](https://spacy.io/)
- UI built with [Streamlit](https://streamlit.io/)