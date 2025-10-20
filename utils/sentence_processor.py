import re
from typing import Optional, Set
from colorama import Fore

class SentenceProcessor:
    """Helper class to process streaming text into complete sentences"""
    
    def __init__(self):
        self.buffer = ""
        # More comprehensive sentence ending pattern
        self.sentence_end_pattern = re.compile(r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$')
        self.processed_sentences: Set[str] = set()  # Track processed sentences
        
    def _clean_sentence(self, sentence: str) -> str:
        """Clean and normalize a sentence"""
        # Remove extra whitespace and normalize
        cleaned = ' '.join(sentence.split())
        # Ensure the sentence has proper ending punctuation
        if cleaned and cleaned[-1] not in '.!?':
            cleaned += '.'
        return cleaned
    
    def _is_complete_sentence(self, text: str) -> bool:
        """Check if text forms a complete sentence"""
        # Basic checks for sentence completeness
        if not text:
            return False
        
        # Check for proper sentence structure (starts with capital, ends with punctuation)
        has_proper_start = text[0].isupper() if text else False
        has_proper_end = text[-1] in '.!?' if text else False
        min_word_count = len(text.split()) >= 2  # At least 2 words
        
        return has_proper_start and has_proper_end and min_word_count
    
    def process_chunk(self, text: str) -> list[str]:
        """Process a chunk of text and return complete, unique sentences"""
        self.buffer += text
        sentences = []
        
        # Split buffer into potential sentences
        potential_sentences = self.sentence_end_pattern.split(self.buffer)
        
        # If we have multiple potential sentences
        if len(potential_sentences) > 1:
            # Process all but the last piece (which might be incomplete)
            complete_sentences = potential_sentences[:-1]
            self.buffer = potential_sentences[-1]
            
            for sentence in complete_sentences:
                cleaned_sentence = self._clean_sentence(sentence)
                if (self._is_complete_sentence(cleaned_sentence) and 
                    cleaned_sentence not in self.processed_sentences):
                    sentences.append(cleaned_sentence)
                    self.processed_sentences.add(cleaned_sentence)
                    print(f"{Fore.CYAN}New complete sentence detected: {cleaned_sentence}{Fore.RESET}")
        else:
            # Check if our single buffer is a complete sentence
            if text.strip() and self._is_complete_sentence(self.buffer):
                cleaned_sentence = self._clean_sentence(self.buffer)
                if cleaned_sentence not in self.processed_sentences:
                    sentences.append(cleaned_sentence)
                    self.processed_sentences.add(cleaned_sentence)
                    self.buffer = ""
                    print(f"{Fore.CYAN}New complete sentence detected: {cleaned_sentence}{Fore.RESET}")
        
        return sentences
    
    def get_remaining(self) -> Optional[str]:
        """Get any remaining text in buffer if it forms a complete sentence"""
        if self.buffer:
            cleaned_buffer = self._clean_sentence(self.buffer)
            if (self._is_complete_sentence(cleaned_buffer) and 
                cleaned_buffer not in self.processed_sentences):
                self.buffer = ""
                self.processed_sentences.add(cleaned_buffer)
                return cleaned_buffer
        return None
        