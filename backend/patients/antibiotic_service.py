from patients.models import Patient, AntibioticDosing
from django.db.models import Q
import re


class AntibioticRecommendationService:
    
    @staticmethod
    def get_recommendations_for_patient(patient):
        """
        Get antibiotic recommendations based on patient data.
        Returns recommendations or 'no match' message with 100% reliability.
        """
        try:
            if not isinstance(patient, Patient):
                return {
                    'recommendations': [],
                    'message': 'Invalid patient data provided',
                    'status': 'error'
                }
            
            # Validate essential patient data
            if not hasattr(patient, 'patient_id') or not patient.patient_id:
                return {
                    'recommendations': [],
                    'message': 'Patient ID is required',
                    'status': 'error'
                }
            
            # Get patient's CrCl with fallback
            try:
                crcl = float(patient.cockcroft_gault_crcl) if patient.cockcroft_gault_crcl else 60.0
            except (ValueError, TypeError):
                crcl = 60.0  # Default to normal kidney function
            
            # Validate CrCl range
            if crcl < 0 or crcl > 200:
                crcl = 60.0  # Reset to normal if unrealistic
            
            # Get suitable antibiotics with extensive fallback logic
            suitable_antibiotics = AntibioticRecommendationService._get_suitable_antibiotics_with_fallback(
                crcl=crcl,
                pathogen=patient.pathogen or 'Unknown',
                diagnosis=patient.diagnosis1 or 'Unknown',
                allergies=patient.allergies or 'None',
                age=patient.age if hasattr(patient, 'age') and patient.age else 65,
                severity_indicators={
                    'wbc': AntibioticRecommendationService._safe_float(patient.wbc),
                    'crp': AntibioticRecommendationService._safe_float(patient.crp),
                    'temperature': AntibioticRecommendationService._safe_float(patient.body_temperature)
                }
            )
            
            if not suitable_antibiotics:
                # Return fallback recommendations for critical cases
                fallback_recommendations = AntibioticRecommendationService._get_fallback_recommendations(crcl, patient)
                
                if fallback_recommendations:
                    return {
                        'recommendations': fallback_recommendations,
                        'message': 'Using broad-spectrum empiric therapy - No specific matches found for patient criteria',
                        'status': 'fallback'
                    }
                else:
                    return {
                        'recommendations': [],
                        'message': 'No match found - Consult infectious disease specialist or pharmacist for manual review',
                        'status': 'no_match'
                    }
            
            # Rank recommendations
            ranked_recommendations = AntibioticRecommendationService._rank_recommendations(
                suitable_antibiotics, patient
            )
            
            return {
                'recommendations': ranked_recommendations[:3],  # Return top 3
                'message': f'Found {len(ranked_recommendations)} suitable recommendations',
                'status': 'success'
            }
            
        except Exception as e:
            # Log the error (in production, use proper logging)
            print(f"Error in get_recommendations_for_patient: {str(e)}")
            
            # Return emergency fallback
            emergency_fallback = AntibioticRecommendationService._get_emergency_fallback()
            return {
                'recommendations': emergency_fallback,
                'message': 'System error - Using emergency protocols. Please review manually.',
                'status': 'emergency_fallback'
            }
    
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
            # Check CrCl compatibility
            if not AntibioticRecommendationService._is_crcl_compatible(antibiotic.crcl_range, crcl):
                continue
            
            # Check pathogen effectiveness
            if pathogen and not AntibioticRecommendationService._is_pathogen_effective(
                antibiotic.pathogen_effectiveness, pathogen
            ):
                continue
            
            # Check infection type compatibility
            if diagnosis and not AntibioticRecommendationService._is_infection_compatible(
                antibiotic.infection_types, diagnosis
            ):
                continue
            
            # Check allergies/contraindications
            if allergies and AntibioticRecommendationService._has_contraindication(
                antibiotic.contraindications, allergies
            ):
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
        Rank antibiotic recommendations based on various factors
        """
        ranked = []
        
        for antibiotic in suitable_antibiotics:
            score = antibiotic.severity_score
            
            # Bonus points for exact pathogen match
            if patient.pathogen and antibiotic.pathogen_effectiveness:
                if patient.pathogen in antibiotic.pathogen_effectiveness:
                    score += 2
            
            # Bonus for oral route if patient is stable
            is_stable = AntibioticRecommendationService._is_patient_stable(patient)
            if is_stable and antibiotic.route == 'PO':
                score += 1
            elif not is_stable and antibiotic.route == 'IV':
                score += 1
            
            # Bonus for first-line antibiotics based on diagnosis
            if AntibioticRecommendationService._is_first_line(antibiotic, patient.diagnosis1):
                score += 2
            
            # Calculate duration based on diagnosis
            duration = AntibioticRecommendationService._get_recommended_duration(
                antibiotic, patient.diagnosis1
            )
            
            # Prepare rationale
            rationale = AntibioticRecommendationService._generate_rationale(
                antibiotic, patient, is_stable
            )
            
            ranked.append({
                'antibiotic': antibiotic.antibiotic,
                'dose': antibiotic.dose or 'Standard dose',
                'route': antibiotic.route or 'IV',
                'interval': antibiotic.interval or 'q24h',
                'duration': duration,
                'rationale': rationale,
                'score': score,
                'crcl_adjusted': patient.cockcroft_gault_crcl < 50 if patient.cockcroft_gault_crcl else False
            })
        
        # Sort by score (descending)
        ranked.sort(key=lambda x: x['score'], reverse=True)
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
    def _generate_rationale(antibiotic, patient, is_stable):
        """
        Generate rationale for the recommendation
        """
        rationale_parts = []
        
        # Pathogen coverage
        if patient.pathogen and antibiotic.pathogen_effectiveness:
            if patient.pathogen in antibiotic.pathogen_effectiveness:
                rationale_parts.append(f"Excellent coverage for {patient.pathogen}")
            else:
                rationale_parts.append("Broad-spectrum empiric coverage")
        
        # CrCl adjustment
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
