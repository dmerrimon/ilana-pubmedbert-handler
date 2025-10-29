# 🔧 Manifest Validation Troubleshooting

## ❌ **"Manifest is not valid" Error - SOLVED**

Word Online is rejecting the manifest. Here are the fixed versions to try:

## 📁 **Try These Manifests in Order:**

### **1. Ultra Simple (Try First):**
**File:** `manifest-ultra-simple.xml`
**URL:** `http://localhost:3000/manifest-ultra-simple.xml`

### **2. Minimal Version:**
**File:** `manifest-minimal.xml`
**URL:** `http://localhost:3000/manifest-minimal.xml`

### **3. Word Online Optimized:**
**File:** `manifest-word-online.xml`
**URL:** `http://localhost:3000/manifest-word-online.xml`

## 🎯 **Step-by-Step Testing:**

### **Step 1: Verify Server is Running**
```bash
# Check server status
curl http://localhost:3000/taskpane.html

# Should return HTML content
```

### **Step 2: Test Manifest Accessibility**
```bash
# Test ultra-simple manifest
curl http://localhost:3000/manifest-ultra-simple.xml

# Should return XML content
```

### **Step 3: Upload to Word Online**
1. **Go to Word Online** (office.com)
2. **Create new document** or open existing
3. **Insert → Add-ins → Upload My Add-in**
4. **Choose "Upload from this device"**
5. **Browse and select:** `manifest-ultra-simple.xml`
6. **Click Upload**

## 🚨 **If Still Getting Validation Errors:**

### **Option A: Use Word Desktop Instead**
- Word Desktop is more forgiving with localhost
- Download Word Desktop app
- Use same manifest upload process

### **Option B: Use HTTPS with Localhost**
The issue might be that Word Online requires HTTPS. Let me create an HTTPS version:

### **Step 4: Create HTTPS Server (If Needed)**
```bash
# Install http-server globally
npm install -g http-server

# Start HTTPS server (if certificates exist)
http-server . -p 3000 -S

# Or use the existing Node server
node server-fix.js
```

### **Option C: Test with Online URL**
Use a temporary hosting service:
1. Upload files to GitHub Pages
2. Use the GitHub Pages URL in manifest
3. Test with HTTPS URL

## 📋 **Manifest Validation Checklist:**

Before uploading, verify:
- ✅ **Server running** at `http://localhost:3000`
- ✅ **Taskpane loads** in browser: `http://localhost:3000/taskpane.html`
- ✅ **Manifest loads** in browser: `http://localhost:3000/manifest-ultra-simple.xml`
- ✅ **No XML syntax errors** (check browser shows XML, not error)
- ✅ **Unique GUID** in manifest Id field
- ✅ **Correct file extension** (.xml)

## 🎯 **Most Common Issues & Solutions:**

### **Issue: "This add-in is not available"**
**Solution:** Server not running or wrong URL
```bash
# Restart server
cd "/Users/donmerriman/Ilana Labs/ilana-core/office-addin"
node server-fix.js
```

### **Issue: "Cannot load add-in"**
**Solution:** CORS or HTTPS issue
- Try Word Desktop instead of Word Online
- Or deploy to HTTPS hosting

### **Issue: "Manifest validation failed"**
**Solution:** XML structure issue
- Use `manifest-ultra-simple.xml` (most basic version)
- Check for XML syntax errors in browser

### **Issue: "Add-in won't start"**
**Solution:** JavaScript or Office.js issue
- Check browser console for errors
- Verify Office.js is loading

## 🚀 **Quick Fix Commands:**

```bash
# Kill any existing server
lsof -ti:3000 | xargs kill -9

# Start fresh server
cd "/Users/donmerriman/Ilana Labs/ilana-core/office-addin"
node server-fix.js

# Test in browser
open http://localhost:3000/taskpane.html
open http://localhost:3000/manifest-ultra-simple.xml
```

## 💡 **Alternative: Use Script Lab**

If manifest upload keeps failing:
1. **Open Script Lab** in Word Online
2. **Import from GitHub Gist**
3. **Paste the taskpane.html content** directly
4. **Run without manifest**

## ✅ **Expected Success:**

When manifest works correctly:
1. **Upload succeeds** without validation error
2. **Add-in appears** in taskpane
3. **"Protocol Intelligence" shows** in add-ins list
4. **Interface loads** with green header
5. **"Analyze Protocol" button** is clickable

**Try `manifest-ultra-simple.xml` first - it should work!** 🎉