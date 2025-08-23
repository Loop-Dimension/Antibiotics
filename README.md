# Medical EMR System with Authentication

A complete medical Electronic Medical Records system with authentication, built with Django REST Framework backend and React frontend.

## Project Structure

### Backend (`backend/`)
```
backend/
├── medical/                    # Django project settings
│   ├── settings.py            # Database config, CORS, authentication settings
│   └── urls.py               # Main URL routing
├── patients/                 # Patient management app
│   ├── models.py            # Patient, CultureTest, Medication models
│   ├── views.py             # API views for patient data
│   ├── serializers.py       # DRF serializers
│   └── management/commands/ # Data import commands
├── authentication/          # Authentication app
│   ├── views.py            # Login, register, logout, profile views
│   └── urls.py             # Auth endpoint routing
├── manage.py               # Django management script
└── sheet.csv              # Patient data (40 records imported)
```

### Frontend (`frontend/src/`)
```
src/
├── App.jsx                 # Main app with routing
├── api.js                 # API service layer and axios configuration
├── AuthContext.jsx        # Authentication context provider
├── ProtectedRoute.jsx     # Route protection component
├── Login.jsx              # Login page
├── Register.jsx           # Registration page
├── Dashboard.jsx          # Main medical dashboard (protected)
└── main.jsx              # React entry point
```

## Authentication System

### Backend Features
- **Token-based authentication** using Django Rest Framework tokens
- **User registration** with email, first name, last name
- **Login/logout** with secure token management
- **Protected API endpoints** requiring authentication
- **User profile** access

### Frontend Features
- **Context-based authentication** state management
- **Local storage** token persistence
- **Protected routes** with automatic redirects
- **Login/Register forms** with validation
- **Automatic token refresh** and error handling
- **User session management**

### API Endpoints

#### Authentication (`/api/auth/`)
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile

#### Patients (`/api/patients/`)
- `GET /api/patients/` - Get all patients (protected)
- `GET /api/patients/search/?q=<query>` - Search patients by name (limit 10, protected)
- `GET /api/patients/{id}/` - Get specific patient (protected)
- `POST /api/patients/` - Create patient (protected)
- `PUT /api/patients/{id}/` - Update patient (protected)
- `DELETE /api/patients/{id}/` - Delete patient (protected)

## Setup Instructions

### Backend Setup
1. Navigate to backend directory: `cd backend`
2. Install dependencies: `pip install django djangorestframework psycopg2-binary django-cors-headers`
3. Run migrations: `python manage.py migrate`
4. Import patient data: `python manage.py import_csv ../sheet.csv`
5. Start server: `python manage.py runserver 8000`

### Frontend Setup
1. Navigate to frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`

### Database Configuration
- **Database**: PostgreSQL
- **Name**: medical
- **User**: orange
- **Password**: 00oo00oo
- **Host**: localhost
- **Port**: 5432

## Usage

### User Registration/Login
1. Navigate to `http://localhost:5174`
2. Click "Sign up" to create new account
3. Fill registration form with username, email, password, names
4. Or use "Sign in" if account exists

### Dashboard Features
- **Smart Patient Search**: Type-ahead search with debounced API calls (300ms delay)
- **Search Results Dropdown**: Live search results with limit of 10 patients
- **Patient Selection**: Click any search result to load patient data
- **Single Patient URLs**: Direct access to individual patients via `/patient/{id}`
- **Complete Patient Display**: All medical data fields including BMI, labs, vitals
- **Medical Data Display**: Comprehensive patient information with proper formatting
- **Antibiotic Recommendations**: AI-powered treatment suggestions based on diagnosis
- **User Management**: View profile, logout functionality
- **Protected Access**: All features require authentication
- **Error Handling**: Graceful handling of non-existent patient IDs

## URL Structure and Navigation

### Available URLs
- **Main Dashboard**: `http://localhost:5174/` - Default dashboard view
- **Single Patient View**: `http://localhost:5174/patient/{id}` - Direct patient access
- **Login**: `http://localhost:5174/login` - User authentication
- **Register**: `http://localhost:5174/register` - User registration

### Patient Access Examples
- Patient 36 (Female, 83, pneumonia): `http://localhost:5174/patient/36`
- Patient 5 (Female, 55, acute pyelonephritis): `http://localhost:5174/patient/5`
- Patient 10 (Female, 81, acute pyelonephritis): `http://localhost:5174/patient/10`

### Navigation Features
- **Direct URL access**: Share or bookmark specific patient URLs
- **Search-driven navigation**: Search results automatically navigate to patient URLs
- **Error handling**: Invalid patient IDs show user-friendly error messages
- **Breadcrumb navigation**: Click dashboard title to return home

## Security Features

### Backend Security
- Token-based authentication
- CORS configuration for frontend access
- Password validation
- Protected API endpoints
- User session management

### Frontend Security
- Token stored in localStorage
- Automatic token validation
- Protected route navigation
- Session expiry handling
- Secure API communication

## Design Consistency
- Maintains exact **ImpactUs Antibiotic Advisor** design
- Korean text preservation
- Medical color scheme (red borders, warning icons)
- Professional medical interface
- Responsive layout

## Data Management
- **40+ patient records** imported from CSV
- **Medical conditions**: UTIs, pneumonia, sepsis
- **Lab values**: WBC, CRP, temperature, kidney function
- **Pathogen data**: E. coli, Klebsiella, etc.
- **Allergy management**: Drug allergy tracking
- **Treatment history**: Antibiotic recommendations

## API Structure (`api.js`)
```javascript
// Authentication API
authAPI.login(credentials)
authAPI.register(userData)
authAPI.logout()
authAPI.getProfile()

// Patients API
patientsAPI.getPatients()
patientsAPI.getPatient(id)
patientsAPI.searchPatients(query)  // New: Search with 10 result limit

// Auth Helpers
auth.getToken()
auth.setToken(token)
auth.isAuthenticated()
auth.logout()
```

## Component Structure
- **App.jsx**: Router setup with authentication provider
- **AuthContext.jsx**: Global authentication state
- **ProtectedRoute.jsx**: Route guard for authenticated users
- **Login.jsx**: User authentication form
- **Register.jsx**: User registration form
- **Dashboard.jsx**: Main medical interface with:
  - Smart search functionality (debounced, 300ms delay)
  - Live search results dropdown (max 10 results)
  - Patient data display and selection
  - Medical recommendations panel

## Testing
Backend authentication tested with included `test_auth.py` script:
```bash
cd backend
python test_auth.py
```

Search functionality tested with included `test_search.py` script:
```bash
cd backend
python test_search.py
```

### Search Functionality Testing
- Search for "Patient" → Returns 10 results (limit enforced)
- Search for specific names → Returns matching patients
- Search for non-existent patients → Returns 0 results
- Empty search → Returns 0 results
- 300ms debounce delay prevents API spam
- Live dropdown with patient details (name, age, gender, CrCl)

## Development URLs
- **Frontend**: http://localhost:5174
- **Backend API**: http://127.0.0.1:8000
- **Django Admin**: http://127.0.0.1:8000/admin
