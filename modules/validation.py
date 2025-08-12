# modules/validation.py
import re
import logging
from typing import Dict, Any, List, Optional

class Validator:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Regular expressions for validation
        self.email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        self.phone_regex = r'^(?:\+\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}$'
        
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all extracted fields and compute confidence scores
        Returns the original data with added validation info
        """
        validated = data.copy()
        
        # Validate personal information
        if 'personal_info' in data:
            validated['personal_info'] = self.validate_personal_info(data['personal_info'])
        
        # Validate education entries
        if 'education' in data:
            validated['education'] = [self.validate_education(edu) for edu in data['education']]
        
        # Validate work experience entries
        if 'work_experience' in data:
            validated['work_experience'] = [self.validate_work_experience(exp) for exp in data['work_experience']]
        
        # Validate skills
        if 'skills' in data:
            validated['skills'] = self.validate_skills(data['skills'])
        
        # Compute overall validation score
        validated['validation'] = {
            'overall_score': self.compute_overall_validation_score(validated),
            'personal_info_score': self.compute_personal_info_score(validated.get('personal_info', {})),
            'education_score': self.compute_education_score(validated.get('education', [])),
            'experience_score': self.compute_experience_score(validated.get('work_experience', [])),
            'skills_score': self.compute_skills_score(validated.get('skills', []))
        }
        
        return validated
    
    def validate_personal_info(self, personal_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate personal information fields"""
        validated = personal_info.copy()
        
        # Name validation
        if 'name' in personal_info and personal_info['name']:
            name = personal_info['name']
            name_valid = len(name.split()) >= 1 and len(name) >= 3
            validated['name_valid'] = name_valid
        else:
            validated['name_valid'] = False
        
        # Email validation
        if 'email' in personal_info and personal_info['email']:
            email = personal_info['email']
            email_valid = bool(re.match(self.email_regex, email))
            validated['email_valid'] = email_valid
        else:
            validated['email_valid'] = False
            
        # Phone validation
        if 'phone' in personal_info and personal_info['phone']:
            phone = personal_info['phone']
            # Remove common formatting characters for validation
            clean_phone = re.sub(r'[\s\-\(\)\.]', '', phone)
            phone_valid = bool(re.match(self.phone_regex, phone)) and len(clean_phone) >= 7
            validated['phone_valid'] = phone_valid
        else:
            validated['phone_valid'] = False
            
        # Address validation (basic)
        if 'address' in personal_info and personal_info['address']:
            address = personal_info['address']
            address_valid = len(address) >= 10  # Very basic validation
            validated['address_valid'] = address_valid
        else:
            validated['address_valid'] = False
            
        return validated
    
    def validate_education(self, education: Dict[str, Any]) -> Dict[str, Any]:
        """Validate education entry"""
        validated = education.copy()
        
        # Institution validation
        if 'institution' in education and education['institution']:
            institution = education['institution']
            institution_valid = len(institution) >= 3
            validated['institution_valid'] = institution_valid
        else:
            validated['institution_valid'] = False
            
        # Degree validation
        if 'degree' in education and education['degree']:
            degree_valid = True
            validated['degree_valid'] = degree_valid
        else:
            validated['degree_valid'] = False
            
        # Dates validation
        if 'dates' in education and education['dates']:
            dates = education['dates']
            dates_valid = len(dates) > 0
            validated['dates_valid'] = dates_valid
        else:
            validated['dates_valid'] = False
            
        # Overall education entry validation
        validated['valid'] = validated.get('institution_valid', False)
        
        return validated
    
    def validate_work_experience(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """Validate work experience entry"""
        validated = experience.copy()
        
        # Company validation
        if 'company' in experience and experience['company']:
            company = experience['company']
            company_valid = len(company) >= 2
            validated['company_valid'] = company_valid
        else:
            validated['company_valid'] = False
            
        # Title validation
        if 'title' in experience and experience['title']:
            title_valid = True
            validated['title_valid'] = title_valid
        else:
            validated['title_valid'] = False
            
        # Dates validation
        if 'dates' in experience and experience['dates']:
            dates = experience['dates']
            dates_valid = len(dates) > 0
            validated['dates_valid'] = dates_valid
        else:
            validated['dates_valid'] = False
            
        # Responsibilities validation
        if 'responsibilities' in experience and experience['responsibilities']:
            resp_valid = len(experience['responsibilities']) > 0
            validated['responsibilities_valid'] = resp_valid
        else:
            validated['responsibilities_valid'] = False
            
        # Overall experience entry validation
        validated['valid'] = validated.get('company_valid', False)
        
        return validated
    
    def validate_skills(self, skills: List[str]) -> List[str]:
        """Validate skills list (simple validation)"""
        if not skills:
            return []
            
        # Filter out skills that are too short
        return [skill for skill in skills if len(skill) >= 2]
    
    def compute_overall_validation_score(self, data: Dict[str, Any]) -> float:
        """Compute overall validation score"""
        scores = []
        
        # Personal info score (40% weight)
        personal_score = self.compute_personal_info_score(data.get('personal_info', {}))
        scores.append(personal_score * 0.4)
        
        # Education score (20% weight)
        education_score = self.compute_education_score(data.get('education', []))
        scores.append(education_score * 0.2)
        
        # Experience score (20% weight)
        experience_score = self.compute_experience_score(data.get('work_experience', []))
        scores.append(experience_score * 0.2)
        
        # Skills score (20% weight)
        skills_score = self.compute_skills_score(data.get('skills', []))
        scores.append(skills_score * 0.2)
        
        # Overall score
        return sum(scores)
    
    def compute_personal_info_score(self, personal_info: Dict[str, Any]) -> float:
        """Compute validation score for personal information"""
        if not personal_info:
            return 0.0
            
        valid_fields = sum([
            personal_info.get('name_valid', False),
            personal_info.get('email_valid', False),
            personal_info.get('phone_valid', False),
            personal_info.get('address_valid', False)
        ])
        
        # Weight name and email more heavily
        if personal_info.get('name_valid', False) and personal_info.get('email_valid', False):
            return min(1.0, valid_fields / 3)  # Name and email count as 2/3 of perfect score
        else:
            return valid_fields / 4  # Otherwise, need all 4 fields for perfect score
    
    def compute_education_score(self, education: List[Dict[str, Any]]) -> float:
        """Compute validation score for education entries"""
        if not education:
            return 0.0
            
        # Count valid education entries
        valid_entries = sum(1 for edu in education if edu.get('valid', False))
        
        # Score based on presence of at least one valid education entry
        return 1.0 if valid_entries > 0 else 0.0
    
    def compute_experience_score(self, experience: List[Dict[str, Any]]) -> float:
        """Compute validation score for work experience entries"""
        if not experience:
            return 0.0
            
        # Count valid work experience entries
        valid_entries = sum(1 for exp in experience if exp.get('valid', False))
        
        # Score based on presence of at least one valid experience entry
        return 1.0 if valid_entries > 0 else 0.0
    
    def compute_skills_score(self, skills: List[str]) -> float:
        """Compute validation score for skills"""
        if not skills:
            return 0.0
            
        # Score based on number of skills
        num_skills = len(skills)
        if num_skills >= 5:
            return 1.0
        elif num_skills >= 3:
            return 0.8
        elif num_skills >= 1:
            return 0.5
        else:
            return 0.0