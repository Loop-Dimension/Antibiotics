import React from 'react';

const DiagnosticPanel = ({ patientData }) => {
  // Function to get diagnostic suggestions based on patient data
  const getDiagnosticSuggestions = () => {
    if (!patientData) return [];

    const suggestions = [];
    
    // Based on the pathogen and symptoms
    if (patientData.pathogen?.toLowerCase().includes('escherichia coli')) {
      suggestions.push({
        condition: 'Urinary Tract Infection',
        confidence: '95%',
        reason: 'E. coli in urine sample'
      });
      
      if (patientData.diagnosis1?.toLowerCase().includes('pyelonephritis')) {
        suggestions.push({
          condition: 'Acute Pyelonephritis',
          confidence: '90%',
          reason: 'Clinical presentation + pathogen'
        });
      }
    }

    // Based on vital signs
    if (patientData.body_temperature > 38) {
      suggestions.push({
        condition: 'Systemic Infection',
        confidence: '85%',
        reason: 'Elevated temperature'
      });
    }

    // Based on lab values
    if (patientData.wbc > 10000) {
      suggestions.push({
        condition: 'Bacterial Infection',
        confidence: '80%',
        reason: 'Elevated WBC count'
      });
    }

    if (patientData.crp > 50) {
      suggestions.push({
        condition: 'Acute Inflammatory Process',
        confidence: '85%',
        reason: 'Significantly elevated CRP'
      });
    }

    return suggestions;
  };

  const diagnosticSuggestions = getDiagnosticSuggestions();

  return (
    <div className="space-y-4">
      {diagnosticSuggestions.length > 0 ? (
        <div>
          <h4 className="font-semibold text-gray-900 mb-3">AI 진단 제안:</h4>
          <div className="space-y-2">
            {diagnosticSuggestions.map((suggestion, index) => (
              <div key={index} className="border border-gray-200 rounded p-3 text-sm">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-medium text-gray-900">{suggestion.condition}</span>
                  <span className="text-green-600 text-xs font-medium">{suggestion.confidence}</span>
                </div>
                <div className="text-gray-600 text-xs">{suggestion.reason}</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center text-gray-500 py-8">
          <div className="text-sm">병원체 및 진단 기반</div>
          <div className="text-sm">자동 질환명 검색 대기중</div>
        </div>
      )}
      
      {patientData && (
        <div className="mt-6 border-t pt-4">
          <h4 className="font-semibold text-gray-900 mb-2">현재 데이터:</h4>
          <div className="text-xs text-gray-600 space-y-1">
            <div>• 병원체: {patientData.pathogen || 'N/A'}</div>
            <div>• 검체: {patientData.sample_type || 'N/A'}</div>
            <div>• 진단: {patientData.diagnosis1 || 'N/A'}</div>
            <div>• 체온: {patientData.body_temperature || 'N/A'}°C</div>
            <div>• WBC: {patientData.wbc || 'N/A'}/μL</div>
            <div>• CRP: {patientData.crp || 'N/A'} mg/L</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiagnosticPanel;
