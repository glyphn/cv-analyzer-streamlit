# modules/skills_matcher.py
import json
import os
import logging
from typing import List, Dict, Any, Set, Tuple
from rapidfuzz import process, fuzz

class SkillsMatcher:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.skills_dict = self._load_skills_dictionaries()
        self.fuzzy_threshold = self.config['skills']['fuzzy_match_threshold']
        
    def _load_skills_dictionaries(self) -> Dict[str, Set[str]]:
        """Load skills dictionaries for both languages"""
        skills_dict = {
            'eng': set(),
            'ind': set()
        }
        
        # Load English skills
        eng_path = self.config['skills']['dictionaries']['english']
        if os.path.exists(eng_path):
            try:
                with open(eng_path, 'r', encoding='utf-8') as f:
                    eng_skills = json.load(f)
                skills_dict['eng'] = set(eng_skills)
                self.logger.info(f"Loaded {len(skills_dict['eng'])} English skills")
            except Exception as e:
                self.logger.error(f"Error loading English skills dictionary: {str(e)}")
        
        # Load Indonesian skills
        ind_path = self.config['skills']['dictionaries']['indonesian']
        if os.path.exists(ind_path):
            try:
                with open(ind_path, 'r', encoding='utf-8') as f:
                    ind_skills = json.load(f)
                skills_dict['ind'] = set(ind_skills)
                self.logger.info(f"Loaded {len(skills_dict['ind'])} Indonesian skills")
            except Exception as e:
                self.logger.error(f"Error loading Indonesian skills dictionary: {str(e)}")
                
        return skills_dict
    
    def extract_skills(self, text: str, lang_code: str) -> List[Dict[str, Any]]:
        """
        Extract skills from text using dictionary lookup and fuzzy matching
        Returns list of skills with confidence scores
        """
        if not text or not lang_code in ('eng', 'ind'):
            return []
        
        # Determine which skills dictionary to use
        skills_set = self.skills_dict.get(lang_code, self.skills_dict['eng'])
        
        if not skills_set:
            self.logger.warning(f"No skills dictionary available for {lang_code}")
            return []
        
        # Normalize text for better matching
        text_lower = text.lower()
        
        # Exact matches first
        exact_matches = []
        for skill in skills_set:
            if skill.lower() in text_lower:
                exact_matches.append({
                    'skill': skill,
                    'confidence': 1.0,
                    'match_type': 'exact'
                })
        
        # Fuzzy matching for skills not found exactly
        # Extract words and phrases (n-grams) from the text
        words = text_lower.split()
        phrases = []
        for i in range(len(words)):
            for j in range(1, min(5, len(words) - i + 1)):  # Up to 4-word phrases
                phrases.append(' '.join(words[i:i+j]))
        
        # Fuzzy match these phrases against the skills dictionary
        fuzzy_matches = []
        for phrase in phrases:
            if len(phrase) < 3:  # Skip very short phrases
                continue
                
            # Check if this phrase might be a skill
            matches = process.extract(
                phrase, 
                skills_set, 
                scorer=fuzz.token_sort_ratio, 
                score_cutoff=self.fuzzy_threshold,
                limit=1
            )
            
            if matches:
                skill, score = matches[0]
                # Check if this skill is already in exact matches
                if not any(m['skill'] == skill for m in exact_matches):
                    fuzzy_matches.append({
                        'skill': skill,
                        'confidence': score / 100.0,  # Convert to 0-1 scale
                        'match_type': 'fuzzy'
                    })
        
        # Combine results, prioritizing exact matches
        all_matches = exact_matches + fuzzy_matches
        
        # Remove duplicates (keep the highest confidence one)
        unique_skills = {}
        for match in all_matches:
            skill = match['skill']
            if skill not in unique_skills or match['confidence'] > unique_skills[skill]['confidence']:
                unique_skills[skill] = match
        
        return list(unique_skills.values())
    
    def categorize_skills(self, skills: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Categorize skills into hard skills and soft skills
        This is a simplified implementation - a real one would use a more sophisticated categorization
        """
        # Common soft skills keywords
        soft_skills_keywords = {
            'eng': ['communication', 'leadership', 'teamwork', 'management', 'organization', 
                   'problem solving', 'creativity', 'critical thinking', 'adaptability'],
            'ind': ['komunikasi', 'kepemimpinan', 'kerja tim', 'manajemen', 'organisasi',
                   'pemecahan masalah', 'kreativitas', 'berpikir kritis', 'adaptasi']
        }
        
        # Flatten the keywords for easier matching
        all_soft_keywords = set()
        for lang_keywords in soft_skills_keywords.values():
            all_soft_keywords.update([kw.lower() for kw in lang_keywords])
        
        hard_skills = []
        soft_skills = []
        
        for skill_data in skills:
            skill = skill_data['skill']
            # Check if it's a soft skill
            if any(kw in skill.lower() for kw in all_soft_keywords):
                soft_skills.append(skill)
            else:
                hard_skills.append(skill)
        
        return {
            'hard_skills': hard_skills,
            'soft_skills': soft_skills
        }