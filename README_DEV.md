# Wallet Tracker - Development Repository

**Version**: 1.2.0 (Development)  
**Purpose**: Testing and Development  
**Production Repository**: https://github.com/cruzdenis/wallet-tracker

---

## 🎯 Purpose

This is a **development and testing repository** for the Wallet Tracker application. Use this repository to:

- Test new features before deploying to production
- Experiment with changes without affecting the live application
- Develop and debug in isolation

**⚠️ Important**: This is NOT the production repository. The live application runs from:
- **Production Repo**: https://github.com/cruzdenis/wallet-tracker
- **Production URL**: https://web-production-e48e6.up.railway.app/

---

## 🚀 Quick Start

### 1. Clone this Repository

```bash
git clone https://github.com/cruzdenis/wallet-tracker-dev.git
cd wallet-tracker-dev
```

### 2. Set Up Local Development

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your DATABASE_URL and other settings

# Run migrations
python3 migrate_quota_system.py

# Start the application
python3 src/main.py
```

### 3. Deploy to Railway (Testing)

1. Go to Railway dashboard: https://railway.app/dashboard
2. Create a new project: "wallet-tracker-dev"
3. Connect this GitHub repository
4. Add PostgreSQL database
5. Set environment variables
6. Deploy!

---

## 📦 What's Included

### Current Features (v1.2.0)

- ✅ Multi-wallet portfolio tracking
- ✅ Octav.fi API integration
- ✅ Balance history tracking
- ✅ Protocol-level balance charts
- ✅ Token breakdown visualization
- ✅ Portfolio net worth dashboard
- ✅ Automatic sync scheduler (24/7)
- ✅ **Quota System** (NEW!)
  - Investment performance tracking
  - Cash flow management
  - ROI calculations
  - Quota value charts

### Technology Stack

- **Backend**: Flask 3.1, SQLAlchemy 2.0, PostgreSQL
- **Frontend**: React 18, Tailwind CSS, Recharts
- **Deployment**: Railway with automatic HTTPS
- **Scheduler**: APScheduler for background jobs

---

## 🔧 Development Workflow

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make your changes**:
   - Edit backend code in `src/`
   - Edit frontend code in `wallet-tracker-frontend/src/`

3. **Test locally**:
   ```bash
   python3 src/main.py
   ```

4. **Build frontend** (if changed):
   ```bash
   cd wallet-tracker-frontend
   pnpm install
   pnpm run build
   cp -r dist/* ../src/static/
   ```

5. **Commit and push**:
   ```bash
   git add .
   git commit -m "Add: my new feature"
   git push origin feature/my-new-feature
   ```

### Testing in Railway

1. Push to this repository
2. Railway will automatically deploy
3. Test on the dev deployment URL
4. If everything works, merge to production repo

---

## 📁 Project Structure

```
wallet-tracker-dev/
├── src/
│   ├── main.py              # Flask application entry point
│   ├── models/
│   │   └── models.py        # Database models
│   ├── routes/
│   │   ├── auth.py          # Authentication routes
│   │   ├── wallets.py       # Wallet management routes
│   │   └── quota.py         # Quota system routes
│   ├── services/
│   │   └── octav_service.py # Octav.fi API integration
│   ├── scheduler/
│   │   └── sync_scheduler.py # Background sync jobs
│   └── static/              # Compiled React frontend
├── wallet-tracker-frontend/ # React source code
├── migrate_quota_system.py  # Database migration script
├── requirements.txt         # Python dependencies
├── Procfile                 # Railway deployment config
└── README_DEV.md           # This file
```

---

## 🔑 Environment Variables

Required environment variables for Railway deployment:

```env
# Database
DATABASE_URL=postgresql://...

# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Optional: For custom domain
RAILWAY_STATIC_URL=your-domain.com
```

---

## 🧪 Testing the Quota System

### Initialize Quotas

1. Go to wallet detail page
2. Click "Quota System" tab
3. Add initial cash flow
4. Monitor performance metrics

### Test Cash Flows

1. Add cash in (deposit)
2. Sync wallet to update net worth
3. Check quota value calculation
4. Add cash out (withdrawal)
5. Verify quota redemption

---

## 📊 Database Migrations

### Run Migrations

```bash
# For quota system (if not already run)
python3 migrate_quota_system.py
```

### Manual SQL (if needed)

See `QUOTA_SYSTEM_README.md` for manual SQL migration commands.

---

## 🔄 Syncing with Production

To sync changes from production to dev:

```bash
cd /path/to/wallet-tracker-dev
git remote add production https://github.com/cruzdenis/wallet-tracker.git
git fetch production
git merge production/main
git push origin main
```

---

## ⚠️ Important Notes

### Do NOT:
- ❌ Use production database for testing
- ❌ Push untested code to production repo
- ❌ Share dev deployment URL publicly

### Do:
- ✅ Test thoroughly before merging to production
- ✅ Use separate Railway project for dev
- ✅ Keep dev and production databases separate
- ✅ Document all changes

---

## 📞 Support

For questions or issues:
1. Check the main documentation in the production repo
2. Review `QUOTA_SYSTEM_README.md` for quota system details
3. Check Railway deployment logs for errors

---

## 🔗 Links

- **Production Repo**: https://github.com/cruzdenis/wallet-tracker
- **Dev Repo**: https://github.com/cruzdenis/wallet-tracker-dev
- **Production App**: https://web-production-e48e6.up.railway.app/
- **Railway Dashboard**: https://railway.app/dashboard

---

**Happy coding!** 🚀

**Version**: 1.2.0-dev  
**Last Updated**: October 16, 2024

