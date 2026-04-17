# TouristGuard 360

**Tourist Safety, Awareness, and Information System**

A comprehensive mobile application system designed to enhance tourist safety through real-time alerts, danger zone monitoring, emergency assistance, secure document storage, and transportation guidance.

---

## 🏗️ System Architecture

```
┌──────────────────────┐     HTTP/WebSocket     ┌──────────────────────────┐
│   Flutter Mobile App  │ ◄──────────────────► │    Python Flask Backend    │
│   (Tourist User)      │                       │    (localhost:5000)        │
└──────────────────────┘                        ├──────────────────────────┤
                                                 │  SQLite Database          │
                                                 │  Mock Blockchain          │
                                                 │  Encrypted File Storage   │
                                                 ├──────────────────────────┤
                                                 │  Web Admin Panel          │
                                                 │  (Police & Medical Auth)  │
                                                 └──────────────────────────┘
```

| Component            | Technology                          |
|----------------------|-------------------------------------|
| Mobile App           | Flutter (Dart)                      |
| Backend Server       | Python Flask + Flask-SocketIO       |
| Database             | SQLite                              |
| Blockchain           | Mock SHA-256 hash-chain (Python)    |
| Admin Panel          | HTML/CSS/JavaScript (served by Flask)|
| Maps                 | OpenStreetMap via flutter_map       |
| Document Encryption  | AES-256-GCM                         |

---

## 📱 Mobile App Features

### 🔐 Authentication
- Email + Password login/register
- Google Sign-In
- Multi-step registration (personal info, emergency contacts)

### 🏠 Home Page
- **Live Map** — Real-time GPS location on OpenStreetMap
- **Smart Search** — Find nearby Police Stations, Hospitals, Pharmacies, Restaurants, Hotels, Tourist Attractions, Banks
- **Map Filters** — Toggle POI icons on map by category
- **SOS Button** — One-tap emergency alert to server with location + timestamp
- **Danger Zones** — Visual danger zone overlays, automatic alerts when entering

### 🚌 Transport Page
- **Bus Search** — GPS auto-detect origin, enter destination, view routes & times
- **Train Search** — Select stations, date, view schedules & availability

### 🔔 Alerts & Notifications
- View admin-sent alerts (severe weather, landslides, nearby emergencies)
- View notifications (government announcements, road closures, events)
- Toggle alerts/notifications ON/OFF
- Search by name or location

### 📄 Documents Page
- Secure encrypted document storage (passport, visa, travel plans, bills)
- Upload via camera capture or file manager
- Supports: JPG, PNG, PDF, DOC formats
- End-to-end encryption — admin cannot view document contents

### ⚙️ Settings
- View/edit profile (name, age, country, blood group, phone, emergency contacts)
- Theme selection (Light / Dark / System Default)
- Language selection (English, Japanese, French, German)
- Server connection status + IP configuration
- Logout & Delete Account options

### 🌍 Multilingual Support
- English, Japanese, French, German
- Dynamic UI update on language change

---

## 🖥️ Admin Panel Features

### Dashboard
- View all registered users with details
- Add / Edit / Delete users
- View user document count (not content), location, alert history

### Alert & Notification Management
- Send location-based alerts with radius targeting
- Send time-bound notifications (auto-expire)
- Search and manage active alerts

### Danger Zone Management
- Add/edit/delete danger zones on interactive map
- Set zone center and radius (km)
- Zones display on both admin and user maps

### Active Tourist Monitoring
- Live map showing all active tourist locations
- Real-time danger zone entry detection
- Event logging for all safety incidents

---

## 🔗 Blockchain Integration
- Immutable SHA-256 hash-chain records for:
  - User registrations
  - SOS emergency events
  - Danger zone entry events
  - Alert dispatches
- Chain verification endpoint to detect tampering
- All security events are permanently logged

---

## 🚀 How to Run

### Prerequisites

| Requirement      | Version  | Notes                              |
|------------------|----------|------------------------------------|
| Python           | 3.10+    | For backend server                 |
| Flutter SDK      | 3.x+     | For mobile app                     |
| pip              | Latest   | Python package manager             |
| Android Emulator | Any      | Or physical Android/iOS device     |

