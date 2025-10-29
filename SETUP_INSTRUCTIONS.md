# Protocol Intelligence Office Add-in Setup

**Script Lab is broken with JSON parsing errors.** This is a proper Office Add-in that bypasses Script Lab entirely and gives you full functionality.

## 🚀 Quick Setup (5 minutes)

### **Step 1: Install Dependencies**
```bash
cd office-addin
npm install
```

### **Step 2: Start Local Server**
```bash
npm run start-simple
```
This starts the add-in at `http://localhost:3000`

### **Step 3: Sideload Add-in**

#### **Option A: Word Online (Easiest)**
1. Go to **Word Online** (office.com)
2. Open a document
3. Go to **Insert** → **Add-ins** → **Upload My Add-in**
4. Upload the `manifest.xml` file
5. The **Protocol Intelligence** button appears in the ribbon

#### **Option B: Word Desktop**
1. Open **Word Desktop**
2. Go to **Insert** → **Get Add-ins** → **Upload My Add-in**
3. Upload the `manifest.xml` file

### **Step 4: Test the Add-in**
1. Click **Protocol Intelligence** in the ribbon
2. Task pane opens on the right
3. Click **"Insert Test Text"** to add sample protocol
4. Click **"Analyze Protocol"** to see analysis
5. Click **"Start Monitoring"** to test real-time suggestions

## 🧪 **Testing Features**

### **Full Protocol Analysis**
- Word count and section detection
- Compliance scoring
- Issue identification
- Therapeutic area detection

### **Real-time Monitoring**
- Type "endpoint" → suggests "primary endpoint"
- Type "patients" → suggests "study subjects"  
- Type "study will" → suggests "this study will"
- Type "drug" → suggests "investigational product"

### **Interactive Suggestions**
- Grammarly-style popups
- Apply/dismiss options
- Confidence scoring
- Detailed explanations

## 📊 **What You'll See**

### **Status Log**
- Real-time feedback of all operations
- Timestamps and detailed messages
- Error reporting and debugging info

### **Analysis Results**
- Compliance scores and section detection
- Missing elements identification
- Therapeutic area classification
- Issue severity levels

### **Suggestion Popups**
- Professional styling like Grammarly
- Clear before/after comparisons
- Regulatory reasoning
- Confidence percentages

## 🔧 **Troubleshooting**

### **"Add-in won't load"**
- Check console for HTTPS errors
- Try `npm run install-cert` for HTTPS support
- Use `npm run start-simple` for HTTP testing

### **"No suggestions appearing"**
- Check status log for detection messages
- Try the exact trigger words: "endpoint", "patients"
- Make sure monitoring is started

### **"Apply doesn't work"**
- Check that the trigger word exists in document
- Word's search is case-sensitive for replacement
- Try typing the word again

## ✅ **Success Criteria**

You'll know it's working when:
- ✅ Add-in loads in Word task pane
- ✅ Status log shows real-time messages
- ✅ Analysis shows compliance scores
- ✅ Suggestions appear as popups
- ✅ Apply button actually changes document text

## 🎯 **Full Feature Demo**

1. **Insert test text** → adds sample protocol
2. **Analyze protocol** → shows 85% compliance score
3. **Start monitoring** → real-time detection active
4. **Type "endpoint"** → popup suggests "primary endpoint"
5. **Click Apply** → document text changes
6. **Status log** → shows "✅ Applied: primary endpoint"

This gives you the **complete Protocol Intelligence experience** without Script Lab limitations!

## 🚀 **Next Steps**

Once this works, you can:
- Connect to the backend API (protocol-intelligence-api.js)
- Add more sophisticated AI features
- Deploy to production servers
- Distribute through Microsoft AppSource

The add-in infrastructure is production-ready!