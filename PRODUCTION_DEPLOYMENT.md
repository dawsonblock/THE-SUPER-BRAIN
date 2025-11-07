# 🚀 Brain-AI Production Deployment Guide

**Version 4.5.0 - Production-Ready**

---

## 📋 **Overview**

This guide covers deploying Brain-AI to production with:
- ✅ Production-optimized builds
- ✅ Process management
- ✅ Logging and monitoring
- ✅ Security hardening
- ✅ Docker containerization
- ✅ Systemd service management

---

## 🎯 **Deployment Options**

### **Option 1: Quick Production Deploy** (Recommended for testing)
```bash
chmod +x deploy-production.sh
sudo ./deploy-production.sh
```

### **Option 2: Docker Compose** (Recommended for production)
```bash
docker-compose -f docker-compose.production.yml up -d
```

### **Option 3: Systemd Services** (Recommended for Linux servers)
```bash
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable brain-ai
sudo systemctl start brain-ai
```

---

## 🔧 **Prerequisites**

### **System Requirements**
- **OS**: Linux (Ubuntu 20.04+, CentOS 8+) or macOS
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 20GB free space
- **Network**: Open ports 80, 443, 5001, 8000

### **Software Requirements**
```bash
# Python 3.8+
python3 --version

# Node.js 16+
node --version

# Docker (optional)
docker --version
docker-compose --version

# Nginx (for reverse proxy)
nginx -v
```

### **Install Dependencies**
```bash
# Python packages
pip3 install -r brain-ai-rest-service/requirements.txt

# Node packages
cd brain-ai-gui && npm install
```

---

## 📦 **Option 1: Quick Production Deploy**

### **Step 1: Prepare Environment**
```bash
# Clone repository
git clone https://github.com/dawsonblock/THE-SUPER-BRAIN.git
cd THE-SUPER-BRAIN

# Copy production environment
cp .env.production .env

# Edit configuration
nano .env
```

### **Step 2: Build Production Assets**
```bash
# Build GUI
cd brain-ai-gui
npm run build
cd ..
```

### **Step 3: Deploy**
```bash
# Make script executable
chmod +x deploy-production.sh
chmod +x stop-production.sh

# Deploy (requires sudo for port 80)
sudo ./deploy-production.sh
```

### **Step 4: Verify Deployment**
```bash
# Check services
curl http://localhost/health
curl http://localhost:5001/healthz
curl http://localhost:8000/health

# View logs
tail -f /var/log/brain-ai-*.log
```

### **Step 5: Stop Services**
```bash
sudo ./stop-production.sh
```

---

## 🐳 **Option 2: Docker Compose Deployment**

### **Step 1: Build Images**
```bash
# Build all services
docker-compose -f docker-compose.production.yml build
```

### **Step 2: Start Services**
```bash
# Start in detached mode
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

### **Step 3: Verify**
```bash
# Check container status
docker-compose -f docker-compose.production.yml ps

# Check health
docker-compose -f docker-compose.production.yml exec api-service curl http://localhost:5001/healthz
```

### **Step 4: Stop Services**
```bash
docker-compose -f docker-compose.production.yml down
```

### **Step 5: Update**
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.production.yml up -d --build
```

---

## ⚙️ **Option 3: Systemd Services**

### **Step 1: Create User**
```bash
sudo useradd -r -s /bin/false brain-ai
```

### **Step 2: Install Application**
```bash
# Copy application
sudo mkdir -p /opt/brain-ai
sudo cp -r . /opt/brain-ai/
sudo chown -R brain-ai:brain-ai /opt/brain-ai

# Create data directory
sudo mkdir -p /opt/brain-ai/data
sudo chown brain-ai:brain-ai /opt/brain-ai/data
```

### **Step 3: Install Services**
```bash
# Copy service files
sudo cp systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable brain-ai
sudo systemctl enable brain-ai-api
sudo systemctl enable brain-ai-ocr
```

### **Step 4: Start Services**
```bash
sudo systemctl start brain-ai
```

### **Step 5: Check Status**
```bash
# Check all services
sudo systemctl status brain-ai

# Check individual services
sudo systemctl status brain-ai-api
sudo systemctl status brain-ai-ocr

# View logs
sudo journalctl -u brain-ai-api -f
```

---

## 🔒 **Security Configuration**

### **Firewall Setup**
```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5001/tcp  # API (restrict in production)
sudo ufw enable

# Firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### **SSL/TLS Setup**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### **API Key Protection**
```bash
# Enable API key requirement
export REQUIRE_API_KEY_FOR_WRITES=true

