# Docker Deployment Summary

## ✅ What's New

Your GNUBOARD6 project is now configured for **zero-configuration Docker deployment**!

### Key Changes

1. **`.env` file is packaged in the Docker image**
   - Configure once on your local machine
   - Build the image with your settings
   - Deploy anywhere without additional configuration

2. **Simplified deployment**
   - No need to create `.env` on the server
   - Just pull and run the container
   - Application works immediately

3. **Flexible configuration**
   - Use packaged `.env` from image (default)
   - Or mount custom `.env` to override settings

## Quick Deployment

### On macOS (One-time setup)

```bash
cd /Users/trieupham/Projects/gnuboard/g6

# 1. Configure .env (will be included in image)
cp example.env .env
nano .env  # Edit your database and settings

# 2. Edit and run build script
nano build-and-push.sh  # Set your ACR name
chmod +x build-and-push.sh
./build-and-push.sh
```

### On Ubuntu Server (Every deployment)

```bash
# 1. Create directories
mkdir -p ~/gnuboard6/data && cd ~/gnuboard6

# 2. Pull and run
docker login <your-acr>.azurecr.io
docker pull <your-acr>.azurecr.io/gnuboard6:latest
docker run -d --name gnuboard6 --restart unless-stopped \
  -p 8000:8000 -v ~/gnuboard6/data:/app/data \
  <your-acr>.azurecr.io/gnuboard6:latest

# 3. Access
# Open http://your-server-ip:8000
```

That's it! No `.env` configuration needed on the server.

## File Changes

### Modified Files

1. **`main.py`** (lines 104-106)
   - Disabled automatic redirect to installer when `.env` is missing
   - Application now expects `.env` to exist (either in image or mounted)

2. **`Dockerfile`**
   - Added logic to include `.env` file in the image
   - Falls back to `example.env` if `.env` doesn't exist during build
   - Multi-stage build for optimized image size

3. **`.dockerignore`**
   - Removed `.env` from ignore list
   - Now `.env` is included in Docker builds

4. **`build-and-push.sh`**
   - Added check for `.env` file before building
   - Warns if `.env` is missing

5. **`server-deploy.sh`**
   - Simplified deployment (no `.env` creation)
   - Supports optional `.env` override

### New Files

- ✅ `Dockerfile` - Production-ready Docker image
- ✅ `.dockerignore` - Build optimization
- ✅ `docker-compose.yml` - Alternative deployment method
- ✅ `build-and-push.sh` - Automated build script (macOS)
- ✅ `server-deploy.sh` - Automated deploy script (Ubuntu)
- ✅ `AZURE_DEPLOYMENT.md` - Complete deployment guide
- ✅ `QUICK_START.md` - Quick reference
- ✅ `DOCKER_CHANGES.md` - Detailed changes log
- ✅ `DEPLOYMENT_SUMMARY.md` - This file

## How It Works

### Build Process

```
1. Configure .env on macOS
2. Build Docker image
   ├─ Copies all application code
   ├─ Includes .env file (or uses example.env)
   └─ Creates optimized production image
3. Push to Azure Container Registry
```

### Deployment Process

```
1. Pull image from ACR
2. Run container
   ├─ Uses .env from image
   ├─ Mounts data directory for persistence
   └─ Application starts immediately
3. Access application
```

## Configuration Options

### Option 1: Use Image Configuration (Recommended)

```bash
# Simple - uses .env packaged in image
docker run -d --name gnuboard6 --restart unless-stopped \
  -p 8000:8000 -v ~/gnuboard6/data:/app/data \
  <your-acr>.azurecr.io/gnuboard6:latest
```

**Pros:**
- Zero configuration on server
- Consistent across deployments
- Fastest deployment

**Cons:**
- Need to rebuild image to change settings
- Same configuration for all deployments

### Option 2: Override with Custom .env

```bash
# Create custom .env on server
nano ~/gnuboard6/.env

# Run with override
docker run -d --name gnuboard6 --restart unless-stopped \
  -p 8000:8000 \
  -v ~/gnuboard6/data:/app/data \
  -v ~/gnuboard6/.env:/app/.env:ro \
  <your-acr>.azurecr.io/gnuboard6:latest
```

**Pros:**
- Different settings per deployment
- No rebuild needed to change config
- Useful for dev/staging/production

**Cons:**
- Need to manage .env on each server
- More setup steps

