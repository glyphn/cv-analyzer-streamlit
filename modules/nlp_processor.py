# modules/nlp_processor.py
import spacy
import os
from spacy.language import Language

import logging
from pathlib import Path

nlp = spacy.load("en_core_web_trf")  # Requires installation
transformer = nlp.get_pipe("transformer")
class NLPProcessor:
    """
    Handles NLP processing of text using spaCy models,
    """
    
    def __init__(self, config):
        """
        Initialize NLP processor with configuration.
        
        Args:
            config (dict): Configuration dictionary containing NLP settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Set up models dictionary
        self.models = {}
        self.load_models()
        
    def load_models(self):
        """Load spaCy models based on configuration"""
        # English models
        try:
            # Try to load transformer model first (higher accuracy)
            self.logger.info("Loading English transformer model...")
            self.models["eng"] = spacy.load(self.config['nlp']['models']['english']['transformer'])
            self.logger.info("English transformer model loaded successfully")
        except (OSError, IOError):
            # Fall back to smaller model if transformer isn't available
            self.logger.warning("English transformer model not found, falling back to smaller model")
            try:
                self.models["eng"] = spacy.load(self.config['nlp']['models']['english']['fallback'])
                self.logger.info("English fallback model loaded successfully")
            except (OSError, IOError) as e:
                self.logger.error(f"Failed to load English NLP models: {str(e)}")
                raise RuntimeError(f"Failed to load English NLP models: {str(e)}")
        
        # Indonesian models
    
    
    def process_text(self, text, language_code):
        """
        Process text with the appropriate spaCy model based on language.
        
        Args:
            text (str): Text to process
            language_code (str): Language code ('eng' or 'ind')
            
        Returns:
            spacy.tokens.Doc: Processed spaCy document
        """
        if not text or not language_code:
            self.logger.warning("Empty text or language code provided")
            return None
            
        if language_code not in self.models:
            self.logger.error(f"Unsupported language code: {language_code}")
            raise ValueError(f"Unsupported language code: {language_code}")
        
        try:
            # Process text with the appropriate model
            self.logger.info(f"Processing text with {language_code} model")
            doc = self.models[language_code](text)
            return doc
        except Exception as e:
            self.logger.error(f"Error processing text: {str(e)}")
            raise RuntimeError(f"Error processing text: {str(e)}")
    
    def get_entities(self, doc, entity_types=None):
        """
        Extract named entities from a spaCy document.
        
        Args:
            doc (spacy.tokens.Doc): Processed spaCy document
            entity_types (list, optional): List of entity types to extract
            
        Returns:
            list: List of extracted entities with their types
        """
        if not doc:
            return []
            
        entities = []
        for ent in doc.ents:
            if entity_types is None or ent.label_ in entity_types:
                entities.append({
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'type': ent.label_
                })
        
        return entities
    
    def get_noun_chunks(self, doc):
        """
        Extract noun chunks from a spaCy document.
        Useful for extracting skills and other key phrases.
        
        Args:
            doc (spacy.tokens.Doc): Processed spaCy document
            
        Returns:
            list: List of noun chunks
        """
        if not doc:
            return []
            
        return [chunk.text for chunk in doc.noun_chunks]
    
    def get_sentences(self, doc):
        """
        Extract sentences from a spaCy document.
        
        Args:
            doc (spacy.tokens.Doc): Processed spaCy document
            
        Returns:
            list: List of sentences as strings
        """
        if not doc:
            return []
            
        return [sent.text for sent in doc.sents]
    
    def tokenize(self, text, language_code):
        """
        Tokenize text without full processing.
        
        Args:
            text (str): Text to tokenize
            language_code (str): Language code ('eng' or 'ind')
            
        Returns:
            list: List of tokens
        """
        if not text or not language_code:
            return []
            
        if language_code not in self.models:
            self.logger.error(f"Unsupported language code: {language_code}")
            raise ValueError(f"Unsupported language code: {language_code}")
        
        # Get just the tokenizer from the pipeline
        tokenizer = self.models[language_code].tokenizer
        tokens = tokenizer(text)
        return [token.text for token in tokens]
    
    def get_document_stats(self, doc):
        """
        Get statistics about the document.
        
        Args:
            doc (spacy.tokens.Doc): Processed spaCy document
            
        Returns:
            dict: Dictionary with document statistics
        """
        if not doc:
            return {}
            
        return {
            'token_count': len(doc),
            'sentence_count': len(list(doc.sents)),
            'entity_count': len(doc.ents),
            'noun_chunk_count': len(list(doc.noun_chunks))
        }