# Generate API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
echo "API_KEY=your-generated-key" >> .env
```

---

## 📊 **Monitoring & Logging**

### **Log Locations**
```
/var/log/brain-ai-ocr.log    - OCR Service logs
/var/log/brain-ai-api.log    - REST API logs
/var/log/brain-ai-gui.log    - GUI logs
```

### **View Logs**
```bash
# Real-time logs
tail -f /var/log/brain-ai-*.log

# Search logs
grep "ERROR" /var/log/brain-ai-api.log

# Rotate logs
sudo logrotate -f /etc/logrotate.d/brain-ai
```

### **Health Monitoring**
```bash
# Create monitoring script
cat > /usr/local/bin/brain-ai-health.sh << 'EOF'
#!/bin/bash
curl -f http://localhost/health || systemctl restart brain-ai
EOF

chmod +x /usr/local/bin/brain-ai-health.sh

# Add to cron (every 5 minutes)
echo "*/5 * * * * /usr/local/bin/brain-ai-health.sh" | sudo crontab -
```

---

## 🔄 **Updates & Maintenance**

### **Update Application**
```bash
# Pull latest code
cd /opt/brain-ai
git pull

# Rebuild GUI
cd brain-ai-gui
npm run build

# Restart services
sudo systemctl restart brain-ai
```

### **Backup Data**
```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/backups/brain-ai"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/brain-ai-$DATE.tar.gz \
    /opt/brain-ai/data \
    /opt/brain-ai/.env

# Keep only last 7 backups
find $BACKUP_DIR -name "brain-ai-*.tar.gz" -mtime +7 -delete
```

### **Database Maintenance**
```bash
# Vacuum database (if using SQLite)
sqlite3 /opt/brain-ai/data/facts.db "VACUUM;"

# Cleanup old cache entries
curl -X POST http://localhost:5001/admin/cleanup
```

---

## 🚨 **Troubleshooting**

### **Service Won't Start**
```bash
# Check logs
sudo journalctl -u brain-ai-api -n 50

# Check permissions
ls -la /opt/brain-ai

# Check ports
sudo netstat -tulpn | grep -E '(80|5001|8000)'
```

### **High Memory Usage**
```bash
# Check memory
free -h

# Reduce workers in .env
WORKERS=2

# Restart services
sudo systemctl restart brain-ai
```

### **Slow Response Times**
```bash
# Check system load
top

# Check API metrics
curl http://localhost:5001/metrics

# Increase workers
WORKERS=8
```

---

## 📈 **Performance Tuning**

### **Nginx Optimization**
```nginx
# In nginx.production.conf
worker_processes auto;
worker_connections 4096;
keepalive_timeout 65;
```

### **API Optimization**
```bash
# Increase workers
API_WORKERS=8

# Enable caching
CACHE_SIZE=10000

# Tune vector index
VECTOR_INDEX_SIZE=10000000
```

### **Database Optimization**
```bash
# SQLite pragmas
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
```

---

## ✅ **Production Checklist**

### **Pre-Deployment**
- [ ] All tests passing
- [ ] Production build successful
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Backup strategy in place
- [ ] Monitoring configured

### **Post-Deployment**
- [ ] All services healthy
- [ ] GUI accessible
- [ ] API responding
- [ ] Logs being written
- [ ] Metrics being collected
- [ ] Backups working
- [ ] SSL working (if configured)

### **Ongoing**
- [ ] Monitor logs daily
- [ ] Check disk space weekly
- [ ] Update dependencies monthly
- [ ] Review security quarterly
- [ ] Test backups quarterly

---

## 🎯 **Quick Reference**

### **Start Services**
```bash
sudo systemctl start brain-ai
```

### **Stop Services**
```bash
sudo systemctl stop brain-ai
```

### **Restart Services**
```bash
sudo systemctl restart brain-ai
```

### **Check Status**
```bash
sudo systemctl status brain-ai
```

### **View Logs**
```bash
sudo journalctl -u brain-ai-api -f
```

### **Update Application**
```bash
cd /opt/brain-ai && git pull && sudo systemctl restart brain-ai
```

---

## 📞 **Support**

- **Documentation**: https://github.com/dawsonblock/THE-SUPER-BRAIN
- **Issues**: https://github.com/dawsonblock/THE-SUPER-BRAIN/issues
- **Discussions**: https://github.com/dawsonblock/THE-SUPER-BRAIN/discussions

---

**Version**: 4.5.0  
**Status**: Production Ready  
**Last Updated**: 2025-11-07

🚀 **Your Brain-AI system is now production-ready!**
