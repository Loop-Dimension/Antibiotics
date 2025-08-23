import re
from typing import List, Dict, Optional, Tuple
from patients.models import AntibioticDosing


class AntibioticMatcher:
    """
    Service for matching current antibiotic strings with database entries
    """
    
    # Common antibiotic name variations and synonyms
    ANTIBIOTIC_SYNONYMS = {
        'amoxicillin/clavulanate': ['augmentin', 'amox/clav', 'amoxiclav', 'co-amoxiclav'],
        'ampicillin/sulbactam': ['unasyn', 'amp/sulb'],
        'piperacillin/tazobactam': ['zosyn', 'pip/tazo', 'tazocin'],
        'trimethoprim/sulfamethoxazole': ['bactrim', 'septra', 'tmp/smx', 'co-trimoxazole'],
        'ciprofloxacin': ['cipro'],
        'levofloxacin': ['levaquin'],
        'moxifloxacin': ['avelox'],
        'ceftriaxone': ['rocephin'],
        'cefepime': ['maxipime'],
        'vancomycin': ['vanco'],
        'linezolid': ['zyvox'],
        'clindamycin': ['cleocin'],
        'doxycycline': ['vibramycin'],
        'azithromycin': ['zithromax', 'z-pack'],
        'cephalexin': ['keflex'],
        'nitrofurantoin': ['macrobid', 'macrodantin']
    }
    
    @staticmethod
    def parse_current_antibiotic(antibiotic_string: str) -> Dict:
        """
        Parse a current antibiotic string like "PO amoxicillin/clavulanate 1g bid"
        into components
        """
        if not antibiotic_string:
            return {}
        
        # Clean up the string
        cleaned = antibiotic_string.strip().lower()
        
        # Extract route (PO, IV, IM, etc.)
        route_match = re.match(r'(po|iv|im|sc|top)\s+', cleaned)
        route = route_match.group(1).upper() if route_match else None
        
        # Remove route from string for further processing
        if route_match:
            cleaned = cleaned[route_match.end():]
        
        # Extract frequency (bid, tid, q8h, q24h, etc.)
        frequency_patterns = [
            r'\b(bid|b\.i\.d\.?)\b',
            r'\b(tid|t\.i\.d\.?)\b', 
            r'\b(qid|q\.i\.d\.?)\b',
            r'\b(q\d+h?)\b',
            r'\b(daily|once daily|qd)\b',
            r'\b(twice daily)\b',
            r'\b(three times daily)\b',
            r'\b(four times daily)\b'
        ]
        
        frequency = None
        for pattern in frequency_patterns:
            freq_match = re.search(pattern, cleaned)
            if freq_match:
                frequency = freq_match.group(1)
                cleaned = re.sub(pattern, '', cleaned).strip()
                break
        
        # Extract dose (1g, 500mg, etc.)
        dose_patterns = [
            r'\b(\d+(?:\.\d+)?)\s*(g|mg|mcg|ug)\b',
            r'\b(\d+(?:\.\d+)?)\s*(gram|grams|milligram|milligrams)\b'
        ]
        
        dose = None
        dose_unit = None
        for pattern in dose_patterns:
            dose_match = re.search(pattern, cleaned)
            if dose_match:
                dose = dose_match.group(1)
                dose_unit = dose_match.group(2)
                cleaned = re.sub(pattern, '', cleaned).strip()
                break
        
        # What's left should be the antibiotic name
        antibiotic_name = cleaned.strip()
        
        return {
            'name': antibiotic_name,
            'route': route,
            'dose': dose,
            'dose_unit': dose_unit,
            'frequency': frequency,
            'original': antibiotic_string
        }
    
    @staticmethod
    def normalize_antibiotic_name(name: str) -> str:
        """
        Normalize antibiotic name for comparison
        """
        if not name:
            return ""
        
        # Convert to lowercase and strip
        normalized = name.lower().strip()
        
        # Remove common prefixes/suffixes
        normalized = re.sub(r'\b(tabs?|capsules?|injection|solution)\b', '', normalized)
        
        # Normalize spacing around slashes and hyphens
        normalized = re.sub(r'\s*[/\-]\s*', '/', normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    @staticmethod
    def find_matching_antibiotics(current_antibiotic: str, patient_crcl: float = None) -> List[Dict]:
        """
        Find database antibiotics that match the current antibiotic
        """
        if not current_antibiotic:
            return []

        # Parse the current antibiotic
        parsed = AntibioticMatcher.parse_current_antibiotic(current_antibiotic)
        current_name = AntibioticMatcher.normalize_antibiotic_name(parsed.get('name', ''))
        
        if not current_name:
            return []
        
        matches = []
        
        # Get all antibiotics from database
        db_antibiotics = AntibioticDosing.objects.all()
        
        for db_ab in db_antibiotics:
            db_name = AntibioticMatcher.normalize_antibiotic_name(db_ab.antibiotic)
            
            # Calculate match score
            score = AntibioticMatcher._calculate_match_score(current_name, db_name, parsed)
            
            if score > 0:
                # Add clinical appropriateness bonus if patient CrCl is provided
                clinical_bonus = 0
                if patient_crcl is not None:
                    # Import here to avoid circular imports
                    from .antibiotic_service import AntibioticRecommendationService
                    
                    is_crcl_appropriate = AntibioticRecommendationService._is_crcl_compatible(
                        db_ab.crcl_range, patient_crcl
                    )
                    if is_crcl_appropriate:
                        clinical_bonus = 50  # Big bonus for clinically appropriate matches
                
                final_score = score + clinical_bonus
                
                matches.append({
                    'antibiotic': db_ab,
                    'score': final_score,
                    'base_score': score,
                    'clinical_bonus': clinical_bonus,
                    'match_type': AntibioticMatcher._get_match_type(final_score),
                    'parsed_current': parsed,
                    'db_name_normalized': db_name
                })
        
        # Sort by final score (highest first)
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches
    
    @staticmethod
    def _calculate_match_score(current_name: str, db_name: str, parsed_current: Dict) -> float:
        """
        Calculate match score between current and database antibiotic names
        """
        score = 0.0
        
        # Exact match
        if current_name == db_name:
            return 100.0
        
        # Check if current name is contained in db name or vice versa
        if current_name in db_name:
            score += 80.0
        elif db_name in current_name:
            score += 75.0
        
        # Check for synonym matches
        for standard_name, synonyms in AntibioticMatcher.ANTIBIOTIC_SYNONYMS.items():
            if AntibioticMatcher.normalize_antibiotic_name(standard_name) == current_name:
                if any(synonym in db_name for synonym in synonyms):
                    score += 90.0
                    break
            elif current_name in synonyms:
                if AntibioticMatcher.normalize_antibiotic_name(standard_name) == db_name:
                    score += 90.0
                    break
        
        # Word-by-word matching for combination drugs
        current_words = set(current_name.split())
        db_words = set(db_name.split())
        
        if current_words and db_words:
            common_words = current_words.intersection(db_words)
            word_match_ratio = len(common_words) / max(len(current_words), len(db_words))
            score += word_match_ratio * 60.0
        
        # Fuzzy matching for similar drug names
        if score == 0:
            score += AntibioticMatcher._fuzzy_match_score(current_name, db_name)
        
        return score
    
    @staticmethod
    def _fuzzy_match_score(name1: str, name2: str) -> float:
        """
        Simple fuzzy matching based on character overlap
        """
        if not name1 or not name2:
            return 0.0
        
        # Simple character-based similarity
        set1 = set(name1.replace(' ', ''))
        set2 = set(name2.replace(' ', ''))
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        similarity = intersection / union if union > 0 else 0.0
        
        # Only consider it a match if similarity is reasonably high
        return similarity * 30.0 if similarity > 0.6 else 0.0
    
    @staticmethod
    def _get_match_type(score: float) -> str:
        """
        Classify the type of match based on score
        """
        if score >= 90:
            return "exact"
        elif score >= 70:
            return "strong"
        elif score >= 50:
            return "moderate"
        elif score >= 30:
            return "weak"
        else:
            return "none"
    
    @staticmethod
    def get_best_match(current_antibiotic: str, patient_crcl: float = None) -> Optional[Dict]:
        """
        Get the best matching antibiotic from the database
        """
        matches = AntibioticMatcher.find_matching_antibiotics(current_antibiotic, patient_crcl)
        return matches[0] if matches else None
    
    @staticmethod
    def explain_current_antibiotic(current_antibiotic: str, patient_crcl: float = None) -> Dict:
        """
        Provide detailed explanation of current antibiotic and its database matches
        """
        if not current_antibiotic:
            return {
                'error': 'No current antibiotic provided',
                'parsed': {},
                'matches': [],
                'best_match': None
            }
        
        # Parse current antibiotic
        parsed = AntibioticMatcher.parse_current_antibiotic(current_antibiotic)
        
        # Find matches with clinical consideration
        matches = AntibioticMatcher.find_matching_antibiotics(current_antibiotic, patient_crcl)
        
        # Get best match
        best_match = matches[0] if matches else None
        
        return {
            'original': current_antibiotic,
            'parsed': parsed,
            'matches': matches[:5],  # Top 5 matches
            'best_match': best_match,
            'total_matches': len(matches)
        }
