"""
Entity Extraction module for Trend Hunter
Extracts product names, brands, and trending terms from text
"""

import re
import logging
from typing import List, Dict, Set, Tuple
from collections import Counter
import string

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract entities (product names, brands, keywords) from text"""
    
    def __init__(self):
        self.min_ngram = 1
        self.max_ngram = 4
        self.min_frequency = 2
        
        # Common stopwords (expanded list)
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'can', 'may', 'might', 'must', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me',
            'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
            'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
            'really', 'like', 'get', 'got', 'want', 'need', 'know', 'think',
            'see', 'look', 'use', 'make', 'good', 'new', 'first', 'last', 'long'
        }
        
        # Product indicators (words that often appear near product names)
        self.product_indicators = {
            'product', 'gadget', 'device', 'tool', 'app', 'software', 'service',
            'brand', 'model', 'version', 'kit', 'set', 'system', 'platform',
            'phone', 'laptop', 'watch', 'case', 'accessory', 'gear'
        }
        
        logger.info("Entity extractor initialized")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove markdown/formatting
        text = re.sub(r'[*_~`#]', '', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words
        Preserves some punctuation for product names (e.g., "AirPods Pro")
        """
        # Clean text first
        text = self.clean_text(text)
        
        # Split on whitespace and some punctuation
        tokens = re.findall(r'\b[\w\-]+\b', text)
        
        return tokens
    
    def is_valid_token(self, token: str) -> bool:
        """Check if token is valid for extraction"""
        token_lower = token.lower()
        
        # Skip stopwords
        if token_lower in self.stopwords:
            return False
        
        # Skip pure numbers
        if token.isdigit():
            return False
        
        # Skip very short tokens (< 3 chars)
        if len(token) < 3:
            return False
        
        # Skip if all punctuation
        if all(c in string.punctuation for c in token):
            return False
        
        return True
    
    def extract_ngrams(self, tokens: List[str], n: int) -> List[str]:
        """Extract n-grams from tokens"""
        ngrams = []
        
        for i in range(len(tokens) - n + 1):
            ngram_tokens = tokens[i:i+n]
            
            # Check if all tokens are valid
            if all(self.is_valid_token(t) for t in ngram_tokens):
                ngram = ' '.join(ngram_tokens)
                ngrams.append(ngram)
        
        return ngrams
    
    def extract_candidate_entities(self, text: str) -> List[str]:
        """
        Extract candidate entities from text using n-grams
        """
        candidates = []
        
        # Tokenize
        tokens = self.tokenize(text)
        
        # Extract n-grams of different lengths
        for n in range(self.min_ngram, self.max_ngram + 1):
            ngrams = self.extract_ngrams(tokens, n)
            candidates.extend(ngrams)
        
        return candidates
    
    def score_entity(self, entity: str) -> float:
        """
        Score entity based on likelihood of being a product/trend
        Higher score = more likely to be interesting
        """
        score = 0.0
        entity_lower = entity.lower()
        
        # Capitalization bonus (likely proper noun/product name)
        if any(word[0].isupper() for word in entity.split() if len(word) > 0):
            score += 2.0
        
        # Contains product indicator
        for indicator in self.product_indicators:
            if indicator in entity_lower:
                score += 1.5
        
        # Contains numbers (often product models: "iPhone 15", "PS5")
        if re.search(r'\d', entity):
            score += 1.0
        
        # Longer phrases often more specific (up to a point)
        word_count = len(entity.split())
        if word_count == 2:
            score += 1.0
        elif word_count == 3:
            score += 0.5
        
        # Contains hyphen (often product names: "Air-Fryer")
        if '-' in entity:
            score += 0.5
        
        return score
    
    def extract_entities_from_posts(self, posts: List[Dict]) -> Dict[str, int]:
        """
        Extract entities from multiple posts
        Returns dict of entity: frequency
        """
        all_candidates = []
        
        for post in posts:
            title = post.get('title', '')
            text = post.get('text', '')
            
            # Extract from both title and text
            candidates = self.extract_candidate_entities(f"{title} {text}")
            all_candidates.extend(candidates)
        
        # Count frequencies
        entity_counts = Counter(all_candidates)
        
        # Filter by minimum frequency
        filtered_entities = {
            entity: count 
            for entity, count in entity_counts.items() 
            if count >= self.min_frequency
        }
        
        return filtered_entities
    
    def extract_top_entities(self, posts: List[Dict], top_n: int = 100) -> List[Tuple[str, int, float]]:
        """
        Extract top N entities from posts
        Returns list of (entity, frequency, score) tuples
        """
        # Get entity frequencies
        entity_counts = self.extract_entities_from_posts(posts)
        
        # Score each entity
        entity_scores = []
        for entity, frequency in entity_counts.items():
            score = self.score_entity(entity)
            # Combined score: frequency * entity_score
            combined_score = frequency * score
            entity_scores.append((entity, frequency, combined_score))
        
        # Sort by combined score
        entity_scores.sort(key=lambda x: x[2], reverse=True)
        
        return entity_scores[:top_n]
    
    def extract_hashtags(self, text: str) -> Set[str]:
        """Extract hashtags from text"""
        hashtags = set(re.findall(r'#(\w+)', text))
        return hashtags
    
    def extract_mentions(self, text: str) -> Set[str]:
        """Extract @mentions from text"""
        mentions = set(re.findall(r'@(\w+)', text))
        return mentions
    
    def extract_brands(self, text: str) -> Set[str]:
        """
        Extract potential brand names (capitalized words)
        Simple heuristic: consecutive capitalized words
        """
        # Find capitalized words
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter out common non-brand words
        common_words = {'Reddit', 'TikTok', 'Instagram', 'Facebook', 'Twitter', 'Google'}
        brands = {word for word in words if word not in common_words}
        
        return brands


