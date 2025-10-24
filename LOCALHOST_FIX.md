# Fix "Localhost Sent Invalid Response" Error

This error means the local server isn't running properly or Office can't connect to it.

## 🔧 **Quick Fix Steps**

### **Option 1: Use Simple Node Server (Recommended)**

1. **Use the fixed package.json:**
   ```bash
   cp package-fixed.json package.json
   ```

2. **Start the fixed server:**
   ```bash
   node server-fix.js
   ```

3. **You should see:**
   ```
   🚀 Protocol Intelligence Add-in server running at http://localhost:3000
   📝 Taskpane: http://localhost:3000/taskpane.html
   ✅ Server is ready for Office Add-in testing!
   ```

4. **Test server manually:**
   - Open browser: `http://localhost:3000/taskpane.html`
   - Should show the Protocol Intelligence interface

### **Option 2: No Installation Method**

If you can't run local servers, use this direct testing approach:

1. **Copy taskpane.html content**
2. **Go to any online HTML editor** (like CodePen, JSFiddle)
3. **Paste the HTML + JavaScript**
4. **Test the Word integration directly**

### **Option 3: Use Different Port**

If port 3000 is busy:

1. **Edit server-fix.js:**
   ```javascript
   const PORT = 8080; // Change to different port
   ```

2. **Update manifest:**
   ```xml
   <SourceLocation DefaultValue="http://localhost:8080/taskpane.html"/>
   ```

## 🧪 **Test Server Connection**

### **Step 1: Verify Server is Running**
```bash
# Should show server response
curl http://localhost:3000/taskpane.html
```

### **Step 2: Check in Browser**
Open: `http://localhost:3000/taskpane.html`

**Expected:** Protocol Intelligence interface loads

### **Step 3: Test Manifest File**
Open: `http://localhost:3000/manifest-simple.xml`

**Expected:** XML content displays

## 🔍 **Common Issues & Solutions**

### **"Port already in use"**
```bash
# Kill existing process
lsof -ti:3000 | xargs kill -9

# Or use different port
node server-fix.js
```

### **"ECONNREFUSED"**
- **Issue:** Server not running
- **Fix:** Run `node server-fix.js` first

### **"Mixed content" (HTTPS/HTTP)**
- **Issue:** Word Online requires HTTPS
- **Fix:** Use Word Desktop for HTTP testing

### **"Add-in won't load"**
- **Issue:** Manifest points to wrong URL
- **Fix:** Verify server URL matches manifest

## 🎯 **Alternative Testing Methods**

### **Method 1: Online Hosting**
1. Upload files to GitHub Pages or Netlify
2. Update manifest with HTTPS URL
3. Test with online hosting

### **Method 2: Local File Testing**
1. Open `taskpane.html` directly in browser
2. Test JavaScript functions manually
3. Verify Office.js integration

### **Method 3: Script Lab Alternative**
If localhost won't work, I can create a version that runs entirely in browser without server.

## ✅ **Success Checklist**

Before uploading manifest:
- ✅ Server running on http://localhost:3000
- ✅ Taskpane loads in browser
- ✅ No console errors
- ✅ Manifest file accessible
- ✅ All files served correctly

**The fixed server should resolve the "invalid response" error!**