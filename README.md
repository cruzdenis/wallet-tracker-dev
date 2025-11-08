# 💼 Wallet Tracker - Multi-Wallet Portfolio Monitor

Monitor your cryptocurrency portfolio across multiple wallets with automatic balance tracking, protocol breakdown, and historical data analysis.

![Wallet Tracker](https://img.shields.io/badge/Status-Production%20Ready-success)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-green)
![React](https://img.shields.io/badge/React-18-61dafb)

---

## ✨ Features

### 🔐 Multi-User System
- **Admin Panel** - Full control over users and wallets
- **User Management** - Create users with granular permissions
- **Wallet Permissions** - Control which users can view which wallets

### 💰 Wallet Tracking
- **Multi-Wallet Support** - Track unlimited wallets
- **Automatic Sync** - Configurable sync intervals (default: 12 hours)
- **Manual Sync** - Force sync anytime
- **Octav.fi Integration** - Real-time balance data from multiple chains

### 📊 Analytics & Visualization
- **Dashboard Overview** - Total net worth, wallet count, average balance
- **Balance History** - 30-day historical charts
- **Protocol Breakdown** - See where your funds are (DeFi protocols)
- **Token Breakdown** - Top tokens by value
- **Wallet Comparison** - Compare balances across wallets

### ⚙️ Configuration
- **API Key Management** - Secure Octav.fi API configuration
- **Sync Interval** - Customize tracking frequency
- **User Permissions** - Fine-grained access control

---

## 🚀 Quick Deploy to Railway

### Prerequisites
- GitHub account
- Railway account (free - $5 credit/month)
- Octav.fi API key

### Steps

1. **Fork or Clone this Repository**
   ```bash
   git clone https://github.com/your-username/wallet-tracker.git
   ```

2. **Push to Your GitHub**
   ```bash
   cd wallet-tracker
   git remote set-url origin https://github.com/YOUR-USERNAME/wallet-tracker.git
   git push -u origin main
   ```

3. **Deploy on Railway**
   - Go to [Railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Add PostgreSQL: Click "+ New" → "Database" → "PostgreSQL"
   - Add environment variable: `SECRET_KEY=your-random-secret-key`
   - Generate domain: Settings → Networking → "Generate Domain"

4. **Access Your App**
   - Wait for deployment to complete (~3 minutes)
   - Access the generated URL
   - Login: `admin` / `admin123`
   - Go to Settings and add your Octav.fi API key

**📖 Detailed Guide:** See [RAILWAY_DEPLOYMENT_GUIDE.md](./RAILWAY_DEPLOYMENT_GUIDE.md)

---

## 🏗️ Tech Stack

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - ORM for database management
- **PostgreSQL** - Production database (SQLite for development)
- **APScheduler** - Background job scheduling
- **Flask-Login** - User authentication
- **Octav.fi API** - Blockchain data provider

### Frontend
- **React** - UI framework
- **Vite** - Build tool
- **Recharts** - Data visualization
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components

---

## 📁 Project Structure

```
wallet_tracker/
├── src/
│   ├── main.py              # Flask application entry point
│   ├── models/
│   │   └── models.py        # Database models
│   ├── routes/
│   │   ├── auth.py          # Authentication routes
│   │   ├── wallets.py       # Wallet management routes
│   │   ├── admin.py         # Admin panel routes
│   │   └── settings.py      # Settings routes
│   ├── services/
│   │   └── octav_service.py # Octav.fi API integration
│   ├── scheduler.py         # Background sync jobs
│   └── static/              # React frontend (built)
├── requirements.txt         # Python dependencies
├── Procfile                 # Railway start command
├── railway.json             # Railway configuration
└── README.md               # This file
```

---

## 🔧 Local Development

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/wallet-tracker.git
   cd wallet-tracker
   ```

2. **Create virtual environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python src/main.py
   ```

5. **Access locally**
   - Open http://localhost:5000
   - Login: `admin` / `admin123`

### Frontend Development

The frontend is pre-built and included in `src/static/`. To modify:

1. Navigate to frontend source (not included in this package)
2. Make changes
3. Build: `npm run build`
4. Copy `dist/` to `src/static/`

---

## 🔐 Security

### Default Credentials
**⚠️ IMPORTANT:** Change these after first login!
- Username: `admin`
- Password: `admin123`

### Environment Variables
Never commit sensitive data. Use environment variables:
- `SECRET_KEY` - Flask secret key (generate random)
- `DATABASE_URL` - Database connection (auto-set by Railway)
- API keys should be configured via Settings page

### Recommendations
- Use strong passwords
- Enable HTTPS (automatic on Railway)
- Regularly backup database
- Monitor access logs
- Keep dependencies updated

---

## 📊 Database Schema

### Tables
- **User** - User accounts and authentication
- **Wallet** - Tracked wallet addresses
- **WalletPermission** - User-wallet access control
- **BalanceHistory** - Historical balance snapshots
- **ProtocolBalance** - Protocol-level breakdown
- **TokenBalance** - Token-level breakdown
- **AppSettings** - Application configuration

---

## 🔄 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/change-password` - Change password

### Wallets
- `GET /api/wallets/` - List accessible wallets
- `GET /api/wallets/<id>/` - Get wallet details
- `GET /api/wallets/<id>/balance-history/` - Get balance history
- `GET /api/wallets/<id>/protocols/` - Get protocol breakdown
- `GET /api/wallets/<id>/tokens/` - Get token breakdown
- `POST /api/wallets/<id>/sync/` - Trigger manual sync
- `GET /api/wallets/summary/` - Portfolio summary

### Admin
- `GET /api/admin/users` - List users
- `POST /api/admin/users` - Create user
- `PUT /api/admin/users/<id>` - Update user
- `DELETE /api/admin/users/<id>` - Delete user
- `POST /api/admin/wallets` - Create wallet
- `PUT /api/admin/wallets/<id>` - Update wallet
- `DELETE /api/admin/wallets/<id>` - Delete wallet
- `GET /api/admin/permissions` - List permissions
- `POST /api/admin/permissions` - Grant permission
- `DELETE /api/admin/permissions/<id>` - Revoke permission

### Settings
- `GET /api/settings/` - Get settings
- `PUT /api/settings/` - Update settings

---

## 🐛 Troubleshooting

### Wallets not syncing
- Check Octav.fi API key in Settings
- Verify wallet address is correct
- Check logs for API errors
- Try manual sync

### Data not persisting
- Ensure PostgreSQL is connected
- Check `DATABASE_URL` environment variable
- Verify database is not read-only

### Cannot login
- Use default credentials: `admin` / `admin123`
- Clear browser cookies
- Check database connection

### Deploy failed on Railway
- Check build logs
- Verify all files are committed
- Ensure `requirements.txt` is present
- Check Python version in `runtime.txt`

---

## 📈 Roadmap

### Planned Features
- [ ] Email notifications for balance changes
- [ ] Multi-currency support (USD, EUR, BTC)
- [ ] Mobile app (React Native)
- [ ] CSV export of balance history
- [ ] Webhook support for external integrations
- [ ] Advanced analytics (ROI, P&L)
- [ ] Dark mode
- [ ] Multi-language support

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **Octav.fi** - Blockchain data provider
- **Railway** - Deployment platform
- **shadcn/ui** - UI components
- **Recharts** - Charting library

---

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the [Deployment Guide](./RAILWAY_DEPLOYMENT_GUIDE.md)
- Review [Troubleshooting](#-troubleshooting) section

---

## 🎉 Credits

Built with ❤️ by Manus AI

**Enjoy tracking your crypto portfolio!** 🚀

