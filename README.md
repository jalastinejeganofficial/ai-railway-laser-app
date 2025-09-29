# 🚄 AI Railway Laser QR Management System

A sophisticated Flask web application for managing railway track fittings through QR code scanning, with AI-powered analysis and reporting capabilities.

## ✨ Features

### 🎯 Core Functionality
- **QR Code Scanning**: Real-time camera scanning and image upload support
- **Track Fitting Management**: Complete CRUD operations for railway components
- **Warranty Tracking**: Automatic warranty expiration monitoring
- **AI-Powered Analysis**: Intelligent inspection reports and recommendations
- **User Authentication**: Role-based access control (Admin/User)

### 🤖 AI Capabilities
- **Smart Chat Assistant**: Natural language queries about inspection data
- **Automated Reports**: AI-generated comprehensive system analysis
- **Maintenance Recommendations**: Intelligent suggestions based on data patterns
- **Warranty Analytics**: Proactive identification of expiring items

### 📊 Reporting & Analytics
- **Dashboard Overview**: Real-time system statistics
- **CSV Export**: Data export for external analysis
- **Replacement Reports**: Automated reports for expired warranty items
- **System Health Scoring**: Overall maintenance status assessment

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: Supabase (PostgreSQL)
- **AI Integration**: OpenRouter API with DeepSeek model
- **Authentication**: Flask-Login
- **QR Processing**: pyzbar + Pillow
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Deployment**: Python WSGI

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- Supabase account
- OpenRouter API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jalastinejeganofficial/ai-railway-laser-app.git
   cd ai-railway-laser-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup**
   Create a `.env` file with:
   ```env
   SUPABASE_KEY=your_supabase_anon_key
   FLASK_SECRET_KEY=your_secret_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key
   ```

5. **Database Setup**
   Create these tables in your Supabase dashboard:
   
   **users table:**
   ```sql
   CREATE TABLE users (
     id BIGSERIAL PRIMARY KEY,
     username TEXT UNIQUE NOT NULL,
     password TEXT NOT NULL,
     role TEXT NOT NULL DEFAULT 'user'
   );
   ```
   
   **track_fittings table:**
   ```sql
   CREATE TABLE track_fittings (
     id BIGSERIAL PRIMARY KEY,
     item TEXT NOT NULL,
     vendor TEXT NOT NULL,
     lot TEXT UNIQUE NOT NULL,
     supply_date DATE NOT NULL,
     warranty TEXT NOT NULL,
     inspection_status TEXT DEFAULT 'Pending',
     location TEXT NOT NULL,
     created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```
   
   **replacement_reports table:**
   ```sql
   CREATE TABLE replacement_reports (
     id BIGSERIAL PRIMARY KEY,
     lot TEXT NOT NULL,
     item TEXT NOT NULL,
     vendor TEXT NOT NULL,
     expired_on DATE NOT NULL,
     report TEXT NOT NULL,
     status TEXT DEFAULT 'Pending',
     created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   - Open http://localhost:5000
   - Default credentials:
     - Admin: `admin` / `admin123`
     - User: `user` / `user123`

## 📱 User Roles

### 👨‍💼 Admin Features
- View and manage all QR records
- Access AI chat assistant
- Generate comprehensive reports
- Export data to CSV
- Manage user accounts
- System analytics dashboard

### 👤 User Features
- Scan QR codes (camera/upload)
- View item details and warranty status
- Generate replacement reports
- Access item history

## 🎨 Screenshots

### Dashboard Overview
Modern railway-themed interface with real-time statistics and animated elements.

### QR Scanning Interface
Intuitive camera scanning with fallback image upload functionality.

### AI Chat Assistant
Natural language interface for querying inspection data and getting recommendations.

## 🔧 Configuration

### Environment Variables
- `SUPABASE_KEY`: Your Supabase anonymous key
- `FLASK_SECRET_KEY`: Flask session secret key
- `OPENROUTER_API_KEY`: API key for AI functionality

### Database Configuration
The application uses Supabase PostgreSQL with automatic connection handling and error recovery.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Supabase** for the robust database infrastructure
- **OpenRouter** for AI integration capabilities
- **Railway Industry** for inspiring the design and functionality
- **Open Source Community** for the excellent libraries used

## 📞 Support

For support, email [your-email] or create an issue in this repository.

---

**Built with ❤️ for Railway Maintenance Excellence** 🚄✨