## Update Workflow

### Update Application Code

```bash
# On macOS
cd /Users/trieupham/Projects/gnuboard/g6
git pull  # or make your changes
./build-and-push.sh

# On Ubuntu Server
docker pull <your-acr>.azurecr.io/gnuboard6:latest
docker stop gnuboard6 && docker rm gnuboard6
docker run -d --name gnuboard6 --restart unless-stopped \
  -p 8000:8000 -v ~/gnuboard6/data:/app/data \
  <your-acr>.azurecr.io/gnuboard6:latest
```

### Update Configuration Only

**If using image configuration:**
```bash
# On macOS - edit .env and rebuild
nano .env
./build-and-push.sh

# On Ubuntu Server - pull and restart
docker pull <your-acr>.azurecr.io/gnuboard6:latest
docker restart gnuboard6
```

**If using .env override:**
```bash
# On Ubuntu Server - just edit and restart
nano ~/gnuboard6/.env
docker restart gnuboard6
```

## Database Setup

The `.env` file in your image should have database configured. Options:

### SQLite (Simplest)
```bash
DB_ENGINE=sqlite
```
- No external database needed
- Database file stored in `/app/data/`
- Backed up with data directory

### MySQL
```bash
DB_ENGINE=mysql
DB_HOST=your-mysql-host
DB_PORT=3306
DB_USER=gnuboard6
DB_PASSWORD=your-password
DB_NAME=gnuboard6
```

### PostgreSQL
```bash
DB_ENGINE=postgresql
DB_HOST=your-postgres-host
DB_PORT=5432
DB_USER=gnuboard6
DB_PASSWORD=your-password
DB_NAME=gnuboard6
```

## Security Notes

### ⚠️ Important

1. **Never commit `.env` to git**
   - Contains sensitive credentials
   - Already in `.gitignore`

2. **Secure your Docker image**
   - `.env` is inside the image
   - Protect access to your ACR
   - Use Azure RBAC for access control

3. **Rotate credentials regularly**
   - Database passwords
   - ACR access keys
   - API keys in `.env`

### Best Practices

1. **Use different `.env` for different environments**
   ```bash
   # Development
   .env.dev
   
   # Staging
   .env.staging
   
   # Production
   .env.production
   ```

2. **Build separate images**
   ```bash
   # Build for production
   cp .env.production .env
   docker build -t gnuboard6:prod .
   docker tag gnuboard6:prod <acr>.azurecr.io/gnuboard6:prod
   
   # Build for staging
   cp .env.staging .env
   docker build -t gnuboard6:staging .
   docker tag gnuboard6:staging <acr>.azurecr.io/gnuboard6:staging
   ```

3. **Use environment-specific tags**
   ```bash
   # Production
   <acr>.azurecr.io/gnuboard6:prod
   <acr>.azurecr.io/gnuboard6:v1.0.0
   
   # Staging
   <acr>.azurecr.io/gnuboard6:staging
   <acr>.azurecr.io/gnuboard6:latest
   ```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs gnuboard6

# Common issues:
# 1. Database connection failed
# 2. Invalid .env configuration
# 3. Port already in use
```

### Need to change configuration

```bash
# Option 1: Rebuild image with new .env
# On macOS
nano .env
./build-and-push.sh

# Option 2: Use .env override
# On server
nano ~/gnuboard6/.env
docker restart gnuboard6
```

### Database errors

```bash
# Check .env in running container
docker exec gnuboard6 cat /app/.env

# Test database connection
docker exec -it gnuboard6 bash
# Inside container, test connection
```

## Monitoring

```bash
# Container status
docker ps
docker stats gnuboard6

# Application logs
docker logs -f gnuboard6
docker logs --tail 100 gnuboard6

# Health check
docker inspect --format='{{.State.Health.Status}}' gnuboard6
```

## Backup

```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz ~/gnuboard6/data

# Backup includes:
# - Uploaded files
# - SQLite database (if used)
# - Any runtime data
```

## Support

For detailed instructions, see:
- **`QUICK_START.md`** - Quick reference guide
- **`AZURE_DEPLOYMENT.md`** - Complete deployment guide
- **`DOCKER_CHANGES.md`** - Detailed technical changes

For GNUBOARD6 support:
- Community: https://sir.kr/main/g6
- Demo: https://g6.demo.sir.kr/
- GitHub: https://github.com/gnuboard/g6
