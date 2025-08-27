#!/usr/bin/env python
import requests
import json

def test_clinical_api_endpoint():
    """Test the clinical recommendations API endpoint"""
    
    # Test endpoint URL - using patient 36 which we know works
    url = "http://localhost:8000/api/patients/36/clinical_recommendations/"
    
    try:
        print("🧪 Testing Clinical Recommendations API Endpoint")
        print(f"URL: {url}")
        print("-" * 50)
        
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Call Successful!")
            print(f"Patient: {data.get('patient_name')} (ID: {data.get('patient_id')})")
            print(f"Success: {data.get('success')}")
            print(f"Total matches: {data.get('total_matches', 0)}")
            
            recommendations = data.get('recommendations', [])
            print(f"Recommendations count: {len(recommendations)}")
            
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"{i}. {rec.get('antibiotic_name')} - {rec.get('dose')}")
                print(f"   Score: {rec.get('preference_score')}, Priority: {rec.get('clinical_priority')}")
                print(f"   Rationale: {rec.get('medical_rationale', 'N/A')[:100]}...")
                
            print("\n✅ Clinical API endpoint working correctly!")
            
        else:
            print(f"❌ API Call Failed!")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django is running on localhost:8000")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_clinical_api_endpoint()
