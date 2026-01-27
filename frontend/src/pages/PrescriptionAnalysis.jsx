import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientsAPI } from '../api';
import { AddPatientModal } from '../components';

const PrescriptionAnalysis = () => {
  const navigate = useNavigate();
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, exact_match, partial_match, no_match, no_recommendation
  const [sortBy, setSortBy] = useState('case_no'); // case_no, similarity_score, diagnosis
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [showAddPatientModal, setShowAddPatientModal] = useState(false);

  useEffect(() => {
    fetchAnalysis();
  }, []);

  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      const response = await patientsAPI.getPrescriptionAnalysis();
      setAnalysisData(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load prescription analysis');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'exact_match':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'partial_match':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'no_match':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'no_recommendation':
        return 'bg-gray-100 text-gray-800 border-gray-300';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'exact_match':
        return 'Exact Match';
      case 'partial_match':
        return 'Partial Match';
      case 'no_match':
        return 'No Match';
      case 'no_recommendation':
        return 'No Software Recommendation';
      default:
        return status;
    }
  };

  const filteredData = analysisData?.analysis?.filter(item => {
    if (filter === 'all') return true;
    return item.match_status === filter;
  }).sort((a, b) => {
    switch (sortBy) {
      case 'similarity_score':
        return b.similarity_score - a.similarity_score;
      case 'diagnosis':
        return a.diagnosis.localeCompare(b.diagnosis);
      case 'case_no':
      default:
        return a.case_no - b.case_no;
    }
  }) || [];

  // Pagination calculations
  const totalItems = filteredData.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedData = filteredData.slice(startIndex, endIndex);

  // Reset to page 1 when filter or sort changes
  useEffect(() => {
    setCurrentPage(1);
  }, [filter, sortBy]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Analyzing prescriptions vs software recommendations...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center text-red-600">
          <p>{error}</p>
          <button 
            onClick={fetchAnalysis}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const summary = analysisData?.summary || {};

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Prescription Analysis</h1>
            <p className="text-gray-600">
              Comparing actual prescriptions from CSV data vs software-generated recommendations
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowAddPatientModal(true)}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center gap-2"
            >
              <span>+</span> Add Patient
            </button>
            <button
              onClick={() => navigate('/patients')}
              className="bg-slate-800 text-white px-4 py-2 rounded-md hover:bg-slate-900"
            >
              ← Back to Patients
            </button>
          </div>
        </div>

        {/* Summary Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">{summary.total_patients}</div>
            <div className="text-sm text-gray-600">Total Patients</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center border-l-4 border-green-500">
            <div className="text-3xl font-bold text-green-600">{summary.exact_matches}</div>
            <div className="text-sm text-gray-600">Exact Matches</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center border-l-4 border-yellow-500">
            <div className="text-3xl font-bold text-yellow-600">{summary.partial_matches}</div>
            <div className="text-sm text-gray-600">Partial Matches</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center border-l-4 border-red-500">
            <div className="text-3xl font-bold text-red-600">{summary.no_matches}</div>
            <div className="text-sm text-gray-600">No Matches</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center border-l-4 border-gray-400">
            <div className="text-3xl font-bold text-gray-600">{summary.no_recommendations}</div>
            <div className="text-sm text-gray-600">No Software Rec.</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center border-l-4 border-blue-500">
            <div className="text-3xl font-bold text-blue-600">{summary.match_rate}%</div>
            <div className="text-sm text-gray-600">Match Rate</div>
          </div>
        </div>

        {/* Match Rate Visual */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Match Distribution</h2>
          <div className="h-8 flex rounded-lg overflow-hidden">
            <div 
              className="bg-green-500 flex items-center justify-center text-white text-xs font-medium"
              style={{ width: `${(summary.exact_matches / summary.total_patients) * 100}%` }}
            >
              {summary.exact_matches > 0 && `${Math.round((summary.exact_matches / summary.total_patients) * 100)}%`}
            </div>
            <div 
              className="bg-yellow-500 flex items-center justify-center text-white text-xs font-medium"
              style={{ width: `${(summary.partial_matches / summary.total_patients) * 100}%` }}
            >
              {summary.partial_matches > 0 && `${Math.round((summary.partial_matches / summary.total_patients) * 100)}%`}
            </div>
            <div 
              className="bg-red-500 flex items-center justify-center text-white text-xs font-medium"
              style={{ width: `${(summary.no_matches / summary.total_patients) * 100}%` }}
            >
              {summary.no_matches > 0 && `${Math.round((summary.no_matches / summary.total_patients) * 100)}%`}
            </div>
            <div 
              className="bg-gray-400 flex items-center justify-center text-white text-xs font-medium"
              style={{ width: `${(summary.no_recommendations / summary.total_patients) * 100}%` }}
            >
              {summary.no_recommendations > 0 && `${Math.round((summary.no_recommendations / summary.total_patients) * 100)}%`}
            </div>
          </div>
          <div className="flex justify-between mt-2 text-sm">
            <span className="flex items-center"><span className="w-3 h-3 bg-green-500 rounded mr-1"></span> Exact Match</span>
            <span className="flex items-center"><span className="w-3 h-3 bg-yellow-500 rounded mr-1"></span> Partial Match</span>
            <span className="flex items-center"><span className="w-3 h-3 bg-red-500 rounded mr-1"></span> No Match</span>
            <span className="flex items-center"><span className="w-3 h-3 bg-gray-400 rounded mr-1"></span> No Software Rec.</span>
          </div>
        </div>

        {/* Filters and Controls */}
        <div className="bg-white rounded-lg shadow p-4 mb-6 flex flex-wrap gap-4 items-center">
          <div>
            <label className="text-sm font-medium text-gray-700 mr-2">Filter:</label>
            <select 
              value={filter} 
              onChange={(e) => setFilter(e.target.value)}
              className="border rounded px-3 py-1.5 text-sm"
            >
              <option value="all">All ({summary.total_patients})</option>
              <option value="exact_match">Exact Match ({summary.exact_matches})</option>
              <option value="partial_match">Partial Match ({summary.partial_matches})</option>
              <option value="no_match">No Match ({summary.no_matches})</option>
              <option value="no_recommendation">No Software Recommendation ({summary.no_recommendations})</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mr-2">Sort by:</label>
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
              className="border rounded px-3 py-1.5 text-sm"
            >
              <option value="case_no">Case No.</option>
              <option value="similarity_score">Similarity Score</option>
              <option value="diagnosis">Diagnosis</option>
            </select>
          </div>
          <button
            onClick={fetchAnalysis}
            className="ml-auto px-4 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          >
            Refresh Analysis
          </button>
        </div>

        {/* Data Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Case #</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Diagnosis</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CrCl</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pathogen</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actual Prescription (CSV)</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Software Recommendations</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginatedData.map((item, index) => (
                  <tr key={item.patient_id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                      {item.case_no}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 max-w-[150px] truncate" title={item.diagnosis}>
                      {item.diagnosis}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {item.crcl ? `${item.crcl.toFixed(1)}` : 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 max-w-[120px] truncate" title={item.pathogen}>
                      {item.pathogen || 'Unknown'}
                    </td>
                    <td className="px-4 py-3 text-sm max-w-[200px]">
                      <div className="bg-blue-50 border border-blue-200 rounded px-2 py-1 text-blue-800 truncate" title={item.actual_prescription}>
                        {item.actual_prescription || 'None'}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm max-w-[250px]">
                      {item.ai_recommendations.length > 0 ? (
                        <div className="space-y-1">
                          {item.ai_recommendations.slice(0, 3).map((rec, i) => (
                            <div 
                              key={i} 
                              className={`text-xs px-2 py-0.5 rounded truncate ${
                                rec === item.best_match 
                                  ? 'bg-green-100 border border-green-300 text-green-800 font-medium' 
                                  : 'bg-gray-100 text-gray-700'
                              }`}
                              title={rec}
                            >
                              {rec}
                            </div>
                          ))}
                          {item.ai_recommendations.length > 3 && (
                            <div className="text-xs text-gray-500">+{item.ai_recommendations.length - 3} more</div>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400 italic">No recommendations</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className={`text-sm font-semibold ${
                        item.similarity_score >= 80 ? 'text-green-600' :
                        item.similarity_score >= 40 ? 'text-yellow-600' :
                        'text-gray-400'
                      }`}>
                        {item.similarity_score > 0 ? `${item.similarity_score}%` : '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(item.match_status)}`}>
                        {getStatusLabel(item.match_status)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {paginatedData.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No data matching the selected filter
            </div>
          )}
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-between bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-700">Items per page:</label>
              <select
                value={itemsPerPage}
                onChange={(e) => {
                  setItemsPerPage(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="border rounded px-2 py-1 text-sm"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className="px-3 py-1 rounded border disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                First
              </button>
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 rounded border disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                Previous
              </button>
              
              <div className="flex items-center gap-1">
                {[...Array(totalPages)].map((_, i) => {
                  const page = i + 1;
                  // Show first 2, last 2, and pages around current
                  if (
                    page === 1 ||
                    page === totalPages ||
                    (page >= currentPage - 1 && page <= currentPage + 1)
                  ) {
                    return (
                      <button
                        key={page}
                        onClick={() => setCurrentPage(page)}
                        className={`px-3 py-1 rounded border ${
                          currentPage === page
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'hover:bg-gray-100'
                        }`}
                      >
                        {page}
                      </button>
                    );
                  } else if (
                    page === currentPage - 2 ||
                    page === currentPage + 2
                  ) {
                    return <span key={page} className="px-2">...</span>;
                  }
                  return null;
                })}
              </div>

              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 rounded border disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                Next
              </button>
              <button
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className="px-3 py-1 rounded border disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                Last
              </button>
            </div>

            <div className="text-sm text-gray-700">
              Page {currentPage} of {totalPages} ({totalItems} total)
            </div>
          </div>
        )}

        {/* Summary */}
        <div className="mt-4 text-center text-sm text-gray-500">
          Showing {startIndex + 1}-{Math.min(endIndex, totalItems)} of {totalItems} filtered results ({summary.total_patients} total patients)
        </div>
      </div>

      {/* Add Patient Modal */}
      <AddPatientModal
        isOpen={showAddPatientModal}
        onClose={() => setShowAddPatientModal(false)}
        onPatientAdded={() => {
          setShowAddPatientModal(false);
          fetchAnalysis(); // Refresh the analysis data
        }}
      />
    </div>
  );
};

export default PrescriptionAnalysis;