def main():
    """Test the entity extractor"""
    print("Testing Entity Extractor...")
    
    extractor = EntityExtractor()
    
    # Test posts
    test_posts = [
        {
            'title': 'Check out the new iPhone 15 Pro',
            'text': 'Just got the iPhone 15 Pro and it\'s amazing! Best phone ever.'
        },
        {
            'title': 'Stanley Cup is everywhere',
            'text': 'Why is everyone buying the Stanley Cup tumbler? Saw it on TikTok.'
        },
        {
            'title': 'Air Fryer recommendations',
            'text': 'Looking for a good Air Fryer. Heard the Ninja Air Fryer is great.'
        },
        {
            'title': 'Best wireless earbuds',
            'text': 'Comparing AirPods Pro vs Sony WF-1000XM5. Which one should I get?'
        },
        {
            'title': 'Trending gadgets',
            'text': 'The Steam Deck and Nintendo Switch are selling out everywhere!'
        }
    ]
    
    print("\n" + "="*60)
    print("Extracting entities from test posts...")
    
    # Extract top entities
    top_entities = extractor.extract_top_entities(test_posts, top_n=15)
    
    print("\n📊 Top Entities:")
    print(f"{'Entity':<30} {'Frequency':<12} {'Score':<10}")
    print("-" * 60)
    for entity, freq, score in top_entities:
        print(f"{entity:<30} {freq:<12} {score:<10.2f}")
    
    # Test single text extraction
    print("\n" + "="*60)
    print("Testing single text extraction...")
    test_text = "The new Apple AirPods Pro 2 with USB-C are amazing!"
    
    candidates = extractor.extract_candidate_entities(test_text)
    print(f"\nText: {test_text}")
    print(f"Candidates: {candidates[:10]}")
    
    # Test hashtags and mentions
    social_text = "Check out #AirPodsMax and #AppleEvent! Tag @Apple"
    hashtags = extractor.extract_hashtags(social_text)
    mentions = extractor.extract_mentions(social_text)
    
    print(f"\nSocial text: {social_text}")
    print(f"Hashtags: {hashtags}")
    print(f"Mentions: {mentions}")
    
    print("\n✅ Entity extractor test completed!")


if __name__ == "__main__":
    main()
