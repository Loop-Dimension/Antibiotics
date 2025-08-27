#!/usr/bin/env python
"""
Test the clinical recommendations API endpoint with HTTP requests
"""
import requests
import json

def test_http_api():
    print("Testing Clinical Recommendations HTTP API")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000"
    
    # Access token for authentication
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU4MjQwMDE2LCJpYXQiOjE3NTU2NDgwMTYsImp0aSI6IjY4M2I5MzQ3MTlhODRiNGY4NGFiNjdmYjlmNGY5MWZmIiwidXNlcl9pZCI6IjEiLCJ1c2VybmFtZSI6Im9yYW5nZSJ9.H963kTM9O4kZS29QfD2pZ98Dh7BTZYhM1wQy5x-ME-Y"
    
    # Headers with authentication
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test with a known patient ID (36 from our previous tests)
        patient_id = 36
        
        print(f"Testing with patient {patient_id}")
        print('-' * 50)
        
        # Test the clinical recommendations endpoint
        rec_url = f"{base_url}/api/patients/{patient_id}/clinical_recommendations/"
        print(f"Calling: {rec_url}")
        
        rec_response = requests.get(rec_url, headers=headers, timeout=30)
        
        print(f"Response Status: {rec_response.status_code}")
        
        if rec_response.status_code != 200:
            print(f"Error response: {rec_response.text}")
            
            # Try the other endpoint as a fallback
            print("\nTrying antibiotic_recommendations endpoint...")
            rec_url_alt = f"{base_url}/api/patients/{patient_id}/antibiotic_recommendations/"
            rec_response = requests.get(rec_url_alt, headers=headers, timeout=30)
            print(f"Alternative Response Status: {rec_response.status_code}")
            
            if rec_response.status_code != 200:
                print(f"Alternative Error response: {rec_response.text}")
                return
        
        if rec_response.status_code == 200:
            rec_data = rec_response.json()
            
            print(f"Success: {rec_data.get('success')}")
            print(f"Total Matches: {rec_data.get('total_matches')}")
            print(f"Number of Recommendations: {len(rec_data.get('recommendations', []))}")
            
            if rec_data.get('recommendations'):
                top_rec = rec_data['recommendations'][0]
                print(f"\nTop Recommendation:")
                print(f"  Antibiotic: {top_rec.get('antibiotic')}")
                print(f"  Score: {top_rec.get('preference_score')}")
                print(f"  Route: {top_rec.get('route')}")
                print(f"  Dose: {top_rec.get('dose')}")
                
            print(f"\nFilter Steps: {len(rec_data.get('filter_steps', []))}")
            for step in rec_data.get('filter_steps', []):
                print(f"  Step {step.get('step')}: {step.get('name')} - {step.get('result')}")
                
            patient_summary = rec_data.get('patient_summary', {})
            print(f"\nMatched Condition: {patient_summary.get('matched_condition')}")
            print(f"Target Pathogens: {len(patient_summary.get('target_pathogens', []))}")
            
        else:
            print(f"Error response: {rec_response.text}")
            
        # Also test with a different patient ID to show flexibility
        print("\n" + "="*50)
        print("Testing with another patient...")
        
        # Try a few different patient IDs
        for test_id in [1, 2, 3, 5, 10]:
            rec_url2 = f"{base_url}/api/patients/{test_id}/clinical_recommendations/"
            
            try:
                rec_response2 = requests.get(rec_url2, headers=headers, timeout=10)
                if rec_response2.status_code == 200:
                    rec_data2 = rec_response2.json()
                    recs = rec_data2.get('recommendations', [])
                    print(f"Patient {test_id}: {len(recs)} recommendations")
                    if recs:
                        patient_summary2 = rec_data2.get('patient_summary', {})
                        print(f"  Condition: {patient_summary2.get('matched_condition')}")
                        print(f"  Top antibiotic: {recs[0].get('antibiotic')}")
                    break
                elif rec_response2.status_code == 404:
                    continue
                else:
                    print(f"Patient {test_id}: Error {rec_response2.status_code}")
                    
            except requests.exceptions.RequestException:
                continue
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_http_api()
