# Elite Command API with Reflective Vault

A comprehensive Flask-based API for data ingestion, psychological analysis, and human signal intelligence with deployment-ready configuration.

## 🚀 Quick Deployment

This application is now configured with safe placeholder values to prevent deployment halts. You can deploy immediately and update configuration later.

### Option 1: Local Docker Deployment (Fastest)

```bash
# Clone or extract the application
cd elite_command_api

# Run the deployment script
./deploy.sh
```

The application will be available at `http://localhost:5000`

### Option 2: Manual Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🌐 Recommended Cloud Deployment Platforms

### 1. **Railway** (FASTEST - Recommended)
- **Deployment time**: 2-3 minutes
- **Why**: Zero-config deployments, automatic HTTPS, built-in monitoring
- **Steps**:
  1. Push code to GitHub
  2. Connect Railway to your GitHub repo
  3. Deploy automatically
- **URL**: https://railway.app
- **Cost**: Free tier available, $5/month for production

### 2. **Render**
- **Deployment time**: 3-5 minutes  
- **Why**: Simple, automatic deployments from Git, free SSL
- **Steps**:
  1. Push code to GitHub
  2. Create new Web Service on Render
  3. Connect your repo and deploy
- **URL**: https://render.com
- **Cost**: Free tier available, $7/month for production

### 3. **Heroku**
- **Deployment time**: 5-10 minutes
- **Why**: Mature platform, extensive add-ons
- **Steps**:
  1. Install Heroku CLI
  2. `heroku create your-app-name`
  3. `git push heroku main`
- **URL**: https://heroku.com
- **Cost**: $7/month minimum

### 4. **DigitalOcean App Platform**
- **Deployment time**: 5-10 minutes
- **Why**: Good performance, competitive pricing
- **URL**: https://digitalocean.com/products/app-platform
- **Cost**: $5/month minimum

## 📋 Pre-Deployment Checklist

✅ **Ready to deploy** - All items below have safe defaults:

- [x] Environment variables configured with placeholders
- [x] Database configured (SQLite default)
- [x] Secret keys set (placeholder values)
- [x] CORS enabled for all origins
- [x] Error handling for missing API keys
- [x] Docker configuration ready
- [x] Health check endpoint available

## 🔧 Configuration

### Environment Variables

The application uses the following environment variables (all have safe defaults):

```bash
# Required (has placeholder defaults)
SECRET_KEY=placeholder_secret_key_change_in_production_12345
WORDSMIMIR_API_KEY=placeholder_wordsmimir_api_key_replace_with_real_key

# Optional (safe defaults)
DATABASE_URL=sqlite:///src/database/app.db
FLASK_ENV=production
CORS_ORIGINS=*
UPLOAD_FOLDER=/tmp/elite_command_uploads
LOG_LEVEL=INFO
```

### Post-Deployment Configuration

After deployment, update these values in your platform's environment variables:

1. **SECRET_KEY**: Generate a secure random key
2. **WORDSMIMIR_API_KEY**: Replace with your actual API key
3. **DATABASE_URL**: Configure external database if needed

## 🏗️ Architecture

- **Framework**: Flask with SQLAlchemy
- **Database**: SQLite (default) / PostgreSQL (production)
- **Features**:
  - Data ingestion and normalization
  - Psychological analysis
  - Multimedia processing
  - Human signal intelligence
  - Reflective vault system
  - API security and monitoring

## 📊 API Endpoints

- **Health Check**: `/api/health`
- **API Info**: `/api/info`
- **Psychological Analysis**: `/api/psychological/*`
- **Multimedia Processing**: `/api/multimedia/*`
- **Data Ingestion**: `/api/ingestion/*`
- **Intelligence Layer**: `/api/intelligence/*`

## 🔒 Security Features

- API rate limiting
- CORS configuration
- Input validation
- Error handling
- Audit logging
- Security monitoring

## 📈 Monitoring

- Health check endpoint: `/api/health`
- Metrics endpoint: `/metrics`
- Comprehensive logging
- Error tracking ready (Sentry compatible)

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.template .env

# Run the application
python src/main.py
```

### Testing

```bash
# Test the health endpoint
curl http://localhost:5000/api/health

# Test with Docker
docker-compose up --build
```

## 📝 Deployment Notes

- The application is configured to run on port 5000
- SQLite database will be created automatically
- Upload directory will be created automatically
- All services have graceful error handling for missing configurations
- Placeholder values prevent deployment failures

## 🆘 Troubleshooting

### Common Issues

1. **Port already in use**: Change port in docker-compose.yml
2. **Permission denied**: Ensure Docker has proper permissions
3. **Database errors**: Check if database directory is writable

### Logs

```bash
# Docker logs
docker-compose logs -f

# Application logs
tail -f logs/elite_command.log
```

## 📞 Support

For deployment issues or questions:
1. Check the health endpoint: `/api/health`
2. Review application logs
3. Verify environment variables are set correctly

---

**Ready to deploy!** 🚀 Choose your preferred platform and deploy in minutes.

