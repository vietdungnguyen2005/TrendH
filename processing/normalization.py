"""
Normalization module for Trend Hunter
Normalizes entity variants and creates canonical mappings
"""

import re
import logging
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import unicodedata
import json

logger = logging.getLogger(__name__)


class EntityNormalizer:
    """Normalize entity variants to canonical forms"""
    
    def __init__(self):
        # Common substitutions for normalization
        self.substitutions = {
            '&': 'and',
            '+': 'plus',
            '@': 'at',
        }
        
        # Known brand/product variations (can be extended)
        self.known_variants = {
            'airpods': ['airpod', 'air pods', 'air pod', 'airpods pro', 'airpod pro'],
            'iphone': ['i phone', 'i-phone', 'iphone pro', 'iphone max'],
            'macbook': ['mac book', 'macbook pro', 'macbook air'],
            'playstation': ['play station', 'ps5', 'ps4', 'playstation 5'],
            'nintendo switch': ['switch', 'nintendo'],
            'airfryer': ['air fryer', 'air-fryer', 'airfryer'],
            'steam deck': ['steamdeck', 'steam-deck'],
        }
        
        # Build reverse lookup
        self.variant_to_canonical = {}
        for canonical, variants in self.known_variants.items():
            for variant in variants:
                self.variant_to_canonical[variant.lower()] = canonical
        
        logger.info("Entity normalizer initialized")
    
    def remove_accents(self, text: str) -> str:
        """Remove accents from text"""
        nfd = unicodedata.normalize('NFD', text)
        return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace"""
        return re.sub(r'\s+', ' ', text).strip()
    
    def remove_special_chars(self, text: str, keep_chars: str = '-') -> str:
        """
        Remove special characters except specified ones
        """
        # Keep alphanumeric, spaces, and specified chars
        pattern = f'[^a-zA-Z0-9\\s{re.escape(keep_chars)}]'
        return re.sub(pattern, '', text)
    
    def normalize_case(self, text: str) -> str:
        """
        Normalize case intelligently
        Lowercase unless it's an acronym (all caps)
        """
        words = text.split()
        normalized_words = []
        
        for word in words:
            if word.isupper() and len(word) > 1:
                # Keep acronyms (e.g., "USB", "LED")
                normalized_words.append(word)
            else:
                normalized_words.append(word.lower())
        
        return ' '.join(normalized_words)
    
    def expand_substitutions(self, text: str) -> str:
        """Expand common substitutions"""
        for symbol, word in self.substitutions.items():
            text = text.replace(symbol, f' {word} ')
        return self.normalize_whitespace(text)
    
    def normalize_basic(self, text: str) -> str:
        """
        Basic normalization pipeline
        - Lowercase
        - Remove accents
        - Remove special chars
        - Normalize whitespace
        """
        # Remove accents
        text = self.remove_accents(text)
        
        # Expand substitutions
        text = self.expand_substitutions(text)
        
        # Remove special characters
        text = self.remove_special_chars(text, keep_chars='-')
        
        # Normalize case
        text = self.normalize_case(text)
        
        # Normalize whitespace
        text = self.normalize_whitespace(text)
        
        return text
    
    def get_canonical_form(self, entity: str) -> str:
        """
        Get canonical form of entity
        Checks known variants first, then applies normalization
        """
        # Normalize first
        normalized = self.normalize_basic(entity)
        
        # Check if it's a known variant
        if normalized in self.variant_to_canonical:
            return self.variant_to_canonical[normalized]
        
        # Check if any known canonical is a substring
        for canonical, variants in self.known_variants.items():
            if canonical in normalized or normalized in canonical:
                return canonical
        
        # Return normalized version as canonical
        return normalized
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings
        Uses simple character-based similarity
        """
        str1 = str1.lower()
        str2 = str2.lower()
        
        # Exact match
        if str1 == str2:
            return 1.0
        
        # One contains the other
        if str1 in str2 or str2 in str1:
            return 0.8
        
        # Character overlap
        set1 = set(str1)
        set2 = set(str2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def group_variants(self, entities: List[str], similarity_threshold: float = 0.7) -> Dict[str, List[str]]:
        """
        Group entity variants into canonical forms
        
        Returns:
            Dict mapping canonical form to list of variants
        """
        groups = defaultdict(list)
        processed = set()
        
        # Sort by length (longer = more likely to be canonical)
        entities_sorted = sorted(entities, key=len, reverse=True)
        
        for entity in entities_sorted:
            if entity in processed:
                continue
            
            # Get canonical form
            canonical = self.get_canonical_form(entity)
            
            # Find similar entities
            variants = [entity]
            for other_entity in entities_sorted:
                if other_entity == entity or other_entity in processed:
                    continue
                
                similarity = self.calculate_similarity(canonical, other_entity)
                if similarity >= similarity_threshold:
                    variants.append(other_entity)
                    processed.add(other_entity)
            
            groups[canonical] = variants
            processed.add(entity)
        
        return dict(groups)
    
    def normalize_entity_list(self, entities: Dict[str, int]) -> List[Dict]:
        """
        Normalize a list of entities with frequencies
        
        Args:
            entities: Dict of entity: frequency
        
        Returns:
            List of dicts with canonical_term, variants, total_mentions
        """
        # Group variants
        groups = self.group_variants(list(entities.keys()))
        
        # Calculate combined frequencies
        normalized_entities = []
        
        for canonical, variants in groups.items():
            total_mentions = sum(entities.get(variant, 0) for variant in variants)
            
            normalized_entities.append({
                'canonical_term': canonical,
                'variants': variants,
                'variants_json': json.dumps(variants),
                'total_mentions': total_mentions
            })
        
        # Sort by total mentions
        normalized_entities.sort(key=lambda x: x['total_mentions'], reverse=True)
        
        return normalized_entities
    
    def add_custom_variant(self, canonical: str, variant: str):
        """Add a custom variant mapping"""
        canonical_lower = canonical.lower()
        variant_lower = variant.lower()
        
        if canonical_lower not in self.known_variants:
            self.known_variants[canonical_lower] = []
        
        if variant_lower not in self.known_variants[canonical_lower]:
            self.known_variants[canonical_lower].append(variant_lower)
            self.variant_to_canonical[variant_lower] = canonical_lower
        
        logger.info(f"Added variant mapping: {variant} -> {canonical}")


def main():
    """Test the entity normalizer"""
    print("Testing Entity Normalizer...")
    
    normalizer = EntityNormalizer()
    
    # Test basic normalization
    print("\n" + "="*60)
    print("Testing basic normalization...")
    
    test_strings = [
        "AirPods Pro",
        "air pods pro",
        "Air-Pods",
        "iPhone 15 Pro Max",
        "I Phone 15",
        "Play Station 5",
        "PS5",
        "Air Fryer",
        "Air-Fryer",
        "USB-C Cable",
        "MacBook Pro"
    ]
    
    for text in test_strings:
        normalized = normalizer.normalize_basic(text)
        canonical = normalizer.get_canonical_form(text)
        print(f"{text:<25} -> Normalized: {normalized:<20} -> Canonical: {canonical}")
    
    # Test variant grouping
    print("\n" + "="*60)
    print("Testing variant grouping...")
    
    entities_with_freq = {
        'AirPods Pro': 15,
        'airpods pro': 10,
        'Air Pods': 5,
        'iPhone 15': 20,
        'iphone 15': 12,
        'i-phone 15': 3,
        'PlayStation 5': 18,
        'PS5': 25,
        'play station 5': 7,
        'Air Fryer': 30,
        'air-fryer': 15,
        'airfryer': 8
    }
    
    normalized_list = normalizer.normalize_entity_list(entities_with_freq)
    
    print("\n📊 Normalized Entities:")
    print(f"{'Canonical':<20} {'Total Mentions':<15} {'Variants'}")
    print("-" * 70)
    for item in normalized_list[:10]:
        variants_str = ', '.join(item['variants'][:3])
        if len(item['variants']) > 3:
            variants_str += f"... (+{len(item['variants'])-3} more)"
        print(f"{item['canonical_term']:<20} {item['total_mentions']:<15} {variants_str}")
    
    # Test similarity calculation
    print("\n" + "="*60)
    print("Testing similarity calculation...")
    
    pairs = [
        ('airpods', 'airpod'),
        ('iphone', 'i-phone'),
        ('playstation', 'ps5'),
        ('macbook', 'laptop')
    ]
    
    for str1, str2 in pairs:
        similarity = normalizer.calculate_similarity(str1, str2)
        print(f"Similarity '{str1}' vs '{str2}': {similarity:.2f}")
    
    print("\n✅ Entity normalizer test completed!")


if __name__ == "__main__":
    main()
