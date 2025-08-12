# modules/entity_extractor.py
import re
import logging
from typing import Dict, Any, List, Tuple
import spacy
from spacy.tokens import Doc

class EntityExtractor:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Regular expressions for common fields
        self.email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_regex = r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b'
        
        # Bilingual education keywords
        self.education_keywords = {
            'eng': ['education', 'university', 'college', 'degree', 'bachelor', 'master', 'phd', 'diploma'],
            'ind': ['pendidikan', 'universitas', 'kuliah', 'gelar', 'sarjana', 'magister', 'doktor', 'diploma']
        }
        
        # Bilingual work experience keywords
        self.experience_keywords = {
            'eng': ['experience', 'work', 'employment', 'job', 'position', 'role', 'career'],
            'ind': ['pengalaman', 'kerja', 'pekerjaan', 'posisi', 'jabatan', 'karir']
        }
    
    def extract_entities(self, doc: Doc, lang_code: str) -> Dict[str, Any]:
        """Extract structured information from a spaCy Doc"""
        result = {
            'personal_info': self.extract_personal_info(doc, lang_code),
            'skills': self.extract_skills(doc, lang_code),
            'education': self.extract_education(doc, lang_code),
            'work_experience': self.extract_work_experience(doc, lang_code),
            'languages': self.extract_languages(doc, lang_code),
            'certifications': self.extract_certifications(doc, lang_code),
            'summary': self.extract_summary(doc, lang_code),
        }
        
        # Add confidence metrics
        result['confidence_scores'] = {
            'overall': self.calculate_overall_confidence(result),
            'personal_info': self.calculate_personal_info_confidence(result['personal_info']),
            'skills': 0.85 if result['skills'] else 0.0,
            'education': 0.85 if result['education'] else 0.0,
            'work_experience': 0.85 if result['work_experience'] else 0.0
        }
        
        return result
    
    def extract_personal_info(self, doc: Doc, lang_code: str) -> Dict[str, Any]:
        """Extract personal information like name, email, phone, address"""
        text = doc.text
        
        # Extract email
        email_matches = re.findall(self.email_regex, text)
        email = email_matches[0] if email_matches else None
        
        # Extract phone
        phone_matches = re.findall(self.phone_regex, text)
        phone = phone_matches[0] if phone_matches else None
        
        # Extract name (first few PERSON entities)
        name_entities = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
        name = name_entities[0] if name_entities else None
        
        # Extract address (look for address-related entities and patterns)
        address = self.extract_address(doc, lang_code)
        
        return {
            'name': name,
            'email': email,
            'phone': phone,
            'address': address
        }
    
    def extract_address(self, doc: Doc, lang_code: str) -> str:
        """Extract physical address from the document"""
        # This is a simplified implementation
        # Would need more complex logic for real-world addresses
        
        # Look for GPE (geopolitical entity) and LOC (location) entities
        address_entities = [ent.text for ent in doc.ents if ent.label_ in ('GPE', 'LOC')]
        
        # Look for postal codes
        postal_pattern = r'\b\d{5}\b' if lang_code == 'eng' else r'\b\d{5}\b'
        postal_matches = re.findall(postal_pattern, doc.text)
        
        # Combine for a simple address extraction
        if address_entities and postal_matches:
            address_parts = address_entities[:2]  # Limit to first two location entities
            address_parts.extend(postal_matches[:1])  # Add first postal code
            return ", ".join(address_parts)
        elif address_entities:
            return ", ".join(address_entities[:2])
        
        return None
    
    def extract_skills(self, doc: Doc, lang_code: str) -> List[str]:
        """Extract skills from the document"""
        # This would be enhanced with skills_matcher.py module
        # Here's a simple implementation
        
        # Look for skill-related sections
        text = doc.text.lower()
        skill_headers = {
            'eng': ['skills', 'technical skills', 'competencies'],
            'ind': ['keahlian', 'keterampilan', 'kompetensi']
        }
        
        # Just a basic extraction for now
        # A real implementation would use the skills dictionary and fuzzy matching
        skills = []
        
        # Extract SKILL entities if the model supports it
        skills.extend([ent.text for ent in doc.ents if ent.label_ == 'SKILL'])
        
        # Add some basic skill patterns
        programming_skills = ['Python', 'Java', 'JavaScript', 'HTML', 'CSS', 'SQL']
        for skill in programming_skills:
            if skill.lower() in text:
                skills.append(skill)
        
        return list(set(skills))  # Remove duplicates
    
    def extract_education(self, doc: Doc, lang_code: str) -> List[Dict[str, Any]]:
        """Extract education history"""
        # This would need more complex parsing in a real implementation
        education_entries = []
        
        # Look for education keywords and nearby ORG entities
        education_keywords = self.education_keywords[lang_code]
        
        # Find sentences that might contain education information
        for sent in doc.sents:
            sent_text = sent.text.lower()
            if any(keyword in sent_text for keyword in education_keywords):
                # Look for organizations in this sentence
                orgs = [ent.text for ent in sent.ents if ent.label_ == 'ORG']
                
                if orgs:
                    # Extract dates nearby
                    dates = [ent.text for ent in sent.ents if ent.label_ == 'DATE']
                    
                    education_entries.append({
                        'institution': orgs[0],
                        'degree': None,  # Would need more specific extraction
                        'field': None,   # Would need more specific extraction
                        'dates': dates[:2] if dates else None
                    })
        
        return education_entries
    
    def extract_work_experience(self, doc: Doc, lang_code: str) -> List[Dict[str, Any]]:
        """Extract work experience history"""
        # Similar approach to education, but for work experience
        experience_entries = []
        
        # Look for work experience keywords and nearby ORG entities
        experience_keywords = self.experience_keywords[lang_code]
        
        # Find sections that might contain work information
        for sent in doc.sents:
            sent_text = sent.text.lower()
            if any(keyword in sent_text for keyword in experience_keywords):
                # Look for organizations in this sentence
                orgs = [ent.text for ent in sent.ents if ent.label_ == 'ORG']
                
                if orgs:
                    # Extract dates nearby
                    dates = [ent.text for ent in sent.ents if ent.label_ == 'DATE']
                    
                    experience_entries.append({
                        'company': orgs[0],
                        'title': None,  # Would need more specific extraction
                        'dates': dates[:2] if dates else None,
                        'responsibilities': []  # Would need more complex extraction
                    })
        
        return experience_entries
    
    def extract_languages(self, doc: Doc, lang_code: str) -> List[str]:
        """Extract languages spoken"""
        # Simple implementation
        languages = []
        language_keywords = {
            'eng': ['language', 'languages', 'speak', 'fluent'],
        }
        
        # Common languages
        common_languages = ['English', 'Indonesian', 'French', 'Spanish', 'German', 'Chinese']
        
        for sent in doc.sents:
            sent_text = sent.text.lower()
            if any(keyword in sent_text for keyword in language_keywords[lang_code]):
                for lang in common_languages:
                    if lang.lower() in sent_text:
                        languages.append(lang)
        
        return list(set(languages))
    
    def extract_certifications(self, doc: Doc, lang_code: str) -> List[str]:
        """Extract certifications"""
        # Simple implementation
        certifications = []
        cert_keywords = {
            'eng': ['certification', 'certificate', 'certified'],
        }
        
        for sent in doc.sents:
            sent_text = sent.text.lower()
            if any(keyword in sent_text for keyword in cert_keywords[lang_code]):
                # Look for organizations or certifications (typically PROPER nouns)
                for token in sent:
                    if token.pos_ == 'PROPN' and len(token.text) > 2:
                        certifications.append(token.text)
        
        return list(set(certifications))
    
    def extract_summary(self, doc: Doc, lang_code: str) -> str:
        """Extract professional summary"""
        # Look for a professional summary/profile section
        summary_headers = {
            'eng': ['summary', 'profile', 'professional summary', 'about me'],
            'ind': ['ringkasan', 'profil', 'tentang saya']
        }
        
        text = doc.text.lower()
        for header in summary_headers[lang_code]:
            if header in text:
                # Find the position of the header
                pos = text.find(header)
                # Get text after the header until the next section (roughly)
                section_text = doc.text[pos:pos+300]  # Grab the next ~300 chars
                # Look for the end of this section (next header)
                for next_header in summary_headers[lang_code]:
                    if next_header != header and next_header in section_text.lower():
                        end_pos = section_text.lower().find(next_header)
                        section_text = section_text[:end_pos]
                
                # Clean up and return
                section_text = section_text.replace(header, '', 1).strip()
                return section_text
        
        # If no explicit summary found, try to use the first paragraph
        for sent in list(doc.sents)[:3]:  # First three sentences
            if len(sent.text.split()) > 10:  # Reasonably long sentence
                return sent.text
                
        return None
    
    def calculate_overall_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate overall confidence score for extracted information"""
        # This would be more sophisticated in a real implementation
        # Consider factors like OCR quality, NER confidence, etc.
        
        if not result['personal_info']['name'] or not result['personal_info']['email']:
            # Missing key information
            return 0.5
            
        if not result['skills'] or len(result['skills']) < 2:
            # Very few skills found
            return 0.6
            
        if not result['education'] or not result['work_experience']:
            # Missing either education or work experience
            return 0.7
            
        # All key sections present
        return 0.9
    
    def calculate_personal_info_confidence(self, personal_info: Dict[str, Any]) -> float:
        """Calculate confidence for personal information"""
        score = 0.0
        count = 0
        
        # Name found
        if personal_info['name']:
            score += 1.0
            count += 1
            
        # Email validation
        if personal_info['email'] and re.match(self.email_regex, personal_info['email']):
            score += 1.0
            count += 1
        
        # Phone validation
        if personal_info['phone'] and re.match(self.phone_regex, personal_info['phone']):
            score += 1.0
            count += 1
            
        # Address found
        if personal_info['address']:
            score += 0.8  # Less confidence in address extraction
            count += 1
            
        return score / count if count > 0 else 0.0