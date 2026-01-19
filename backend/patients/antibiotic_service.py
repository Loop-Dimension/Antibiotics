from patients.models import Patient, AntibioticDosing, Condition
from django.db.models import Q
import re
from .antibiotic_matcher import AntibioticMatcher
from .drug_classifier import DrugClassifier


class AntibioticRecommendationService:
    
    @staticmethod
    def get_recommendations_for_patient(patient):
        """
        Get antibiotic recommendations based on patient's DIAGNOSIS (condition).
        Looks up AntibioticDosing records linked to the patient's diagnosis1.
        """
        try:
            if not isinstance(patient, Patient):
                return {
                    'recommendations': [],
                    'current_antibiotic_analysis': None,
                    'message': 'Invalid patient data provided',
                    'status': 'error'
                }
            
            # Validate essential patient data
            if not hasattr(patient, 'patient_id') or not patient.patient_id:
                return {
                    'recommendations': [],
                    'current_antibiotic_analysis': None,
                    'message': 'Patient ID is required',
                    'status': 'error'
                }
            
            # Analyze current antibiotic first
            current_antibiotic_analysis = AntibioticRecommendationService._analyze_current_antibiotic(patient)
            
            # Get patient's diagnosis
            diagnosis = getattr(patient, 'diagnosis1', None)
            if not diagnosis:
                return {
                    'recommendations': [],
                    'current_antibiotic_analysis': current_antibiotic_analysis,
                    'message': 'No diagnosis specified - Cannot provide recommendations',
                    'status': 'no_diagnosis'
                }
            
            # Get recommendations by diagnosis/condition
            recommendations = AntibioticRecommendationService._get_recommendations_by_diagnosis(patient, diagnosis)
            
            if not recommendations:
                # Fallback: try similarity matching on current antibiotic
                if hasattr(patient, 'antibiotics') and patient.antibiotics:
                    similar_matches = AntibioticRecommendationService._get_exact_antibiotic_matches(patient)
                    if similar_matches:
                        try:
                            crcl = float(patient.cockcroft_gault_crcl) if patient.cockcroft_gault_crcl else 60.0
                        except (ValueError, TypeError):
                            crcl = 60.0
                        
                        clinically_appropriate = AntibioticRecommendationService._filter_exact_matches_by_clinical_criteria(
                            similar_matches, patient, crcl
                        )
                        if clinically_appropriate:
                            recommendations = AntibioticRecommendationService._rank_exact_matches(
                                clinically_appropriate, patient
                            )
                
                if not recommendations:
                    return {
                        'recommendations': [],
                        'current_antibiotic_analysis': current_antibiotic_analysis,
                        'message': f'No recommendations found for diagnosis: {diagnosis}',
                        'status': 'no_recommendations'
                    }
            
            return {
                'recommendations': recommendations,
                'current_antibiotic_analysis': current_antibiotic_analysis,
                'message': f'Found {len(recommendations)} recommendation(s) for "{diagnosis}"',
                'status': 'success'
            }
            
        except Exception as e:
            # Log the error
            print(f"Error in get_recommendations_for_patient: {str(e)}")
            
            return {
                'recommendations': [],
                'current_antibiotic_analysis': None,
                'message': f'System error: {str(e)}',
                'status': 'system_error'
            }
    
    @staticmethod
    def _get_recommendations_by_diagnosis(patient, diagnosis):
        """
        Get antibiotic dosing recommendations based on patient's diagnosis.
        Matches diagnosis1 to Condition name in AntibioticDosing table.
        """
        diagnosis_lower = diagnosis.lower().strip()
        
        # Find matching condition(s)
        matching_conditions = Condition.objects.filter(
            Q(name__iexact=diagnosis) | 
            Q(name__icontains=diagnosis_lower) |
            Q(description__icontains=diagnosis_lower)
        )
        
        if not matching_conditions.exists():
            return []
        
        # Get patient's CrCl
        try:
            crcl = float(patient.cockcroft_gault_crcl) if patient.cockcroft_gault_crcl else 60.0
        except (ValueError, TypeError):
            crcl = 60.0
        
        # Get allergies
        allergies = (getattr(patient, 'allergies', '') or '').lower()
        
        # Get dosing recommendations for matching conditions
        dosings = AntibioticDosing.objects.filter(
            condition__in=matching_conditions
        ).select_related('condition', 'severity')
        
        recommendations = []
        seen_antibiotics = set()  # Avoid duplicates
        
        for dosing in dosings:
            # Skip if already seen this antibiotic
            antibiotic_key = f"{dosing.antibiotic}_{dosing.interval}"
            if antibiotic_key in seen_antibiotics:
                continue
            seen_antibiotics.add(antibiotic_key)
            
            # Check CrCl compatibility
            if dosing.crcl_min is not None and dosing.crcl_max is not None:
                if not (dosing.crcl_min <= crcl <= dosing.crcl_max):
                    continue
            
            # Check allergies
            if allergies and 'none' not in allergies:
                antibiotic_name = dosing.antibiotic.lower()
                if any(allergen in antibiotic_name for allergen in allergies.split(',')):
                    continue
            
            # Build recommendation object
            route_str = ', '.join(dosing.route) if isinstance(dosing.route, list) else str(dosing.route or '')
            
            recommendations.append({
                'antibiotic': dosing.antibiotic,
                'dose': dosing.dose or 'As prescribed',
                'route': route_str,
                'interval': dosing.interval or '',
                'duration': dosing.duration or '',
                'remarks': dosing.remark or '',
                'condition': dosing.condition.name,
                'severity': dosing.severity.level if dosing.severity else 'Standard',
                'crcl_range': f"{dosing.crcl_min or ''}-{dosing.crcl_max or ''}" if dosing.crcl_min or dosing.crcl_max else 'Any',
                'dialysis_type': dosing.dialysis_type or 'none',
                'patient_type': dosing.patient_type or 'adult',
                'rationale': f'Recommended for {dosing.condition.name}',
                'score': 10  # Base score
            })
        
        # Sort by antibiotic name
        recommendations.sort(key=lambda x: x['antibiotic'])
        
        return recommendations
    
    @staticmethod
    def _get_exact_antibiotic_matches(patient):
        """
        Get most similar antibiotic name matches from database using fuzzy matching.
        Returns the best matching antibiotics based on name similarity.
        """
        if not hasattr(patient, 'antibiotics') or not patient.antibiotics:
            return []
        
        # Parse current antibiotic
        parsed_antibiotic = AntibioticMatcher.parse_current_antibiotic(patient.antibiotics)
        if not parsed_antibiotic or not parsed_antibiotic.get('name'):
            return []
        
        current_name = parsed_antibiotic['name'].lower().strip()
        
        # Get fuzzy matches from database with similarity scoring
        patient_crcl = float(patient.cockcroft_gault_crcl) if patient.cockcroft_gault_crcl else None
        matching_results = AntibioticMatcher.find_matching_antibiotics(current_name, patient_crcl)
        
        if not matching_results:
            return []
        
        # Sort by similarity score (highest first)
        matching_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Get the best match(es) - take matches within 10 points of the best score
        best_score = matching_results[0].get('score', 0)
        
        # Accept matches with score >= 50 OR within 10 points of best match
        similar_matches = []
        for match_result in matching_results:
            score = match_result.get('score', 0)
            if score >= 50 and (score >= best_score - 10):  # Similar enough
                similar_matches.append(match_result['antibiotic'])
        
        return similar_matches
    
    @staticmethod
    def _filter_exact_matches_by_clinical_criteria(exact_matches, patient, crcl):
        """
        Filter exact matches by clinical appropriateness (CrCl, allergies).
        """
        if not exact_matches:
            return []
        
        clinically_appropriate = []
        allergies = (patient.allergies or '').lower()
        
        for antibiotic in exact_matches:
            # Check CrCl compatibility using crcl_min and crcl_max fields
            if antibiotic.crcl_min is not None and antibiotic.crcl_max is not None:
                if not (antibiotic.crcl_min <= crcl <= antibiotic.crcl_max):
                    continue
            
            # Basic allergy check - skip if antibiotic name is in allergies
            antibiotic_name = antibiotic.antibiotic.lower()
            if allergies and 'none' not in allergies:
                # Check if any part of the antibiotic name matches allergies
                skip_due_to_allergy = False
                for word in antibiotic_name.split():
                    if word in allergies:
                        skip_due_to_allergy = True
                        break
                
                if skip_due_to_allergy:
                    continue
            
            clinically_appropriate.append(antibiotic)
        
        return clinically_appropriate
    
    @staticmethod
    def _rank_exact_matches(similar_matches, patient):
        """
        Rank similar matches by clinical appropriateness and similarity.
        """
        if not similar_matches:
            return []
        
        ranked_matches = []
        
        for antibiotic in similar_matches:
            # Calculate clinical score
            score = 10  # Base score for similar match
            
            # Bonus for IV route if patient has severe infection
            if antibiotic.route and 'IV' in antibiotic.route.upper():
                if AntibioticRecommendationService._has_severe_infection_indicators(patient):
                    score += 2
            
            # Bonus for appropriate interval (once daily is preferred)
            if antibiotic.interval and 'q24h' in antibiotic.interval:
                score += 1  # Once daily is often preferred for compliance
            
            # Create rationale showing similarity
            current_antibiotic = getattr(patient, 'antibiotics', 'current antibiotic')
            rationale = f"⭐ SIMILAR MATCH: {antibiotic.antibiotic} matches '{current_antibiotic}'"
            if hasattr(antibiotic, 'indication') and antibiotic.indication:
                rationale += f"; {antibiotic.indication}"
            elif antibiotic.remark:
                rationale += f"; {antibiotic.remark}"
            rationale += "; Per IDSA 2024 guidelines"
            
            recommendation = {
                'antibiotic': antibiotic.antibiotic,
                'dose': antibiotic.dose or 'Standard dose',
                'frequency': antibiotic.interval or 'Standard interval',
                'route': antibiotic.route or 'Standard route',
                'duration': '7-10 days',  # Default duration
                'rationale': rationale,
                'priority': 'Similar Match',
                'score': score,
                'is_similar_match': True
            }
            
            ranked_matches.append(recommendation)
        
        # Sort by score (highest first), then by antibiotic name for consistency
        ranked_matches.sort(key=lambda x: (-x['score'], x['antibiotic']))
        
        return ranked_matches
    
    @staticmethod
    def _safe_float(value):
        """Safely convert value to float with fallback"""
        try:
            if value is None:
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _get_suitable_antibiotics_with_fallback(crcl, pathogen, diagnosis, allergies, age, severity_indicators):
        """
        Enhanced version with multiple fallback strategies
        """
        # Try exact matching first
        suitable = AntibioticRecommendationService._get_suitable_antibiotics(
            crcl, pathogen, diagnosis, allergies, age, severity_indicators
        )
        
        if suitable:
            return suitable
        
        # Fallback 1: Ignore pathogen specificity (empiric therapy)
        suitable = AntibioticRecommendationService._get_suitable_antibiotics(
            crcl, None, diagnosis, allergies, age, severity_indicators
        )
        
        if suitable:
            return suitable
        
        # Fallback 2: Ignore diagnosis specificity 
        suitable = AntibioticRecommendationService._get_suitable_antibiotics(
            crcl, None, None, allergies, age, severity_indicators
        )
        
        if suitable:
            return suitable
        
        # Fallback 3: Only consider CrCl and major allergies
        if allergies and allergies.lower() != 'none':
            suitable = AntibioticRecommendationService._get_suitable_antibiotics(
                crcl, None, None, allergies, age, severity_indicators
            )
        else:
            suitable = AntibioticRecommendationService._get_suitable_antibiotics(
                crcl, None, None, None, age, severity_indicators
            )
        
        return suitable
    
    @staticmethod
    def _get_fallback_recommendations(crcl, patient):
        """
        Provide standard broad-spectrum recommendations when no matches found
        """
        fallback = []
        
        # Standard broad-spectrum options based on CrCl
        if crcl >= 50:
            fallback = [
                {
                    'antibiotic': 'Ceftriaxone (Broad-spectrum)',
                    'dose': '2g',
                    'route': 'IV',
                    'interval': 'q24h',
                    'duration': '7-10 days',
                    'rationale': 'Broad-spectrum empiric therapy; Safe with normal kidney function',
                    'score': 4,
                    'crcl_adjusted': False
                },
                {
                    'antibiotic': 'Levofloxacin (Broad-spectrum)',
                    'dose': '750mg',
                    'route': 'IV/PO',
                    'interval': 'q24h',
                    'duration': '7-10 days',
                    'rationale': 'Broad-spectrum quinolone; Good bioavailability',
                    'score': 3,
                    'crcl_adjusted': False
                }
            ]
        elif crcl >= 30:
            fallback = [
                {
                    'antibiotic': 'Ceftriaxone (Renal-adjusted)',
                    'dose': '1g',
                    'route': 'IV',
                    'interval': 'q24h',
                    'duration': '7-10 days',
                    'rationale': f'Broad-spectrum therapy; Dose reduced for CrCl {crcl:.1f}',
                    'score': 4,
                    'crcl_adjusted': True
                }
            ]
        else:
            fallback = [
                {
                    'antibiotic': 'Consult Nephrology',
                    'dose': 'Individualized',
                    'route': 'TBD',
                    'interval': 'TBD',
                    'duration': 'TBD',
                    'rationale': f'Severe renal impairment (CrCl {crcl:.1f}) - Requires specialist consultation',
                    'score': 2,
                    'crcl_adjusted': True
                }
            ]
        
        return fallback
    
    @staticmethod
    def _get_emergency_fallback():
        """
        Emergency recommendations when system fails
        """
        return [
            {
                'antibiotic': 'SYSTEM ERROR - Manual Review Required',
                'dose': 'See guidelines',
                'route': 'Per protocol',
                'interval': 'Per protocol',
                'duration': 'Per protocol',
                'rationale': 'System error encountered. Please consult IDSA guidelines or infectious disease specialist.',
                'score': 1,
                'crcl_adjusted': False
            }
        ]
    
    @staticmethod
    def _get_suitable_antibiotics(crcl, pathogen, diagnosis, allergies, age, severity_indicators):
        """
        Filter antibiotics based on patient criteria
        """
        suitable = []
        
        # Get all antibiotic dosing records
        all_antibiotics = AntibioticDosing.objects.all()
        
        for antibiotic in all_antibiotics:
            # Check CrCl compatibility using crcl_min and crcl_max
            if antibiotic.crcl_min is not None and antibiotic.crcl_max is not None:
                if not (antibiotic.crcl_min <= crcl <= antibiotic.crcl_max):
                    continue
            
            # Check allergies/contraindications
            if allergies:
                antibiotic_name = antibiotic.antibiotic.lower()
                if any(allergen.lower() in antibiotic_name for allergen in allergies.split(',')):
                    continue
            
            suitable.append(antibiotic)
        
        return suitable
    
    @staticmethod
    def _is_crcl_compatible(crcl_range, patient_crcl):
        """
        Check if patient's CrCl matches the antibiotic's CrCl range
        """
        if not crcl_range or not patient_crcl:
            return True
        
        crcl_range = crcl_range.strip()
        
        # Handle special cases
        if crcl_range in ['HD', 'CRRT', 'PD']:
            return False  # For now, don't recommend for dialysis patients
        
        # Handle >= ranges
        if crcl_range.startswith('>='):
            threshold = float(crcl_range[2:])
            return patient_crcl >= threshold
        
        # Handle > ranges
        if crcl_range.startswith('>'):
            threshold = float(crcl_range[1:])
            return patient_crcl > threshold
        
        # Handle <= ranges
        if crcl_range.startswith('<='):
            threshold = float(crcl_range[2:])
            return patient_crcl <= threshold
        
        # Handle < ranges
        if crcl_range.startswith('<'):
            threshold = float(crcl_range[1:])
            return patient_crcl < threshold
        
        # Handle ranges like "20-50"
        if '-' in crcl_range:
            try:
                parts = crcl_range.split('-')
                if len(parts) == 2:
                    lower = float(parts[0])
                    upper = float(parts[1])
                    return lower <= patient_crcl <= upper
            except ValueError:
                pass
        
        # Default to compatible if can't parse
        return True
    
    @staticmethod
    def _is_pathogen_effective(pathogen_effectiveness, patient_pathogen):
        """
        Check if antibiotic is effective against patient's pathogen
        """
        if not pathogen_effectiveness:
            return True  # Default to compatible if no pathogen effectiveness data
            
        if not patient_pathogen:
            return True  # Default to compatible if no patient pathogen
        
        patient_pathogen_lower = patient_pathogen.lower()
        
        # Handle cases where pathogen is pending, unknown, or NA
        if any(word in patient_pathogen_lower for word in ['pending', 'unknown', 'na', 'culture pending']):
            return True  # Allow empiric therapy for unknown pathogens
        
        for effective_pathogen in pathogen_effectiveness:
            if effective_pathogen.lower() in patient_pathogen_lower:
                return True
            
            # Check for partial matches
            if any(word in patient_pathogen_lower for word in effective_pathogen.lower().split()):
                return True
        
        return False
    
    @staticmethod
    def _is_infection_compatible(infection_types, patient_diagnosis):
        """
        Check if antibiotic is suitable for patient's infection type
        """
        if not infection_types or not patient_diagnosis:
            return True  # Default to compatible if no data
        
        patient_diagnosis_lower = patient_diagnosis.lower()
        
        for infection_type in infection_types:
            infection_lower = infection_type.lower()
            
            # Direct matches
            if infection_lower in patient_diagnosis_lower:
                return True
            
            # Specific matching logic
            if infection_lower == 'uti' and any(word in patient_diagnosis_lower for word in [
                'pyelonephritis', 'ureteritis', 'urinary', 'urine'
            ]):
                return True
            
            if infection_lower == 'pneumonia' and 'pneumonia' in patient_diagnosis_lower:
                return True
                
            if infection_lower == 'sepsis' and any(word in patient_diagnosis_lower for word in [
                'sepsis', 'bacteremia', 'blood'
            ]):
                return True
        
        return False
    
    @staticmethod
    def _has_contraindication(contraindications, patient_allergies):
        """
        Check if patient has allergies that contraindicate this antibiotic
        """
        if not contraindications or not patient_allergies:
            return False
        
        patient_allergies_lower = patient_allergies.lower()
        
        for contraindication in contraindications:
            contraindication_lower = contraindication.lower()
            
            # Direct allergy match
            if contraindication_lower in patient_allergies_lower:
                return True
            
            # Check for class allergies
            if 'penicillin' in contraindication_lower and any(word in patient_allergies_lower for word in [
                'penicillin', 'amoxicillin', 'ampicillin'
            ]):
                return True
                
            if 'cephalosporin' in contraindication_lower and any(word in patient_allergies_lower for word in [
                'cephalosporin', 'ceftriaxone', 'cefepime', 'cefotaxime'
            ]):
                return True
        
        return False
    
    @staticmethod
    def _rank_recommendations(suitable_antibiotics, patient):
        """
        Rank antibiotic recommendations based on various factors including current antibiotic matching
        """
        ranked = []
        current_antibiotic_name = ""
        current_antibiotic_analysis = None
        
        # Get current antibiotic for comparison
        if hasattr(patient, 'antibiotics') and patient.antibiotics:
            current_antibiotic_analysis = AntibioticRecommendationService._analyze_current_antibiotic(patient)
            if current_antibiotic_analysis.get('best_match') and current_antibiotic_analysis['best_match'].get('antibiotic'):
                current_antibiotic_name = current_antibiotic_analysis['best_match']['antibiotic_name']
        
        for antibiotic in suitable_antibiotics:
            score = antibiotic.severity_score
            
            # Get current antibiotic analysis once
            current_antibiotic_best_match = None
            if current_antibiotic_analysis and current_antibiotic_analysis.get('best_match'):
                # Get the raw antibiotic object for comparison (stored in 'antibiotic' key)
                current_antibiotic_best_match = current_antibiotic_analysis['best_match'].get('antibiotic')
            
            # PRIORITY 1: Check if this IS the current antibiotic (exact match)
            is_current_antibiotic = (current_antibiotic_best_match and 
                                   antibiotic.antibiotic == current_antibiotic_best_match.antibiotic and
                                   antibiotic.crcl_min == current_antibiotic_best_match.crcl_min and
                                   antibiotic.crcl_max == current_antibiotic_best_match.crcl_max)
            
            if is_current_antibiotic:
                # Check if current antibiotic is appropriate
                appropriateness = current_antibiotic_analysis.get('appropriateness', {}) if current_antibiotic_analysis else {}
                contraindications = current_antibiotic_analysis.get('contraindication_warning') if current_antibiotic_analysis else None
                
                # If current antibiotic is appropriate and no major contraindications, give it highest priority
                if (appropriateness.get('status') in ['appropriate', 'needs_review'] and 
                    not contraindications):
                    score += 10  # Huge bonus for continuing current appropriate therapy
                elif contraindications:
                    score -= 5   # Penalize if there are contraindications
                else:
                    score += 5   # Still give some bonus for continuity, but less
            
            # Bonus points for pathogen match using pathogens ManyToMany field
            if patient.pathogen and antibiotic.pathogens.exists():
                pathogen_names = list(antibiotic.pathogens.values_list('name', flat=True))
                if any(p.lower() in patient.pathogen.lower() for p in pathogen_names):
                    score += 2
            
            # Route preference based on patient stability
            is_stable = AntibioticRecommendationService._is_patient_stable(patient)
            if is_stable and antibiotic.route == 'PO':
                score += 1
            elif not is_stable and antibiotic.route == 'IV':
                score += 1
            
            # Bonus for first-line antibiotics based on diagnosis
            if AntibioticRecommendationService._is_first_line(antibiotic, patient.diagnosis1):
                score += 2
            
            # ONLY apply class diversity penalty if NOT the current antibiotic
            if not is_current_antibiotic and current_antibiotic_name:
                class_analysis = DrugClassifier.should_avoid_same_class(
                    current_antibiotic_name, 
                    antibiotic.antibiotic,
                    clinical_context={
                        'current_route': AntibioticRecommendationService._extract_route_from_current(patient.antibiotics) if hasattr(patient, 'antibiotics') else None,
                        'recommendation_route': antibiotic.route,
                        'treatment_failure': False
                    }
                )
                
                if class_analysis['avoid']:
                    score -= 3  # Penalize same class alternatives
                else:
                    score += 1  # Bonus for different class alternatives
            
            # Calculate duration based on diagnosis
            duration = AntibioticRecommendationService._get_recommended_duration(
                antibiotic, patient.diagnosis1
            )
            
            # Prepare rationale with current antibiotic considerations
            rationale = AntibioticRecommendationService._generate_rationale(
                antibiotic, patient, is_stable, current_antibiotic_name, is_current_antibiotic
            )
            
            ranked.append({
                'antibiotic': antibiotic.antibiotic,
                'dose': antibiotic.dose or 'Standard dose',
                'route': antibiotic.route or 'IV',
                'interval': antibiotic.interval or 'q24h',
                'duration': duration,
                'rationale': rationale,
                'score': score,
                'crcl_adjusted': patient.cockcroft_gault_crcl < 50 if patient.cockcroft_gault_crcl else False,
                'drug_class': DrugClassifier.classify_antibiotic(antibiotic.antibiotic)['class'],
                'is_current_antibiotic': is_current_antibiotic
            })
        
        # Sort by score (descending) - current appropriate antibiotic should be first
        ranked.sort(key=lambda x: x['score'], reverse=True)
        
        # Only apply diversity filter if current antibiotic is not appropriate or not found
        current_is_top_choice = ranked and ranked[0].get('is_current_antibiotic', False)
        
        if not current_is_top_choice:
            # Apply diversity filter for alternatives
            diversified_ranked = AntibioticRecommendationService._ensure_class_diversity(ranked, top_n=5)
            return diversified_ranked
        else:
            # Current antibiotic is best choice - return as-is
            return ranked
    
    @staticmethod
    def _is_patient_stable(patient):
        """
        Determine if patient is stable based on vitals
        """
        # Consider stable if:
        # - Temperature < 38.5
        # - WBC < 15000
        # - CRP < 100
        
        temp_stable = not patient.body_temperature or float(patient.body_temperature) < 38.5
        wbc_stable = not patient.wbc or float(patient.wbc) < 15000
        crp_stable = not patient.crp or float(patient.crp) < 100
        
        return temp_stable and wbc_stable and crp_stable
    
    @staticmethod
    def _has_severe_infection_indicators(patient):
        """
        Determine if patient has severe infection indicators that warrant IV therapy
        """
        # Check for high fever
        if hasattr(patient, 'body_temperature') and patient.body_temperature:
            try:
                temp = float(patient.body_temperature)
                if temp >= 39.0:  # High fever >= 39°C
                    return True
            except (ValueError, TypeError):
                pass
        
        # Check for elevated WBC
        if hasattr(patient, 'wbc') and patient.wbc:
            try:
                wbc = float(patient.wbc)
                if wbc >= 20000:  # Very high WBC
                    return True
            except (ValueError, TypeError):
                pass
        
        # Check for very high CRP
        if hasattr(patient, 'crp') and patient.crp:
            try:
                crp = float(patient.crp)
                if crp >= 150:  # Very high CRP
                    return True
            except (ValueError, TypeError):
                pass
        
        # Check for severe diagnoses
        if hasattr(patient, 'diagnosis1') and patient.diagnosis1:
            severe_conditions = ['sepsis', 'bacteremia', 'endocarditis', 'meningitis', 
                               'severe pneumonia', 'necrotizing']
            if any(condition in patient.diagnosis1.lower() for condition in severe_conditions):
                return True
        
        return False
    
    @staticmethod
    def _is_first_line(antibiotic, diagnosis):
        """
        Check if antibiotic is first-line for the diagnosis
        """
        if not diagnosis:
            return False
        
        diagnosis_lower = diagnosis.lower()
        antibiotic_lower = antibiotic.antibiotic.lower()
        
        # UTI/Pyelonephritis first-line
        if any(word in diagnosis_lower for word in ['pyelonephritis', 'ureteritis', 'uti']):
            return any(drug in antibiotic_lower for drug in [
                'ciprofloxacin', 'levofloxacin', 'ceftriaxone'
            ])
        
        # Pneumonia first-line
        if 'pneumonia' in diagnosis_lower:
            return any(drug in antibiotic_lower for drug in [
                'ceftriaxone', 'levofloxacin', 'cefepime'
            ])
        
        return False
    
    @staticmethod
    def _get_recommended_duration(antibiotic, diagnosis):
        """
        Get recommended duration based on diagnosis and antibiotic
        """
        if not diagnosis:
            return '7 days'
        
        diagnosis_lower = diagnosis.lower()
        
        # UTI/Pyelonephritis
        if any(word in diagnosis_lower for word in ['pyelonephritis', 'ureteritis']):
            return '7-10 days'
        
        # Pneumonia
        if 'pneumonia' in diagnosis_lower:
            return '7-10 days'
        
        # Default
        return '5-7 days'
    
    @staticmethod
    def _generate_rationale(antibiotic, patient, is_stable, current_antibiotic_name=None, is_current_antibiotic=False):
        """
        Generate enhanced rationale for the recommendation including current antibiotic considerations
        """
        rationale_parts = []
        
        # If this IS the current antibiotic
        if is_current_antibiotic:
            rationale_parts.append("Continue current therapy")
            
            # Add clinical justification for continuing using pathogens field
            if patient.pathogen and antibiotic.pathogens.exists():
                pathogen_names = list(antibiotic.pathogens.values_list('name', flat=True))
                if any(p.lower() in patient.pathogen.lower() for p in pathogen_names):
                    rationale_parts.append(f"Excellent coverage for {patient.pathogen}")
                else:
                    rationale_parts.append("Empiric coverage maintained")
            
            # Add appropriateness note
            rationale_parts.append("Current regimen clinically appropriate")
            
        else:
            # This is an alternative recommendation
            # Pathogen coverage using pathogens field
            if patient.pathogen and antibiotic.pathogens.exists():
                pathogen_names = list(antibiotic.pathogens.values_list('name', flat=True))
                if any(p.lower() in patient.pathogen.lower() for p in pathogen_names):
                    rationale_parts.append(f"Excellent coverage for {patient.pathogen}")
                else:
                    rationale_parts.append("Broad-spectrum empiric coverage")
            
            # Drug class considerations for alternatives
            if current_antibiotic_name:
                class_analysis = DrugClassifier.should_avoid_same_class(
                    current_antibiotic_name, 
                    antibiotic.antibiotic
                )
                
                if class_analysis['avoid']:
                    current_class = DrugClassifier.classify_antibiotic(current_antibiotic_name)
                    rationale_parts.append(f"Alternative to current {current_class['class']}")
                else:
                    # If it's a different class, mention the class advantage
                    rec_classification = DrugClassifier.classify_antibiotic(antibiotic.antibiotic)
                    if rec_classification['class'] != 'unknown':
                        rationale_parts.append(f"{rec_classification['details']['mechanism']}")
        
        # CrCl adjustment (applies to both current and alternatives)
        if patient.cockcroft_gault_crcl and float(patient.cockcroft_gault_crcl) < 50:
            rationale_parts.append(f"Dose adjusted for CrCl {float(patient.cockcroft_gault_crcl):.1f}")
        
        # Route selection
        if antibiotic.route == 'PO' and is_stable:
            rationale_parts.append("Oral route appropriate for stable patient")
        elif antibiotic.route == 'IV' and not is_stable:
            rationale_parts.append("IV route for severe infection")
        
        # Guideline compliance
        rationale_parts.append("Per IDSA 2024 guidelines")
        
        return "; ".join(rationale_parts) if rationale_parts else "Standard empiric therapy"
    
    @staticmethod
    def _extract_route_from_current(current_antibiotic_string):
        """
        Extract route from current antibiotic string
        """
        if not current_antibiotic_string:
            return None
        
        route_match = re.match(r'(po|iv|im|sc|top)\s+', current_antibiotic_string.lower())
        return route_match.group(1).upper() if route_match else None
    
    @staticmethod
    def _ensure_class_diversity(ranked_recommendations, top_n=5):
        """
        Ensure top recommendations include diverse antibiotic classes when possible
        """
        if len(ranked_recommendations) <= 1:
            return ranked_recommendations
        
        # Keep track of classes already selected
        selected_classes = set()
        diversified = []
        remaining = []
        
        # First pass: select highest scoring antibiotics from different classes
        for rec in ranked_recommendations:
            drug_class = rec.get('drug_class', 'unknown')
            
            if drug_class not in selected_classes and drug_class != 'unknown':
                selected_classes.add(drug_class)
                diversified.append(rec)
            else:
                remaining.append(rec)
            
            # Stop if we have enough diverse recommendations
            if len(diversified) >= top_n:
                break
        
        # Second pass: fill remaining slots with highest scoring options
        while len(diversified) < min(top_n, len(ranked_recommendations)):
            if remaining:
                diversified.append(remaining.pop(0))
            else:
                break
        
        # Add any remaining recommendations
        diversified.extend(remaining)
        
        return diversified
    
    @staticmethod
    def _analyze_current_antibiotic(patient):
        """
        Analyze the patient's current antibiotic and provide detailed information
        """
        if not hasattr(patient, 'antibiotics') or not patient.antibiotics:
            return {
                'status': 'none',
                'message': 'No current antibiotic specified',
                'matches': [],
                'parsed': {},
                'contraindication_warning': None
            }
        
        current_abx = patient.antibiotics.strip()
        
        # Get patient CrCl for clinical matching
        patient_crcl = None
        if hasattr(patient, 'cockcroft_gault_crcl') and patient.cockcroft_gault_crcl:
            try:
                patient_crcl = float(patient.cockcroft_gault_crcl)
            except (ValueError, TypeError):
                pass
        
        # Use the matcher to analyze the current antibiotic with clinical context
        explanation = AntibioticMatcher.explain_current_antibiotic(current_abx, patient_crcl)
        
        # Check for contraindications (allergies)
        contraindication_warning = AntibioticRecommendationService._check_current_antibiotic_contraindications(
            explanation.get('best_match'), patient
        )
        
        # Determine appropriateness for patient's condition
        appropriateness = AntibioticRecommendationService._assess_current_antibiotic_appropriateness(
            explanation.get('best_match'), patient
        )
        
        # Convert matches to serializable format
        serializable_matches = []
        for match in explanation.get('matches', [])[:3]:
            if match.get('antibiotic'):
                ab = match['antibiotic']
                serializable_matches.append({
                    'antibiotic_name': ab.antibiotic,
                    'crcl_range': f"{ab.crcl_min or ''}-{ab.crcl_max or ''}" if ab.crcl_min or ab.crcl_max else 'Any',
                    'route': ab.route,
                    'dose': match['antibiotic'].dose,
                    'interval': match['antibiotic'].interval,
                    'score': match.get('score', 0),
                    'base_score': match.get('base_score', 0),
                    'clinical_bonus': match.get('clinical_bonus', 0),
                    'match_type': match.get('match_type', 'unknown')
                })
        
        # Convert best match to serializable format
        serializable_best_match = None
        if explanation.get('best_match') and explanation['best_match'].get('antibiotic'):
            best_match = explanation['best_match']
            ab = best_match['antibiotic']
            serializable_best_match = {
                'antibiotic_name': ab.antibiotic,
                'crcl_range': f"{ab.crcl_min or ''}-{ab.crcl_max or ''}" if ab.crcl_min or ab.crcl_max else 'Any',
                'route': ab.route,
                'dose': best_match['antibiotic'].dose,
                'interval': best_match['antibiotic'].interval,
                'score': best_match.get('score', 0),
                'base_score': best_match.get('base_score', 0),
                'clinical_bonus': best_match.get('clinical_bonus', 0),
                'match_type': best_match.get('match_type', 'unknown'),
                'antibiotic': best_match['antibiotic']  # Keep original for internal use
            }
        
        return {
            'original': current_abx,
            'parsed': explanation.get('parsed', {}),
            'database_matches': serializable_matches,
            'best_match': serializable_best_match,
            'total_matches': explanation.get('total_matches', 0),
            'contraindication_warning': contraindication_warning,
            'appropriateness': appropriateness,
            'status': 'analyzed' if explanation.get('best_match') else 'unknown'
        }
    
    @staticmethod
    def _check_current_antibiotic_contraindications(best_match, patient):
        """
        Check if current antibiotic has contraindications for this patient
        """
        if not best_match or not hasattr(patient, 'allergies') or not patient.allergies:
            return None
        
        antibiotic_obj = best_match.get('antibiotic')
        if not antibiotic_obj:
            return None
        
        patient_allergies = patient.allergies.lower()
        antibiotic_name = antibiotic_obj.antibiotic.lower()
        
        warnings = []
        
        # Check for penicillin allergy
        if 'penicillin' in patient_allergies and any(term in antibiotic_name for term in [
            'penicillin', 'amoxicillin', 'ampicillin', 'piperacillin'
        ]):
            warnings.append({
                'type': 'allergy',
                'severity': 'high',
                'message': 'PENICILLIN ALLERGY WARNING: Patient has documented penicillin allergy',
                'recommendation': 'Consider alternative non-beta-lactam antibiotic'
            })
        
        # Check for cephalosporin allergy
        if 'cephalosporin' in patient_allergies and any(term in antibiotic_name for term in [
            'cef', 'cephalexin', 'ceftriaxone', 'cefepime'
        ]):
            warnings.append({
                'type': 'allergy',
                'severity': 'high',
                'message': 'CEPHALOSPORIN ALLERGY WARNING: Patient has documented cephalosporin allergy',
                'recommendation': 'Consider alternative antibiotic class'
            })
        
        # Check for fluoroquinolone allergy
        if any(term in patient_allergies for term in ['fluoroquinolone', 'quinolone']) and any(term in antibiotic_name for term in [
            'ciprofloxacin', 'levofloxacin', 'moxifloxacin'
        ]):
            warnings.append({
                'type': 'allergy',
                'severity': 'high',
                'message': 'FLUOROQUINOLONE ALLERGY WARNING: Patient has documented fluoroquinolone allergy',
                'recommendation': 'Consider alternative antibiotic class'
            })
        
        return warnings if warnings else None
    
    @staticmethod
    def _assess_current_antibiotic_appropriateness(best_match, patient):
        """
        Assess if the current antibiotic is appropriate for the patient's condition
        """
        if not best_match:
            return {
                'status': 'unknown',
                'message': 'Cannot assess appropriateness - antibiotic not found in database',
                'recommendations': []
            }
        
        antibiotic_obj = best_match.get('antibiotic')
        recommendations = []
        issues = []
        
        # Check CrCl appropriateness
        if hasattr(patient, 'cockcroft_gault_crcl') and patient.cockcroft_gault_crcl:
            patient_crcl = float(patient.cockcroft_gault_crcl)
            # Check using crcl_min and crcl_max
            if antibiotic_obj.crcl_min is not None and antibiotic_obj.crcl_max is not None:
                if not (antibiotic_obj.crcl_min <= patient_crcl <= antibiotic_obj.crcl_max):
                    issues.append('Dose may need adjustment for current kidney function')
                    recommendations.append('Consider dose adjustment based on CrCl')
        
        # Check pathogen coverage using pathogens ManyToMany field
        if hasattr(patient, 'pathogen') and patient.pathogen and antibiotic_obj.pathogens.exists():
            pathogen_names = list(antibiotic_obj.pathogens.values_list('name', flat=True))
            if not any(p.lower() in patient.pathogen.lower() for p in pathogen_names):
                issues.append('May have limited effectiveness against identified pathogen')
                recommendations.append('Consider pathogen-specific therapy')
        
        # Check infection type appropriateness using condition field
        if hasattr(patient, 'diagnosis1') and patient.diagnosis1 and hasattr(antibiotic_obj, 'condition') and antibiotic_obj.condition:
            if patient.diagnosis1.lower() not in antibiotic_obj.condition.name.lower():
                issues.append('May not be optimal for current infection type')
                recommendations.append('Consider infection-specific therapy')
        
        # Determine overall status
        if not issues:
            status = 'appropriate'
            message = 'Current antibiotic appears appropriate for patient condition'
        elif len(issues) == 1:
            status = 'needs_review'
            message = f'Minor concern: {issues[0]}'
        else:
            status = 'inappropriate'
            message = f'Multiple concerns identified: {"; ".join(issues)}'
        
        return {
            'status': status,
            'message': message,
            'issues': issues,
            'recommendations': recommendations
        }