### Step 1: Start the Backend Server

```bash
# Navigate to backend directory
cd v2/backend

# Install Python dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

The server will start on `http://localhost:5000`. The admin panel will be available at `http://localhost:5000/admin/`.

### Step 2: Start the Flutter Mobile App

```bash
# Navigate to Flutter project
cd v2/tourist_guard_app

# Install dependencies
flutter pub get

# Run on connected device or emulator
flutter run
```

### Step 3: Configure Server Connection

1. Open the app on your device/emulator
2. On the login screen, tap the server status indicator
3. Enter your PC's local IP address (e.g., `192.168.1.100`)
4. The app will connect to `http://<your-ip>:5000`

> **Note for Android Emulator**: The default server URL is `http://10.0.2.2:5000` which maps to `localhost` on your PC.

### Step 4: Access Admin Panel

Open a web browser and navigate to:
```
http://localhost:5000/admin/
```

No login is required. The admin panel provides full management capabilities for user oversight, alert dispatching, danger zone configuration, and live tourist monitoring.

---

## 📁 Project Structure

```
v2/
├── tourist_guard_app/          # Flutter mobile application
│   ├── lib/
│   │   ├── main.dart           # App entry point
│   │   ├── config/             # App config, routes, themes
│   │   ├── l10n/               # Localization (EN, JA, HI, TA)
│   │   ├── models/             # Data models
│   │   ├── services/           # API, auth, location services
│   │   ├── providers/          # State management (Provider)
│   │   ├── screens/            # UI screens (auth, home, transport, etc.)
│   │   └── widgets/            # Reusable UI components
│   └── pubspec.yaml
├── backend/                    # Python Flask API + Admin Panel
│   ├── app.py                  # Flask app entry point
│   ├── config.py               # Server configuration
│   ├── database.py             # SQLite setup & schema
│   ├── models/                 # Database models
│   ├── routes/                 # API endpoints
│   ├── services/               # Blockchain, encryption, geofencing
│   ├── admin/                  # Web admin panel (HTML/CSS/JS)
│   │   ├── templates/          # Admin HTML pages
│   │   └── static/             # CSS and JavaScript
│   └── uploads/                # Encrypted document storage
└── README.md
```

---

## 🔒 Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Authentication**: Token-based API access
- **Document Encryption**: AES-256-GCM per-user encryption
- **Blockchain Logging**: Tamper-proof event recording
- **Activity Logging**: All user actions logged with timestamps

---

## 📝 API Endpoints Summary

| Category       | Endpoint                          | Method | Description                    |
|----------------|-----------------------------------|--------|--------------------------------|
| Auth           | `/api/auth/register`              | POST   | Register new user              |
| Auth           | `/api/auth/login`                 | POST   | Login with email/password      |
| Auth           | `/api/auth/google`                | POST   | Google Sign-In                 |
| Emergency      | `/api/emergency/sos`              | POST   | Trigger SOS alert              |
| Danger Zones   | `/api/danger-zones`               | GET    | List all danger zones          |
| Transport      | `/api/transport/buses`            | GET    | Search bus routes              |
| Transport      | `/api/transport/trains`           | GET    | Search train schedules         |
| Alerts         | `/api/alerts`                     | GET    | Get active alerts              |
| Notifications  | `/api/notifications`              | GET    | Get active notifications       |
| Documents      | `/api/documents/upload`           | POST   | Upload encrypted document      |
| Documents      | `/api/documents`                  | GET    | List user's documents          |
| Blockchain     | `/api/blockchain/chain`           | GET    | View blockchain                |
| Blockchain     | `/api/blockchain/verify`          | GET    | Verify chain integrity         |
| Admin          | `/api/admin/users`                | CRUD   | Manage users                   |
| Admin          | `/api/admin/alerts`               | CRUD   | Manage alerts                  |
| Admin          | `/api/admin/danger-zones`         | CRUD   | Manage danger zones            |
| Admin          | `/api/admin/active-users`         | GET    | Get active user locations      |

---

## 📄 License

This project is developed for educational and demonstration purposes.
