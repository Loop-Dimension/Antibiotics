from typing import Dict, List, Set
import re


class DrugClassifier:
    """
    Classifies antibiotics into their respective drug classes
    """
    
    DRUG_CLASSES = {
        'fluoroquinolones': {
            'names': ['ciprofloxacin', 'levofloxacin', 'moxifloxacin', 'gemifloxacin', 'ofloxacin', 'norfloxacin'],
            'mechanism': 'DNA gyrase inhibitors',
            'spectrum': 'Broad-spectrum',
            'common_uses': ['UTI', 'pneumonia', 'gastroenteritis', 'skin infections']
        },
        'penicillins': {
            'names': ['penicillin', 'amoxicillin', 'ampicillin', 'piperacillin', 'nafcillin'],
            'mechanism': 'Beta-lactam cell wall synthesis inhibitors',
            'spectrum': 'Variable (narrow to broad)',
            'common_uses': ['strep infections', 'pneumonia', 'skin infections']
        },
        'beta_lactam_combinations': {
            'names': ['amoxicillin/clavulanate', 'ampicillin/sulbactam', 'piperacillin/tazobactam'],
            'mechanism': 'Beta-lactam + beta-lactamase inhibitor',
            'spectrum': 'Extended spectrum',
            'common_uses': ['polymicrobial infections', 'healthcare-associated infections']
        },
        'cephalosporins': {
            'names': ['cephalexin', 'cefazolin', 'ceftriaxone', 'cefepime', 'ceftaroline', 'cefpodoxime', 'cefotaxime', 'ceftolozane'],
            'mechanism': 'Beta-lactam cell wall synthesis inhibitors',
            'spectrum': 'Variable by generation',
            'common_uses': ['pneumonia', 'UTI', 'skin infections', 'meningitis']
        },
        'carbapenems': {
            'names': ['imipenem', 'meropenem', 'ertapenem', 'doripenem'],
            'mechanism': 'Beta-lactam cell wall synthesis inhibitors',
            'spectrum': 'Ultra-broad spectrum',
            'common_uses': ['severe infections', 'multidrug-resistant organisms']
        },
        'macrolides': {
            'names': ['azithromycin', 'clarithromycin', 'erythromycin'],
            'mechanism': 'Protein synthesis inhibitors (50S ribosome)',
            'spectrum': 'Atypical pathogens and gram-positive',
            'common_uses': ['atypical pneumonia', 'upper respiratory infections']
        },
        'glycopeptides': {
            'names': ['vancomycin', 'teicoplanin'],
            'mechanism': 'Cell wall synthesis inhibitors (different from beta-lactams)',
            'spectrum': 'Gram-positive',
            'common_uses': ['MRSA infections', 'C. difficile colitis (oral vanco)']
        },
        'oxazolidinones': {
            'names': ['linezolid', 'tedizolid'],
            'mechanism': 'Protein synthesis inhibitors (unique mechanism)',
            'spectrum': 'Gram-positive including VRE and MRSA',
            'common_uses': ['resistant gram-positive infections']
        },
        'lincosamides': {
            'names': ['clindamycin'],
            'mechanism': 'Protein synthesis inhibitors (50S ribosome)',
            'spectrum': 'Anaerobes and gram-positive',
            'common_uses': ['skin infections', 'anaerobic infections']
        },
        'tetracyclines': {
            'names': ['doxycycline', 'minocycline', 'tetracycline'],
            'mechanism': 'Protein synthesis inhibitors (30S ribosome)',
            'spectrum': 'Broad including atypicals',
            'common_uses': ['atypical infections', 'tick-borne diseases', 'acne']
        },
        'sulfonamides': {
            'names': ['trimethoprim/sulfamethoxazole', 'sulfamethoxazole'],
            'mechanism': 'Folate synthesis inhibitors',
            'spectrum': 'Broad spectrum',
            'common_uses': ['UTI', 'PCP prophylaxis', 'MRSA (skin)']
        },
        'nitroimidazoles': {
            'names': ['metronidazole', 'tinidazole'],
            'mechanism': 'DNA damage',
            'spectrum': 'Anaerobes and certain parasites',
            'common_uses': ['anaerobic infections', 'C. difficile', 'H. pylori']
        },
        'nitrofurans': {
            'names': ['nitrofurantoin'],
            'mechanism': 'Multiple mechanisms',
            'spectrum': 'Urinary pathogens',
            'common_uses': ['uncomplicated UTI']
        }
    }
    
    @classmethod
    def classify_antibiotic(cls, antibiotic_name: str) -> Dict:
        """
        Classify an antibiotic by its drug class
        """
        if not antibiotic_name:
            return {'class': 'unknown', 'details': None}
        
        name_lower = antibiotic_name.lower().strip()
        
        # Remove dosing information for classification
        name_clean = re.sub(r'\d+(\.\d+)?\s*(mg|g|mcg)', '', name_lower)
        name_clean = re.sub(r'\s+', ' ', name_clean).strip()
        
        for drug_class, details in cls.DRUG_CLASSES.items():
            for drug_name in details['names']:
                if drug_name.lower() in name_clean:
                    return {
                        'class': drug_class,
                        'details': details,
                        'drug_name': drug_name,
                        'mechanism': details['mechanism'],
                        'spectrum': details['spectrum']
                    }
        
        return {'class': 'unknown', 'details': None}
    
    @classmethod
    def are_same_class(cls, antibiotic1: str, antibiotic2: str) -> bool:
        """
        Check if two antibiotics are from the same drug class
        """
        class1 = cls.classify_antibiotic(antibiotic1)
        class2 = cls.classify_antibiotic(antibiotic2)
        
        return (class1['class'] != 'unknown' and 
                class2['class'] != 'unknown' and 
                class1['class'] == class2['class'])
    
    @classmethod
    def get_different_classes(cls, current_antibiotic: str, available_antibiotics: List[str]) -> List[Dict]:
        """
        Get antibiotics from different classes than the current one
        """
        current_class = cls.classify_antibiotic(current_antibiotic)['class']
        
        different_class_antibiotics = []
        
        for antibiotic in available_antibiotics:
            antibiotic_class = cls.classify_antibiotic(antibiotic)
            if antibiotic_class['class'] != current_class and antibiotic_class['class'] != 'unknown':
                different_class_antibiotics.append({
                    'antibiotic': antibiotic,
                    'class': antibiotic_class['class'],
                    'details': antibiotic_class
                })
        
        return different_class_antibiotics
    
    @classmethod
    def should_avoid_same_class(cls, current_antibiotic: str, recommendation: str, clinical_context: Dict = None) -> Dict:
        """
        Determine if recommending the same antibiotic class should be avoided
        """
        if cls.are_same_class(current_antibiotic, recommendation):
            current_class = cls.classify_antibiotic(current_antibiotic)
            
            # Default recommendation is to avoid same class
            avoid_reason = f"Patient already on {current_class['class']} - consider alternative class"
            avoid = True
            
            # Clinical scenarios where same class might be acceptable
            if clinical_context:
                # If current drug is ineffective or has resistance
                if clinical_context.get('treatment_failure', False):
                    avoid = False
                    avoid_reason = "Treatment failure - same class with different pharmacokinetics may be appropriate"
                
                # If stepping up/down within class (e.g., oral to IV)
                current_route = clinical_context.get('current_route', '').upper()
                rec_route = clinical_context.get('recommendation_route', '').upper()
                if current_route == 'PO' and rec_route == 'IV':
                    avoid = False
                    avoid_reason = "Route optimization (oral to IV) within same class"
                elif current_route == 'IV' and rec_route == 'PO':
                    avoid = False
                    avoid_reason = "De-escalation to oral therapy within same class"
            
            return {
                'avoid': avoid,
                'reason': avoid_reason,
                'current_class': current_class['class'],
                'recommendation_class': cls.classify_antibiotic(recommendation)['class']
            }
        
        return {'avoid': False, 'reason': 'Different antibiotic classes', 'current_class': None, 'recommendation_class': None}
    
    @classmethod
    def get_class_diversity_score(cls, antibiotics: List[str]) -> Dict:
        """
        Calculate diversity score for a list of antibiotics based on class representation
        """
        classes = set()
        classified_antibiotics = []
        
        for antibiotic in antibiotics:
            classification = cls.classify_antibiotic(antibiotic)
            if classification['class'] != 'unknown':
                classes.add(classification['class'])
                classified_antibiotics.append({
                    'antibiotic': antibiotic,
                    'class': classification['class']
                })
        
        diversity_score = len(classes) / len(antibiotics) if antibiotics else 0
        
        return {
            'diversity_score': diversity_score,
            'unique_classes': len(classes),
            'total_antibiotics': len(antibiotics),
            'classes_represented': list(classes),
            'classified_antibiotics': classified_antibiotics
        }
