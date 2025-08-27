# Frontend Structure

This frontend project is organized using a clean folder structure for better maintainability and scalability.

## Folder Structure

```
src/
├── api/                    # API related files
│   ├── base.js            # Base axios configuration
│   ├── auth.js            # Authentication API endpoints
│   ├── patients.js        # Patient management API endpoints
│   └── index.js           # API exports
├── assets/                # Static assets (images, icons, etc.)
├── components/            # Reusable UI components
│   ├── AddPatientModal.jsx # Modal for adding new patients
│   ├── DiagnosticPanel.jsx # Patient diagnostic information
│   ├── ProtectedRoute.jsx  # Route protection component
│   └── index.js           # Component exports
├── contexts/              # React contexts for state management
│   ├── AuthContext.jsx    # Authentication context
│   └── index.js           # Context exports
├── pages/                 # Main page components
│   ├── Dashboard.jsx      # Patient dashboard with recommendations
│   ├── Login.jsx          # Login page
│   ├── PatientsList.jsx   # Patients list with add/edit patient functionality
│   ├── Register.jsx       # Registration page
│   ├── AddPatient.jsx     # Full-page add patient form
│   ├── EditPatient.jsx    # Full-page edit patient form
│   └── index.js           # Page exports
├── styles/                # Global styles and CSS files
│   └── index.css          # Main stylesheet
├── utils/                 # Utility functions and helpers
├── App.jsx               # Main app component
└── main.jsx              # Application entry point
```

## Recent Changes

### EMR Integration Removed
- Removed all EMR (Electronic Medical Record) functionality
- Deleted `EMRContext.jsx` and `EMRAuthModal.jsx`
- Cleaned up all EMR-related buttons and status indicators
- Simplified authentication flow to focus on core antibiotic recommendation features

### New Features Added
- **Add Patient Modal**: New component for adding patients with comprehensive form
- **Edit Patient Page**: Full-page form for editing existing patient data
- **Modular API Structure**: Split API into separate files (auth.js, patients.js, base.js)
- **Improved Patient Management**: Focus on core patient data and antibiotic recommendations

## Import Patterns

### Using index.js exports (Recommended)

```javascript
// Import multiple components from the same folder
import { Login, Register, Dashboard } from './pages';
import { ProtectedRoute, AddPatientModal } from './components';
import { AuthProvider, useAuth } from './contexts';
import { authAPI, patientsAPI } from './api';
```

### Direct imports (Alternative)

```javascript
// Direct imports when you need specific files
import Login from './pages/Login';
import { useAuth } from './contexts/AuthContext';
import { patientsAPI } from './api/patients';
```

## API Structure

The API layer is now modular and organized by feature:

- **base.js**: Core axios configuration with interceptors
- **auth.js**: Authentication related endpoints and helper functions
- **patients.js**: Patient data management endpoints
- **index.js**: Centralized exports for all API modules

## Context Usage

- **AuthContext**: Manages user authentication state and login/logout functionality

## Key Features

1. **Patient List Management**: View all patients with search functionality
2. **Add New Patients**: Comprehensive form for adding patient data
3. **Edit Patients**: Full-page form for updating existing patient information
4. **Patient Dashboard**: Detailed view with antibiotic recommendations
5. **Antibiotic Recommendations**: AI-powered suggestions based on patient data
6. **Search & Filter**: Find patients quickly by name or other criteria

## Best Practices

1. **Components**: Keep components small and focused on a single responsibility
2. **Pages**: Represent full page views and compose multiple components
3. **API**: Modular API structure with separate files for different domains
4. **Contexts**: Use for app-wide state that multiple components need
5. **Styles**: Keep global styles in the styles folder, component-specific styles can be co-located

## Getting Started

All imports have been updated to use the new structure. The application focuses on core antibiotic recommendation functionality without EMR integration complexity.
