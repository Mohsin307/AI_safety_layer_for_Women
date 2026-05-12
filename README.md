# AI Safety Layer for Women

An intelligent, proactive women safety platform that automatically detects threats using audio-visual data, evaluates contextual risk, and triggers emergency responses without manual intervention while preserving user privacy.

## 🎯 Overview

This system provides a comprehensive safety solution with:

- **Automatic Threat Detection**: AI-powered audio and visual threat recognition
- **Real-time Risk Assessment**: Dynamic risk scoring based on location, time, and behavior
- **Emergency Response**: Automated SOS, evidence capture, and authority alerts
- **Community Safety Network**: Crowdsourced safety ratings and volunteer guardians
- **Privacy-First Design**: On-device processing and encrypted communications

## 🏗️ Architecture

```
AI_safety_layer_for_Women/
├── ai_modules/                 # AI/ML Components
│   ├── audio_detection/        # Audio threat detection (CNN-LSTM)
│   ├── visual_detection/       # Visual threat recognition (YOLO)
│   ├── risk_assessment/        # Contextual risk scoring
│   ├── emergency_response/     # Emergency orchestration
│   └── community/              # Community safety features
├── backend/                    # FastAPI Backend
│   ├── api/                    # REST API routes
│   │   ├── routes/             # Endpoint handlers
│   │   ├── schemas.py          # Pydantic models
│   │   └── auth.py             # Authentication
│   ├── database/               # Database models
│   └── main.py                 # Application entry
├── config/                     # Configuration
├── models/                     # ML model weights
├── tests/                      # Test suite
└── docs/                       # Documentation
```

## Smart Architecture
Mobile App / Smart Device
          ↓
      FastAPI Backend
          ↓
     AI Detection Modules
   ├── Audio Detection
   ├── Visual Detection
   ├── Risk Assessment
          ↓
 Emergency Response Engine
          ↓
 SOS + Alerts + Evidence
 
## 🚀 Features

### Audio Threat Detection
- Detects: Screams, cries for help, aggressive voices, glass breaking, gunshots
- CNN-LSTM architecture with MFCC features
- >95% accuracy with <500ms latency
- Multi-language support

### Visual Threat Recognition
- Weapon detection (knives, guns, bats)
- Aggressive gesture recognition
- Stalking behavior detection
- Low-light image enhancement
- Pose-based threat identification

### Contextual Risk Assessment
- Location-based risk scoring
- Time-of-day analysis
- Crime statistics integration
- Behavioral anomaly detection
- Dynamic risk levels (Low, Medium, High, Critical)

### Emergency Response
- Silent SOS activation
- Live location sharing
- Audio/video evidence capture
- Automated police and helpline alerts
- Fake call/message generation

### Community Safety
- Crowdsourced safety ratings
- Verified safe zones
- Volunteer guardian network
- Anonymous incident reporting

## 📋 Requirements

- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- CUDA-capable GPU (recommended)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/AI_safety_layer_for_Women.git
cd AI_safety_layer_for_Women
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Initialize Database
```bash
# Start PostgreSQL and Redis
# Then run migrations
alembic upgrade head
```

### 6. Download Model Weights
```bash
python scripts/download_models.py
```

### 7. Run the Application
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 API Documentation

Once running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | User authentication |
| `/api/v1/users/register` | POST | User registration |
| `/api/v1/emergency/trigger` | POST | Trigger emergency SOS |
| `/api/v1/safety/assess-risk` | POST | Get risk assessment |
| `/api/v1/safety/safe-zones` | GET | Find nearby safe zones |
| `/ws` | WebSocket | Real-time updates |

## 🔒 Security

- JWT-based authentication
- End-to-end encryption for evidence
- On-device AI processing for privacy
- Secure evidence storage with tamper-proof logs
- GDPR-compliant data handling

## 📱 Mobile Integration

The backend API supports integration with:
- Flutter / React Native apps
- Smartwatch applications
- IoT safety devices

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## 📊 Performance Targets

| Metric | Target |
|--------|--------|
| Threat Detection Accuracy | ≥95% |
| Inference Latency | <500ms |
| False Positive Rate | <5% |
| Response Time Reduction | 15min → 3min |
| System Availability | 99.9% |

## 🗺️ Roadmap

- [ ] Predictive crime hotspot analysis
- [ ] Drone-assisted emergency response
- [ ] AR-based safety navigation
- [ ] Mental health AI support
- [ ] Child and elderly safety extensions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- TensorFlow and PyTorch teams
- Ultralytics YOLOv8
- MediaPipe
- FastAPI

## 📞 Emergency Numbers

- Women Helpline: **1091**
- Police: **100**
- Emergency: **112**
- Ambulance: **108**

---

**Built with ❤️ for women's safety**
