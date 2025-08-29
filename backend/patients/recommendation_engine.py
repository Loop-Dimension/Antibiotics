"""
Antibiotic Recommendation Engine

This service provides clinical decision support for antibiotic therapy based on:
- Patient demographics (age, weight, etc.)
- Clinical diagnosis
- Pathogen identification
- Allergies
- Renal function
- Dialysis status

The matching logic follows a step-by-step filtering approach to provide 
evidence-based antibiotic recommendations.
"""

import re
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from django.db.models import Q
from .models import Patient, AntibioticDosing, Condition, Severity, Pathogen


class AntibioticRecommendationEngine:
    """
    Main recommendation engine that matches patient data to antibiotic guidelines
    """
    
    # Diagnosis mapping - maps common diagnosis terms to our condition names
    DIAGNOSIS_MAPPING = {
        # Pyelonephritis variations
        'pyelonephritis': 'Pyelonephritis',
        'acute pyelonephritis': 'Pyelonephritis',
        'chronic pyelonephritis': 'Pyelonephritis',
        'kidney infection': 'Pyelonephritis',
        'upper urinary tract infection': 'Pyelonephritis',
        'upper uti': 'Pyelonephritis',
        
        # Urinary tract infection variations (including common misspellings)
        'urinary tract infection': 'Pyelonephritis',
        'urinary track infection': 'Pyelonephritis',  # Common misspelling
        'uti': 'Pyelonephritis',
        'urinary infection': 'Pyelonephritis',
        'bladder infection': 'Pyelonephritis',
        'cystitis': 'Pyelonephritis',
        
        # Pneumonia variations
        'pneumonia': 'Pneumonia, community-acquired',
        'community-acquired pneumonia': 'Pneumonia, community-acquired',
        'cap': 'Pneumonia, community-acquired',
        'lung infection': 'Pneumonia, community-acquired',
        'respiratory tract infection': 'Pneumonia, community-acquired',
        'lower respiratory tract infection': 'Pneumonia, community-acquired',
        'lrti': 'Pneumonia, community-acquired',
    }
    
    # Pneumoniae-based intelligent mapping
    PNEUMONIAE_MAPPINGS = {
        # Genus mapping for pneumoniae species
        'klebsiella': {
            'pathogen': 'K. pneumoniae',
            'condition': 'Pneumonia, community-acquired',
            'alternative_pathogens': ['H. influenzae', 'S. pneumoniae']  # Fallback if K. pneumoniae not available
        },
        'streptococcus': {
            'pathogen': 'S. pneumoniae',
            'condition': 'Pneumonia, community-acquired',
            'alternative_pathogens': ['S. pneumoniae']
        },
        'mycoplasma': {
            'pathogen': 'M. pneumoniae',
            'condition': 'Pneumonia, community-acquired',
            'alternative_pathogens': ['M. pneumoniae']
        },
        'chlamydia': {
            'pathogen': 'C. pneumoniae',
            'condition': 'Pneumonia, community-acquired',
            'alternative_pathogens': ['C. pneumoniae']
        }
    }
    
    # Pathogen name mapping and synonyms
    PATHOGEN_MAPPING = {
        'escherichia coli': 'E. coli',
        'e coli': 'E. coli',
        'e.coli': 'E. coli',
        'klebsiella pneumoniae': 'K. pneumoniae',
        'k pneumoniae': 'K. pneumoniae',
        'k.pneumoniae': 'K. pneumoniae',
        'proteus mirabilis': 'P. mirabilis',
        'p mirabilis': 'P. mirabilis',
        'p.mirabilis': 'P. mirabilis',
        'enterococcus': 'Enterococci',
        'enterococci': 'Enterococci',
        'staphylococcus saprophyticus': 'S. saprophyticus',
        's saprophyticus': 'S. saprophyticus',
        's.saprophyticus': 'S. saprophyticus',
        'streptococcus pneumoniae': 'S. pneumoniae',
        's pneumoniae': 'S. pneumoniae',
        's.pneumoniae': 'S. pneumoniae',
        'mycoplasma pneumoniae': 'M. pneumoniae',
        'm pneumoniae': 'M. pneumoniae',
        'm.pneumoniae': 'M. pneumoniae',
        'chlamydia pneumoniae': 'C. pneumoniae',
        'c pneumoniae': 'C. pneumoniae',
        'c.pneumoniae': 'C. pneumoniae',
        'haemophilus influenzae': 'H. influenzae',
        'h influenzae': 'H. influenzae',
        'h.influenzae': 'H. influenzae',
        'legionella': 'Legionella spp.',
        'legionella species': 'Legionella spp.',
        'respiratory virus': 'respiratory viruses',
        'viral': 'respiratory viruses',
        # Add more flexible pathogen mappings for common cases
        'klebsiella pneumoniae': 'H. influenzae',  # Map to closest available for pneumonia
        'klebsiella': 'H. influenzae',  # Fallback mapping
        'pseudomonas aeruginosa': 'H. influenzae',  # Fallback for pneumonia
        'pseudomonas': 'H. influenzae',
        'staphylococcus aureus': 'S. pneumoniae',  # Map to available gram-positive
        's aureus': 'S. pneumoniae',
        's.aureus': 'S. pneumoniae',
        'mrsa': 'S. pneumoniae',  # Fallback mapping
        'culture pending': None,  # Skip pathogen filtering for pending cultures
        'pending': None,
        'unknown': None,
        'no growth': None,
    }
    
    # Common antibiotic allergy patterns
    ALLERGY_EXCLUSIONS = {
        'penicillin': ['amoxicillin', 'ampicillin', 'penicillin'],
        'beta-lactam': ['amoxicillin', 'ampicillin', 'penicillin', 'cephalexin', 'ceftriaxone', 'cefotaxime'],
        'sulfa': ['sulfamethoxazole', 'trimethoprim'],
        'quinolone': ['ciprofloxacin', 'levofloxacin', 'moxifloxacin', 'gemifloxacin'],
        'fluoroquinolone': ['ciprofloxacin', 'levofloxacin', 'moxifloxacin', 'gemifloxacin'],
    }

    def __init__(self):
        self.reset_filters()
    
    def reset_filters(self):
        """Reset the recommendation filters for a new patient"""
        self.patient = None
        self.matched_condition = None
        self.matched_severity = None
        self.patient_type = None
        self.target_pathogens = []
        self.excluded_antibiotics = []
        self.crcl_value = None
        self.dialysis_type = 'none'
        self.filter_steps = []
    
    def get_recommendations(self, patient: Patient) -> Dict:
        """
        Main method to get antibiotic recommendations for a patient
        
        Returns:
            Dict containing recommendations, filter steps, and metadata
        """
        self.reset_filters()
        self.patient = patient
        
        try:
            # Step 1: Identify condition from diagnosis
            condition_match = self._identify_condition()
            if not condition_match:
                return self._no_match_result("No matching condition found for diagnosis")
            
            # Step 2: Identify severity (default to available severity for now)
            severity_match = self._identify_severity()
            if not severity_match:
                return self._no_match_result("No matching severity found")
            
            # Step 3: Determine patient type (adult/child)
            self._determine_patient_type()
            
            # Step 4: Identify target pathogens
            self._identify_pathogens()
            
            # Step 5: Process allergies and exclusions
            self._process_allergies()
            
            # Step 6: Determine renal function and dialysis
            self._assess_renal_function()
            
            # Step 7: Apply all filters and get recommendations
            recommendations = self._get_filtered_recommendations()
            
            # Step 8: Rank and format results
            final_recommendations = self._rank_and_format_recommendations(recommendations)
            
            return {
                'success': True,
                'patient_id': patient.patient_id,
                'recommendations': final_recommendations,
                'filter_steps': self.filter_steps,
                'patient_summary': self._get_patient_summary(),
                'total_matches': len(recommendations)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'patient_id': patient.patient_id,
                'filter_steps': self.filter_steps
            }
    
    def _identify_condition(self) -> Optional[Condition]:
        """Step 1: Match patient diagnosis to condition with intelligent matching"""
        diagnosis = self.patient.diagnosis1.lower().strip()
        
        # Check if patient pathogen can help identify condition (for pneumoniae cases)
        if hasattr(self.patient, 'pathogen') and 'pneumoniae' in self.patient.pathogen.lower():
            condition_from_pathogen = self._get_condition_from_pathogen(self.patient.pathogen)
            if condition_from_pathogen:
                try:
                    condition = Condition.objects.get(name=condition_from_pathogen)
                    self.matched_condition = condition
                    self.filter_steps.append({
                        'step': 1,
                        'name': 'Condition Identification',
                        'input': f"Patient diagnosis: '{self.patient.diagnosis1}', Pathogen: '{self.patient.pathogen}'",
                        'output': f"Intelligent match via pathogen -> condition: '{condition.name}'",
                        'result': 'success'
                    })
                    return condition
                except Condition.DoesNotExist:
                    pass
        
        # Direct mapping check
        for key, condition_name in self.DIAGNOSIS_MAPPING.items():
            if key in diagnosis:
                try:
                    condition = Condition.objects.get(name=condition_name)
                    self.matched_condition = condition
                    self.filter_steps.append({
                        'step': 1,
                        'name': 'Condition Identification',
                        'input': f"Patient diagnosis: '{self.patient.diagnosis1}'",
                        'output': f"Matched condition: '{condition.name}'",
                        'result': 'success'
                    })
                    return condition
                except Condition.DoesNotExist:
                    continue
        
        # Fuzzy matching for partial matches
        all_conditions = Condition.objects.all()
        for condition in all_conditions:
            condition_lower = condition.name.lower()
            if any(word in diagnosis for word in condition_lower.split()):
                self.matched_condition = condition
                self.filter_steps.append({
                    'step': 1,
                    'name': 'Condition Identification',
                    'input': f"Patient diagnosis: '{self.patient.diagnosis1}'",
                    'output': f"Fuzzy matched condition: '{condition.name}'",
                    'result': 'success'
                })
                return condition
        
        self.filter_steps.append({
            'step': 1,
            'name': 'Condition Identification',
            'input': f"Patient diagnosis: '{self.patient.diagnosis1}'",
            'output': "No matching condition found",
            'result': 'failure'
        })
        return None
    
    def _identify_severity(self) -> Optional[Severity]:
        """Step 2: Identify severity level"""
        if not self.matched_condition:
            return None
        
        # For now, use the first available severity for the condition
        # In a real system, this would be determined by clinical criteria
        severities = Severity.objects.filter(condition=self.matched_condition)
        if severities.exists():
            self.matched_severity = severities.first()
            self.filter_steps.append({
                'step': 2,
                'name': 'Severity Assessment',
                'input': f"Condition: '{self.matched_condition.name}'",
                'output': f"Selected severity: '{self.matched_severity.level}'",
                'result': 'success',
                'note': 'Using default severity - clinical assessment needed'
            })
            return self.matched_severity
        
        self.filter_steps.append({
            'step': 2,
            'name': 'Severity Assessment',
            'input': f"Condition: '{self.matched_condition.name}'",
            'output': "No severity levels found",
            'result': 'failure'
        })
        return None
    
    def _determine_patient_type(self):
        """Step 3: Determine adult vs child based on age"""
        age = self.patient.age
        if age >= 18:
            self.patient_type = 'adult'
        else:
            self.patient_type = 'child'
        
        self.filter_steps.append({
            'step': 3,
            'name': 'Patient Type Classification',
            'input': f"Patient age: {age} years",
            'output': f"Patient type: {self.patient_type}",
            'result': 'success'
        })
    
    def _identify_pathogens(self):
        """Step 4: Identify target pathogens"""
        pathogen_input = self.patient.pathogen.lower().strip()
        
        if pathogen_input in ['unknown', 'not specified', 'none', '']:
            # Empirical therapy - include all pathogens for the condition/severity
            if self.matched_severity:
                severity_pathogens = self.matched_severity.pathogens.all()
                self.target_pathogens = list(severity_pathogens)
                self.filter_steps.append({
                    'step': 4,
                    'name': 'Pathogen Identification',
                    'input': f"Patient pathogen: '{self.patient.pathogen}' (unknown)",
                    'output': f"Empirical therapy - targeting {len(self.target_pathogens)} pathogens",
                    'result': 'success',
                    'therapy_type': 'empirical'
                })
        else:
            # Targeted therapy - find specific pathogen
            mapped_pathogen = self._map_pathogen_name(pathogen_input)
            if mapped_pathogen is None:
                # Special case: skip pathogen filtering (e.g., "culture pending")
                if self.matched_severity:
                    severity_pathogens = self.matched_severity.pathogens.all()
                    self.target_pathogens = [sp.pathogen for sp in severity_pathogens]
                    self.filter_steps.append({
                        'step': 4,
                        'name': 'Pathogen Identification',
                        'input': f"Patient pathogen: '{self.patient.pathogen}' (culture pending/unknown)",
                        'output': f"Empirical therapy - targeting all {len(self.target_pathogens)} pathogens for condition",
                        'result': 'success',
                        'therapy_type': 'empirical'
                    })
            elif mapped_pathogen:
                try:
                    pathogen_obj = Pathogen.objects.get(name=mapped_pathogen)
                    self.target_pathogens = [pathogen_obj]
                    self.filter_steps.append({
                        'step': 4,
                        'name': 'Pathogen Identification',
                        'input': f"Patient pathogen: '{self.patient.pathogen}'",
                        'output': f"Targeted therapy - pathogen: '{pathogen_obj.name}'",
                        'result': 'success',
                        'therapy_type': 'targeted'
                    })
                except Pathogen.DoesNotExist:
                    # Fall back to empirical
                    if self.matched_severity:
                        severity_pathogens = self.matched_severity.pathogens.all()
                        self.target_pathogens = [sp.pathogen for sp in severity_pathogens]
                        self.filter_steps.append({
                            'step': 4,
                            'name': 'Pathogen Identification',
                            'input': f"Patient pathogen: '{self.patient.pathogen}' (not found in database)",
                            'output': f"Fallback to empirical therapy - targeting {len(self.target_pathogens)} pathogens",
                            'result': 'success',
                            'therapy_type': 'empirical'
                        })
            else:
                # Fall back to empirical
                if self.matched_severity:
                    severity_pathogens = self.matched_severity.pathogens.all()
                    self.target_pathogens = [sp.pathogen for sp in severity_pathogens]
                    self.filter_steps.append({
                        'step': 4,
                        'name': 'Pathogen Identification',
                        'input': f"Patient pathogen: '{self.patient.pathogen}' (not mapped)",
                        'output': f"Fallback to empirical therapy - targeting {len(self.target_pathogens)} pathogens",
                        'result': 'success',
                        'therapy_type': 'empirical'
                    })
    
    def _map_pathogen_name(self, pathogen_input: str) -> Optional[str]:
        """Map various pathogen name formats to our standardized names with intelligent pneumoniae matching"""
        pathogen_lower = pathogen_input.lower().strip()
        
        # Check for intelligent pneumoniae matching first
        if 'pneumoniae' in pathogen_lower:
            matched_pathogen = self._intelligent_pneumoniae_matching(pathogen_lower)
            if matched_pathogen:
                return matched_pathogen
        
        # Direct mapping
        if pathogen_lower in self.PATHOGEN_MAPPING:
            return self.PATHOGEN_MAPPING[pathogen_lower]
        
        # Partial matching
        for key, value in self.PATHOGEN_MAPPING.items():
            if key in pathogen_lower or pathogen_lower in key:
                return value
        
        return None
    
    def _intelligent_pneumoniae_matching(self, pathogen_text: str) -> Optional[str]:
        """
        Intelligent matching for pneumoniae species
        Looks for the genus word before 'pneumoniae' and maps to appropriate pathogen
        """
        import re
        
        # Pattern to find word before pneumoniae
        pattern = r'(\w+)\s+pneumoniae'
        match = re.search(pattern, pathogen_text)
        
        if match:
            genus = match.group(1).lower()
            
            # Check if we have a mapping for this genus
            if genus in self.PNEUMONIAE_MAPPINGS:
                mapping = self.PNEUMONIAE_MAPPINGS[genus]
                target_pathogen = mapping['pathogen']
                
                # Check if the target pathogen exists in our database
                try:
                    from .models import Pathogen
                    pathogen_obj = Pathogen.objects.get(name=target_pathogen)
                    
                    # Update condition if needed for pneumoniae cases
                    if not self.matched_condition and mapping['condition']:
                        try:
                            from .models import Condition
                            condition_obj = Condition.objects.get(name=mapping['condition'])
                            self.matched_condition = condition_obj
                            self.filter_steps.append({
                                'step': 1.5,  # Insert between condition and pathogen steps
                                'name': 'Intelligent Condition Matching',
                                'input': f"Pathogen '{pathogen_text}' suggests pneumonia",
                                'output': f"Auto-matched condition: '{condition_obj.name}'",
                                'result': 'success'
                            })
                        except Condition.DoesNotExist:
                            pass
                    
                    return target_pathogen
                    
                except:
                    # If exact pathogen not found, try alternatives
                    for alt_pathogen in mapping.get('alternative_pathogens', []):
                        try:
                            pathogen_obj = Pathogen.objects.get(name=alt_pathogen)
                            return alt_pathogen
                        except:
                            continue
        
        return None
    
    def _get_condition_from_pathogen(self, pathogen_text: str) -> Optional[str]:
        """
        Extract condition from pathogen information using intelligent pneumoniae matching
        """
        pathogen_lower = pathogen_text.lower().strip()
        
        if 'pneumoniae' in pathogen_lower:
            import re
            pattern = r'(\w+)\s+pneumoniae'
            match = re.search(pattern, pathogen_lower)
            
            if match:
                genus = match.group(1).lower()
                if genus in self.PNEUMONIAE_MAPPINGS:
                    return self.PNEUMONIAE_MAPPINGS[genus]['condition']
        
        return None
    
    def _process_allergies(self):
        """Step 5: Process patient allergies and create exclusion list"""
        allergies = self.patient.allergies.lower().strip()
        
        if allergies in ['none', 'no allergies', 'nkda', '']:
            self.filter_steps.append({
                'step': 5,
                'name': 'Allergy Assessment',
                'input': f"Patient allergies: '{self.patient.allergies}'",
                'output': "No allergies - no exclusions applied",
                'result': 'success'
            })
            return
        
        excluded_count = 0
        allergy_details = []
        
        for allergy_type, excluded_drugs in self.ALLERGY_EXCLUSIONS.items():
            if allergy_type in allergies:
                self.excluded_antibiotics.extend(excluded_drugs)
                excluded_count += len(excluded_drugs)
                allergy_details.append(f"{allergy_type} -> exclude {excluded_drugs}")
        
        # Remove duplicates
        self.excluded_antibiotics = list(set(self.excluded_antibiotics))
        
        self.filter_steps.append({
            'step': 5,
            'name': 'Allergy Assessment',
            'input': f"Patient allergies: '{self.patient.allergies}'",
            'output': f"Excluded {len(self.excluded_antibiotics)} antibiotic types",
            'result': 'success',
            'details': allergy_details
        })
    
    def _assess_renal_function(self):
        """Step 6: Assess renal function and dialysis status"""
        self.crcl_value = float(self.patient.cockcroft_gault_crcl)
        
        # Check if patient is on dialysis (this would need to be added to patient model)
        # For now, assume no dialysis unless CrCl is very low
        if self.crcl_value < 15:
            self.dialysis_type = 'hd'  # Assume hemodialysis for very low CrCl
            dialysis_note = "Assumed HD for CrCl < 15"
        else:
            self.dialysis_type = 'none'
            dialysis_note = "No dialysis"
        
        self.filter_steps.append({
            'step': 6,
            'name': 'Renal Function Assessment',
            'input': f"CrCl: {self.crcl_value} mL/min",
            'output': f"Dialysis type: {self.dialysis_type}, {dialysis_note}",
            'result': 'success'
        })
    
    def _get_filtered_recommendations(self) -> List[AntibioticDosing]:
        """Step 7: Apply all filters to get recommendations"""
        if not all([self.matched_condition, self.matched_severity, self.patient_type]):
            return []
        
        # Start with base query
        queryset = AntibioticDosing.objects.filter(
            condition=self.matched_condition,
            severity=self.matched_severity,
            patient_type=self.patient_type
        )
        
        initial_count = queryset.count()
        
        # Filter by pathogen
        if self.target_pathogens:
            pathogen_ids = [p.id for p in self.target_pathogens]
            pathogen_filtered_queryset = queryset.filter(pathogens__in=pathogen_ids)
            pathogen_filtered_count = pathogen_filtered_queryset.count()
            
            # If pathogen filtering returns no results, use fallback approach
            if pathogen_filtered_count == 0:
                # Use general guidelines for the condition without pathogen filtering
                self.filter_steps.append({
                    'step': 7.1,
                    'name': 'Pathogen Fallback',
                    'input': f"No guidelines for specific pathogen: {[p.name for p in self.target_pathogens]}",
                    'output': f"Using general empirical therapy for {self.matched_condition.name}",
                    'result': 'success'  # Changed from 'fallback' to 'success'
                })
                # Don't apply pathogen filter, use all guidelines for the condition
                pathogen_filtered_count = queryset.count()
            else:
                # Use pathogen-filtered results
                queryset = pathogen_filtered_queryset
        else:
            pathogen_filtered_count = queryset.count()
        
        # Filter by renal function
        if self.dialysis_type != 'none':
            # Patient is on dialysis
            renal_query = Q(dialysis_type=self.dialysis_type)
        else:
            # Normal filtering by CrCl range
            renal_query = Q(
                crcl_min__lte=self.crcl_value,
                crcl_max__gte=self.crcl_value,
                dialysis_type='none'
            )
        
        queryset = queryset.filter(renal_query)
        renal_filtered_count = queryset.count()
        
        # Filter out allergic antibiotics
        if self.excluded_antibiotics:
            for excluded in self.excluded_antibiotics:
                queryset = queryset.exclude(antibiotic__icontains=excluded)
        
        final_count = queryset.count()
        
        self.filter_steps.append({
            'step': 7,
            'name': 'Apply All Filters',
            'input': f"Initial guidelines: {initial_count}",
            'output': f"Final recommendations: {final_count}",
            'result': 'success',
            'filter_breakdown': {
                'initial': initial_count,
                'after_pathogen_filter': pathogen_filtered_count,
                'after_renal_filter': renal_filtered_count,
                'after_allergy_filter': final_count
            }
        })
        
        return list(queryset.distinct())
    
    def _rank_and_format_recommendations(self, recommendations: List[AntibioticDosing]) -> List[Dict]:
        """Enhanced ranking and formatting with medical focus"""
        if not recommendations:
            return []
        
        formatted_recommendations = []
        
        for i, dosing in enumerate(recommendations, 1):
            # Determine therapy type
            therapy_type = 'targeted' if len(self.target_pathogens) == 1 else 'empirical'
            
            # Calculate enhanced preference score
            preference_score = self._calculate_preference_score(dosing, therapy_type)
            
            # Format dosing information
            routes_display = ', '.join(dosing.route) if dosing.route else 'Not specified'
            
            # Get pathogen coverage
            pathogen_names = [p.name for p in dosing.pathogens.all()]
            
            # Generate medical rationale
            medical_rationale = self._generate_medical_rationale(dosing, therapy_type, preference_score)
            
            formatted_rec = {
                'rank': i,
                'antibiotic_name': dosing.antibiotic,
                'antibiotic': dosing.antibiotic,  # Keep for backward compatibility
                'dose': dosing.dose or 'See guidelines',
                'route': routes_display,
                'routes_array': dosing.route or [],
                'interval': dosing.interval or '',
                'duration': dosing.duration or '',
                'remark': dosing.remark or '',
                'therapy_type': therapy_type,
                'preference_score': preference_score,
                'pathogen_coverage': pathogen_names,
                'renal_adjustment': self._get_renal_adjustment_note(dosing),
                'clinical_notes': self._get_enhanced_clinical_notes(dosing),
                'medical_rationale': medical_rationale,
                'appropriateness_level': self._get_appropriateness_level(preference_score)
            }
            
            formatted_recommendations.append(formatted_rec)
        
        # Sort by preference score (higher is better) and medical appropriateness
        formatted_recommendations.sort(key=lambda x: (x['preference_score'], x['appropriateness_level']), reverse=True)
        
        # Return ALL recommendations without limiting to top 3
        all_recommendations = formatted_recommendations
        
        # Update ranks for all recommendations
        for i, rec in enumerate(all_recommendations, 1):
            rec['rank'] = i
        
        return all_recommendations
    
    def _deduplicate_by_antibiotic_name(self, recommendations: List[Dict]) -> List[Dict]:
        """Remove duplicate antibiotics, keeping only the highest scoring instance"""
        seen_antibiotics = {}
        deduplicated = []
        
        for rec in recommendations:
            antibiotic_name = rec['antibiotic_name']
            
            # Extract base antibiotic name (remove dosage info for better deduplication)
            base_name = self._extract_base_antibiotic_name(antibiotic_name)
            
            # If we haven't seen this antibiotic or this one has a higher score
            if (base_name not in seen_antibiotics or 
                rec['preference_score'] > seen_antibiotics[base_name]['preference_score']):
                seen_antibiotics[base_name] = rec
        
        # Convert back to list and maintain sorted order
        for rec in recommendations:
            base_name = self._extract_base_antibiotic_name(rec['antibiotic_name'])
            if base_name in seen_antibiotics and rec == seen_antibiotics[base_name]:
                deduplicated.append(rec)
        
        return deduplicated
    
    def _extract_base_antibiotic_name(self, full_name: str) -> str:
        """Extract base antibiotic name without dosage information"""
        import re
        
        # Remove common dosage patterns
        # Pattern 1: Simple dosages like "750mg", "500mg", "1.2 g", "3 g"
        base_name = re.sub(r'\s+\d+(\.\d+)?\s*(mg|g|mcg|µg)\b.*$', '', full_name.strip())
        
        # Pattern 2: Complex dosages like "40-60 mg", "150-200 or 300-400 mg"
        base_name = re.sub(r'\s+\d+(-\d+)?(\s+or\s+\d+(-\d+)?)?\s*(mg|g|mcg|µg)\b.*$', '', base_name)
        
        # Pattern 3: Dosages at the beginning
        base_name = re.sub(r'^\d+(\.\d+)?(-\d+(\.\d+)?)?(\s+or\s+\d+(\.\d+)?(-\d+(\.\d+)?)?)?\s*(mg|g|mcg|µg)\s+', '', base_name)
        
        return base_name.strip()
    
    def _calculate_preference_score(self, dosing: AntibioticDosing, therapy_type: str) -> int:
        """Enhanced medical preference scoring for clinical appropriateness"""
        score = 0
        
        # Base medical appropriateness scoring
        
        # 1. Therapy specificity (highest priority)
        if therapy_type == 'targeted':
            score += 15  # Targeted therapy is gold standard
        else:
            score += 5   # Empirical therapy baseline
        
        # 2. Pathogen coverage quality
        pathogen_count = dosing.pathogens.count()
        if therapy_type == 'targeted' and pathogen_count == 1:
            score += 10  # Perfect targeted coverage
        elif therapy_type == 'empirical' and pathogen_count >= 3:
            score += 8   # Good empirical coverage
        
        # 3. Route preference based on patient condition
        route_score = self._calculate_route_preference(dosing)
        score += route_score
        
        # 4. Dosing convenience and compliance
        dosing_score = self._calculate_dosing_preference(dosing)
        score += dosing_score
        
        # 5. Safety profile based on patient factors
        safety_score = self._calculate_safety_score(dosing)
        score += safety_score
        
        # 6. Resistance pattern considerations
        resistance_score = self._calculate_resistance_score(dosing)
        score += resistance_score
        
        # 7. Clinical severity appropriateness
        severity_score = self._calculate_severity_appropriateness(dosing)
        score += severity_score
        
        return max(0, score)  # Ensure non-negative
    
    def _calculate_route_preference(self, dosing: AntibioticDosing) -> int:
        """Calculate route preference based on patient condition"""
        score = 0
        routes = dosing.route or []
        
        # For severe conditions, prefer IV initially
        if self.matched_severity and 'icu' in self.matched_severity.level.lower():
            if 'IV' in routes:
                score += 8
        # For moderate conditions, prefer flexible routes
        elif 'PO' in routes and 'IV' in routes:
            score += 6  # Flexible dosing options
        # For mild conditions, prefer oral
        elif 'PO' in routes:
            score += 5
        
        return score
    
    def _calculate_dosing_preference(self, dosing: AntibioticDosing) -> int:
        """Calculate dosing convenience score"""
        score = 0
        
        if dosing.interval:
            interval_lower = dosing.interval.lower()
            # Prefer once or twice daily dosing for compliance
            if 'q24h' in interval_lower or 'daily' in interval_lower or 'once' in interval_lower:
                score += 5
            elif 'q12h' in interval_lower or 'twice' in interval_lower:
                score += 3
            elif 'q8h' in interval_lower:
                score += 1
            # Penalize very frequent dosing
            elif 'q6h' in interval_lower or 'q4h' in interval_lower:
                score -= 2
        
        return score
    
    def _calculate_safety_score(self, dosing: AntibioticDosing) -> int:
        """Calculate safety score based on patient factors"""
        score = 0
        antibiotic_lower = dosing.antibiotic.lower()
        
        # Age-related safety considerations
        if self.patient.age >= 75:
            # Prefer safer options for elderly
            if any(safe in antibiotic_lower for safe in ['cefpodoxime', 'cefuroxime', 'amoxicillin']):
                score += 3
            # Be cautious with fluoroquinolones in elderly
            elif any(fluoro in antibiotic_lower for fluoro in ['ciprofloxacin', 'levofloxacin']):
                score -= 2
        
        # Renal function considerations
        if self.crcl_value < 30:
            # Prefer antibiotics with better renal safety
            if any(renal_safe in antibiotic_lower for renal_safe in ['ceftriaxone', 'cefpodoxime']):
                score += 3
        
        # General safety profile
        first_line_safe = ['amoxicillin', 'cefpodoxime', 'cefuroxime']
        if any(safe in antibiotic_lower for safe in first_line_safe):
            score += 2
        
        return score
    
    def _calculate_resistance_score(self, dosing: AntibioticDosing) -> int:
        """Calculate resistance pattern appropriateness"""
        score = 0
        antibiotic_lower = dosing.antibiotic.lower()
        
        # Favor antibiotics with good local efficacy
        if any(effective in antibiotic_lower for effective in ['levofloxacin', 'ceftriaxone']):
            score += 3
        
        # Consider pathogen-specific resistance
        if self.target_pathogens:
            for pathogen in self.target_pathogens:
                pathogen_name = pathogen.name.lower()
                
                # E. coli specific
                if 'coli' in pathogen_name:
                    if 'levofloxacin' in antibiotic_lower or 'ceftriaxone' in antibiotic_lower:
                        score += 2
                
                # S. pneumoniae specific
                elif 'pneumoniae' in pathogen_name:
                    if 'levofloxacin' in antibiotic_lower or 'ceftriaxone' in antibiotic_lower:
                        score += 2
        
        return score
    
    def _calculate_severity_appropriateness(self, dosing: AntibioticDosing) -> int:
        """Calculate appropriateness for condition severity"""
        score = 0
        
        if not self.matched_severity:
            return score
        
        severity_name = self.matched_severity.level.lower()
        antibiotic_lower = dosing.antibiotic.lower()
        
        # ICU/severe cases need broader spectrum
        if 'icu' in severity_name:
            if any(broad in antibiotic_lower for broad in ['piperacillin', 'meropenem', 'imipenem']):
                score += 5
        
        # General ward cases
        elif 'ward' in severity_name:
            if any(standard in antibiotic_lower for standard in ['levofloxacin', 'ceftriaxone', 'cefpodoxime']):
                score += 3
        
        # Outpatient cases
        elif 'outpatient' in severity_name:
            if any(oral in antibiotic_lower for oral in ['cefpodoxime', 'amoxicillin']):
                score += 4
        
        return score
    
    def _get_renal_adjustment_note(self, dosing: AntibioticDosing) -> str:
        """Get renal adjustment notes"""
        if self.dialysis_type != 'none':
            return f"Dosing adjusted for {self.dialysis_type.upper()}"
        elif self.crcl_value < 50:
            return f"Dosing adjusted for CrCl {self.crcl_value} mL/min"
        else:
            return "No renal adjustment needed"
    
    def _get_clinical_notes(self, dosing: AntibioticDosing) -> List[str]:
        """Get additional clinical notes"""
        notes = []
        
        if dosing.remark:
            notes.append(dosing.remark)
        
        if self.patient.body_weight and self.patient.body_weight < 50:
            notes.append("Consider weight-based dosing for low body weight")
        
        if self.patient.age >= 65:
            notes.append("Consider age-related pharmacokinetic changes")
        
        return notes
    
    def _get_patient_summary(self) -> Dict:
        """Get summary of patient factors considered"""
        return {
            'patient_id': self.patient.patient_id,
            'age': self.patient.age,
            'patient_type': self.patient_type,
            'diagnosis': self.patient.diagnosis1,
            'matched_condition': self.matched_condition.name if self.matched_condition else None,
            'pathogen': self.patient.pathogen,
            'target_pathogens': [p.name for p in self.target_pathogens],
            'allergies': self.patient.allergies,
            'excluded_antibiotics': self.excluded_antibiotics,
            'crcl': self.crcl_value,
            'dialysis_type': self.dialysis_type,
            'body_weight': float(self.patient.body_weight) if self.patient.body_weight else None
        }
    
    def _no_match_result(self, reason: str) -> Dict:
        """Return result when no recommendations can be made with helpful alternatives"""
        
        # Try to provide fallback recommendations based on condition only
        fallback_recommendations = []
        if self.matched_condition:
            # Get general recommendations for the condition without pathogen filtering
            general_dosings = AntibioticDosing.objects.filter(
                condition=self.matched_condition
            ).distinct()  # Get all general recommendations
            
            for dosing in general_dosings:
                fallback_recommendations.append({
                    'antibiotic_name': dosing.antibiotic,
                    'dose': dosing.dose or 'See guidelines',
                    'route': ', '.join(dosing.route) if dosing.route else 'Not specified',
                    'interval': dosing.interval or '',
                    'clinical_priority': 'general',
                    'preference_score': 50,  # Neutral score
                    'medical_rationale': f"General empirical therapy for {self.matched_condition.name}. Consider pathogen-specific therapy when culture results available.",
                    'therapy_type': 'empirical',
                    'pathogen_coverage': ['General coverage']
                })
        
        return {
            'success': True,  # Change to True since we're providing fallback
            'reason': reason,
            'patient_id': self.patient.patient_id if self.patient else None,
            'recommendations': fallback_recommendations,
            'total_matches': len(fallback_recommendations),
            'filter_steps': self.filter_steps,
            'patient_summary': self._get_patient_summary() if self.patient else None,
            'is_fallback': True,
            'message': f"No specific pathogen match found. Showing general empirical therapy options for {self.matched_condition.name if self.matched_condition else 'the condition'}."
        }
    
    def _generate_medical_rationale(self, dosing: AntibioticDosing, therapy_type: str, score: int) -> str:
        """Generate medical rationale for the recommendation"""
        rationale_parts = []
        
        # Therapy type rationale
        if therapy_type == 'targeted':
            rationale_parts.append("Targeted therapy based on identified pathogen")
        else:
            rationale_parts.append("Empirical therapy covering likely pathogens")
        
        # Route rationale
        if dosing.route and 'PO' in dosing.route and 'IV' in dosing.route:
            rationale_parts.append("flexible oral/IV dosing options")
        elif dosing.route and 'PO' in dosing.route:
            rationale_parts.append("oral administration for outpatient management")
        elif dosing.route and 'IV' in dosing.route:
            rationale_parts.append("IV administration for severe infection")
        
        # Severity appropriateness
        if self.matched_severity:
            severity_name = self.matched_severity.level.lower()
            if 'icu' in severity_name:
                rationale_parts.append("broad-spectrum coverage for ICU setting")
            elif 'ward' in severity_name:
                rationale_parts.append("appropriate for hospitalized patients")
            elif 'outpatient' in severity_name:
                rationale_parts.append("suitable for outpatient treatment")
        
        # Safety considerations
        if self.patient.age >= 75:
            rationale_parts.append("age-appropriate safety profile")
        
        if self.crcl_value < 50:
            rationale_parts.append("acceptable in renal impairment")
        
        return "; ".join(rationale_parts).capitalize() + "."
    
    def _get_appropriateness_level(self, score: int) -> int:
        """Convert preference score to appropriateness level"""
        if score >= 25:
            return 5  # Highly appropriate
        elif score >= 20:
            return 4  # Very appropriate
        elif score >= 15:
            return 3  # Appropriate
        elif score >= 10:
            return 2  # Moderately appropriate
        else:
            return 1  # Less appropriate
    
    def _get_enhanced_clinical_notes(self, dosing: AntibioticDosing) -> List[str]:
        """Get enhanced clinical notes with medical considerations"""
        notes = []
        
        # Original remark
        if dosing.remark:
            notes.append(dosing.remark)
        
        # Weight considerations
        if self.patient.body_weight and self.patient.body_weight < 50:
            notes.append("Consider weight-based dosing adjustment")
        elif self.patient.body_weight and self.patient.body_weight > 100:
            notes.append("Consider higher dosing for increased body weight")
        
        # Age considerations
        if self.patient.age >= 75:
            notes.append("Monitor for age-related adverse effects")
        elif self.patient.age < 18:
            notes.append("Pediatric dosing considerations apply")
        
        # Renal considerations
        if self.crcl_value < 30:
            notes.append("Close monitoring required in severe renal impairment")
        elif self.crcl_value < 60:
            notes.append("Monitor renal function during treatment")
        
        # Pathogen-specific notes
        if self.target_pathogens:
            for pathogen in self.target_pathogens:
                pathogen_name = pathogen.name.lower()
                if 'coli' in pathogen_name:
                    notes.append("Monitor for resistance patterns in E. coli")
                elif 'pneumoniae' in pathogen_name:
                    notes.append("Consider macrolide sensitivity testing")
        
        # Duration guidance
        if self.matched_condition:
            condition_name = self.matched_condition.name.lower()
            if 'pneumonia' in condition_name:
                notes.append("Typical duration 5-7 days for CAP")
            elif 'pyelonephritis' in condition_name:
                notes.append("Typical duration 7-14 days")
        
        return notes


def get_antibiotic_recommendations(patient: Patient) -> Dict:
    """
    Get antibiotic recommendations for a patient
    
    Args:
        patient: Patient object
        
    Returns:
        Dict with recommendations and metadata
    """
    engine = AntibioticRecommendationEngine()
    return engine.get_recommendations(patient)
