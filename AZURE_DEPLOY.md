# DEPLOY TO AZURE STATIC WEB APPS

## Why Azure instead of Netlify:
- **Integration**: Works seamlessly with Azure ecosystem
- **Security**: Enterprise-grade security for clinical applications
- **Compliance**: Better for healthcare/clinical protocol requirements
- **Custom domains**: Easy to set up professional domains
- **Performance**: Global CDN with excellent performance

## AZURE DEPLOYMENT STEPS:

### Option 1: Azure Portal (5 minutes)
1. **Go to**: https://portal.azure.com
2. **Create Resource** > "Static Web Apps"
3. **Upload** the zip file or connect GitHub repo
4. **Get URL**: `https://yourapp.azurestaticapps.net`

### Option 2: Azure CLI (2 minutes)
```bash
# Install Azure CLI if needed
brew install azure-cli

# Login to Azure
az login

# Create resource group
az group create --name protocol-intelligence --location eastus

# Create static web app
az staticwebapp create \
  --name protocol-intelligence-addin \
  --resource-group protocol-intelligence \
  --source . \
  --location eastus \
  --branch main \
  --app-location "/" \
  --output-location "."
```

### Option 3: GitHub Actions (Automated)
1. **Push files to GitHub repo**
2. **Azure will auto-detect and deploy**
3. **Get production URL**

## FILES READY FOR AZURE:
- ✅ taskpane.html (Protocol Intelligence interface)
- ✅ taskpane.js (Full functionality with demo mode)
- ✅ All CSS files (Grammarly-inspired styling)
- ✅ protocol-intelligence-addin.zip (Deployment package)

## AFTER AZURE DEPLOYMENT:
1. **Get Azure URL**: `https://yourapp.azurestaticapps.net`
2. **Update manifest**: Use `https://yourapp.azurestaticapps.net/taskpane.html`
3. **Test in Word**: Upload new manifest with Azure URL

**AZURE WILL GIVE YOU:**
- ✅ Reliable HTTPS hosting
- ✅ Global CDN performance
- ✅ Enterprise security
- ✅ Perfect for AppSource submission
- ✅ No localhost bullshit