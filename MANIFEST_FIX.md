# Manifest Fix Guide

The original manifest had validation issues. I've created two corrected versions:

## **Option 1: Simple Manifest (Recommended)**
**File:** `manifest-simple.xml`

**Use this for basic testing** - minimal, clean manifest that should work immediately.

### What's Fixed:
- ✅ Proper XML structure
- ✅ Valid GUID for Id
- ✅ Working icon URLs (using Office dev samples)
- ✅ Simplified structure without version overrides
- ✅ Basic taskpane functionality

## **Option 2: Full-Featured Manifest**  
**File:** `manifest-fixed.xml`

**Use this for production** - includes ribbon button and modern features.

### What's Fixed:
- ✅ Proper namespace declarations
- ✅ Fixed VersionOverrides structure
- ✅ Working icon and resource URLs
- ✅ Ribbon integration
- ✅ Modern Office requirements

## **🚀 Quick Test Steps**

### **Step 1: Try Simple Version First**
1. Use `manifest-simple.xml` file
2. Upload to Word Online → Insert → Add-ins → Upload My Add-in
3. Should load as basic taskpane

### **Step 2: If Simple Works, Try Full Version**
1. Use `manifest-fixed.xml` file
2. Should add ribbon button and advanced features

## **🔧 Common Manifest Issues & Fixes**

### **"Invalid manifest" error:**
- **Issue**: XML syntax or structure
- **Fix**: Use `manifest-simple.xml` first

### **"Add-in won't load" error:**
- **Issue**: HTTPS requirement
- **Fix**: Run `npm run start-simple` and use HTTP

### **"Icon not found" error:**
- **Issue**: Icon URLs not accessible
- **Fix**: Using public GitHub URLs that work

### **HTTPS Issues (if needed):**
```bash
# Install dev certificates
npm install -g office-addin-dev-certs
npx office-addin-dev-certs install

# Start with HTTPS
npm run start
```

## **✅ Validation Test**

You can validate the manifest here:
https://docs.microsoft.com/en-us/office/dev/add-ins/testing/troubleshoot-manifest

Or upload directly to Word Online to test.

## **🎯 Expected Result**

After uploading the correct manifest:
- ✅ No validation errors
- ✅ Add-in appears in Word
- ✅ Taskpane opens with Protocol Intelligence UI
- ✅ All buttons and features work

**Start with `manifest-simple.xml` - it should work immediately!**