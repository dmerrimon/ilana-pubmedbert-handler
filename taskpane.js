/*
 * Copyright (c) Ilana Labs. All rights reserved.
 * Licensed under the MIT license.
 */

/* global document, Office, Word */

Office.onReady((info) => {
  if (info.host === Office.HostType.Word) {
    document.getElementById("analyze-btn").onclick = analyzeProtocol;
    
    // Initialize UI
    initializeUI();
    
    // Set up real-time monitoring
    setupRealTimeMonitoring();
  }
});

function initializeUI() {
  console.log("Protocol Intelligence add-in initialized");
}

async function analyzeProtocol() {
  const analyzeBtn = document.getElementById("analyze-btn");
  const welcomeSection = document.getElementById("welcome-section");
  const analysisSection = document.getElementById("analysis-section");
  const loadingSection = document.getElementById("analysis-loading");
  const resultsSection = document.getElementById("analysis-results");
  
  try {
    // Show loading state
    analyzeBtn.disabled = true;
    welcomeSection.style.display = "none";
    analysisSection.style.display = "block";
    loadingSection.style.display = "block";
    resultsSection.style.display = "none";
    
    // Get document content
    const documentText = await getDocumentContent();
    
    // Call our API
    const analysisResults = await callProtocolAnalysisAPI(documentText);
    
    // Show results
    displayAnalysisResults(analysisResults);
    
    loadingSection.style.display = "none";
    resultsSection.style.display = "block";
    
  } catch (error) {
    console.error("Analysis failed:", error);
    showError("Analysis failed. Please try again.");
  } finally {
    analyzeBtn.disabled = false;
  }
}

async function getDocumentContent() {
  return Word.run(async (context) => {
    const body = context.document.body;
    body.load("text");
    await context.sync();
    return body.text;
  });
}

async function callProtocolAnalysisAPI(text, options = {}) {
  // DEMO MODE: Return mock data since API isn't deployed yet
  console.log("🔍 Demo mode: Analyzing protocol text:", text.substring(0, 100) + "...");
  
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  return {
    compliance_analysis: {
      overall_score: 85,
      grade: "Good",
      missing_sections: [
        "Statistical Analysis Plan details",
        "Data Safety Monitoring Board charter"
      ],
      red_flags: [
        { severity: "medium", issue: "Inclusion criteria may be too broad", description: "Consider more specific patient population" },
        { severity: "low", issue: "Primary endpoint timeline unclear", description: "Specify exact measurement timepoints" }
      ]
    },
    feasibility_analysis: {
      overall_risk: "Medium",
      risk_factors: [
        "Target enrollment may be challenging in proposed timeline",
        "Multiple site coordination requires robust infrastructure"
      ],
      recruitment_prediction: "12-18 months for full enrollment"
    },
    recommendations: [
      "Add more specific inclusion criteria to reduce screen failures",
      "Clarify primary endpoint measurement schedule",
      "Consider adaptive trial design for efficiency"
    ]
  };
  
  // Original API call (disabled for demo):
  // const apiBase = "https://protocol-intelligence-api.onrender.com/api";
  // 
  // try {
  //   console.log("🔍 Calling Protocol Intelligence API...");
  //   
  //   const response_disabled = await fetch(`${apiBase}/analyze`, {
  //     method: "POST", 
  //     headers: {
  //       "Content-Type": "application/json",
  //     },
  //     body: JSON.stringify({ 
  //       text: text,
  //       context: {
  //         document_type: "clinical_protocol",
  //         analysis_type: "comprehensive"
  //       }
  //     })
  //   });
  // 
  //   if (!response.ok) {
  //     throw new Error(`API call failed: ${response.status}`);
  //   }
  // 
  //   const result = await response.json();
  //   console.log("✅ API Response received");
  //   return result;
  //   
  // } catch (error) {
  //   console.error("API call failed:", error);
  //   // Return fallback results
  //   return {
  //     compliance: {
  //       compliance_level: "UNKNOWN",
  //       compliance_score: 0,
  //       missing_sections: ["Unable to analyze - service unavailable"],
  //       recommendations: ["Please check your internet connection and try again"]
  //     },
  //     feasibility: {
  //       risk_level: "UNKNOWN",
  //       red_flags: [],
  //       recommendations: ["Service temporarily unavailable"]
  //     },
  //     clarity: {
  //       clarity_score: 0,
  //       recommendations: ["Service temporarily unavailable"]
  //     }
  //   };
  // }
}

function displayAnalysisResults(results) {
  const resultsSection = document.getElementById("analysis-results");
  
  const compliance = results.compliance || {};
  const feasibility = results.feasibility || {};
  const clarity = results.clarity || {};
  
  resultsSection.innerHTML = `
    <div class="analysis-results">
      <h2 class="ms-fontSize-xl ms-fontWeight-semibold">Analysis Results</h2>
      
      <div class="result-section">
        <h3 class="result-title">📋 Compliance Analysis</h3>
        <div class="score-indicator ${getScoreClass(compliance.compliance_score)}">
          Level: ${compliance.compliance_level || 'UNKNOWN'}
          <span class="score-value">${Math.round((compliance.compliance_score || 0) * 100)}%</span>
        </div>
        ${compliance.missing_sections && compliance.missing_sections.length > 0 ? `
          <div class="missing-sections">
            <h4>Missing Sections:</h4>
            <ul>
              ${compliance.missing_sections.map(section => `<li>${section}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
        ${compliance.recommendations && compliance.recommendations.length > 0 ? `
          <div class="recommendations">
            <h4>Recommendations:</h4>
            <ul>
              ${compliance.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
      </div>
      
      <div class="result-section">
        <h3 class="result-title">🎯 Feasibility Analysis</h3>
        <div class="risk-indicator ${getRiskClass(feasibility.risk_level)}">
          Risk Level: ${feasibility.risk_level || 'UNKNOWN'}
        </div>
        ${feasibility.red_flags && feasibility.red_flags.length > 0 ? `
          <div class="red-flags">
            <h4>Red Flags Detected:</h4>
            <ul>
              ${feasibility.red_flags.map(flag => `
                <li class="red-flag ${flag.severity ? flag.severity.toLowerCase() : 'medium'}">
                  <strong>${flag.category || 'General'}:</strong> ${flag.pattern || flag}
                </li>
              `).join('')}
            </ul>
          </div>
        ` : '<p>No significant feasibility concerns detected.</p>'}
        ${feasibility.recommendations && feasibility.recommendations.length > 0 ? `
          <div class="recommendations">
            <h4>Recommendations:</h4>
            <ul>
              ${feasibility.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
      </div>
      
      <div class="result-section">
        <h3 class="result-title">📝 Clarity Analysis</h3>
        <div class="clarity-score">
          <div class="score-indicator ${getScoreClass(clarity.clarity_score)}">
            Clarity Score: ${Math.round((clarity.clarity_score || 0) * 100)}%
          </div>
        </div>
        ${clarity.recommendations && clarity.recommendations.length > 0 ? `
          <div class="recommendations">
            <h4>Writing Suggestions:</h4>
            <ul>
              ${clarity.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
      </div>
      
      <div class="action-buttons">
        <button class="ms-Button ms-Button--primary" onclick="enableRealTimeAnalysis()">
          <span class="ms-Button-label">Enable Real-time Analysis</span>
        </button>
        <button class="ms-Button ms-Button--default" onclick="exportResults()">
          <span class="ms-Button-label">Export Results</span>
        </button>
      </div>
    </div>
  `;
}

function getScoreClass(score) {
  if (score >= 0.8) return 'excellent';
  if (score >= 0.6) return 'good';
  if (score >= 0.4) return 'fair';
  return 'poor';
}

function getRiskClass(level) {
  switch(level) {
    case 'LOW': return 'low-risk';
    case 'MEDIUM': return 'medium-risk';
    case 'HIGH': return 'high-risk';
    default: return 'unknown-risk';
  }
}

function showError(message) {
  const resultsSection = document.getElementById("analysis-results");
  resultsSection.innerHTML = `
    <div class="error-message">
      <h3>❌ Error</h3>
      <p>${message}</p>
      <button class="ms-Button ms-Button--primary" onclick="analyzeProtocol()">
        <span class="ms-Button-label">Try Again</span>
      </button>
    </div>
  `;
  
  const loadingSection = document.getElementById("analysis-loading");
  const resultsSection2 = document.getElementById("analysis-results");
  loadingSection.style.display = "none";
  resultsSection2.style.display = "block";
}

// Real-time analysis functions
let realTimeEnabled = false;
let analysisInterval;

function setupRealTimeMonitoring() {
  console.log("Setting up real-time monitoring...");
}

function toggleRealTimeAnalysis() {
  const button = document.getElementById("realtime-toggle");
  const label = button.querySelector(".ms-Button-label");
  
  if (realTimeEnabled) {
    // Disable real-time
    realTimeEnabled = false;
    if (analysisInterval) {
      clearInterval(analysisInterval);
    }
    label.textContent = "Enable Real-time";
    button.classList.remove("ms-Button--primary");
    button.classList.add("ms-Button--default");
    console.log("Real-time analysis disabled");
  } else {
    // Enable real-time
    realTimeEnabled = true;
    label.textContent = "Disable Real-time";
    button.classList.remove("ms-Button--default");
    button.classList.add("ms-Button--primary");
    
    // Start monitoring (every 10 seconds)
    analysisInterval = setInterval(performRealTimeCheck, 10000);
    console.log("Real-time analysis enabled");
    
    // Show confirmation
    showMessage("Real-time analysis enabled. Changes will be monitored automatically.", "success");
  }
}

function enableRealTimeAnalysis() {
  if (!realTimeEnabled) {
    toggleRealTimeAnalysis();
  }
}

async function performRealTimeCheck() {
  if (!realTimeEnabled) return;
  
  try {
    const currentText = await getDocumentContent();
    const lastText = localStorage.getItem('lastAnalyzedText');
    
    if (currentText !== lastText && currentText.length > 100) {
      console.log("📝 Document changed, performing real-time analysis...");
      localStorage.setItem('lastAnalyzedText', currentText);
      
      // Perform quick analysis
      const results = await callProtocolAnalysisAPI(currentText, { analysisType: "quick" });
      
      // Show brief notification
      if (results.compliance && results.compliance.compliance_score < 0.7) {
        showInlineNotification("⚠️ Potential compliance issues detected", "warning");
      }
      
      if (results.feasibility && results.feasibility.risk_level === "HIGH") {
        showInlineNotification("🎯 High feasibility risk detected", "error");
      }
    }
  } catch (error) {
    console.error("Real-time analysis error:", error);
  }
}

function showInlineNotification(message, type = "info") {
  // Create notification popup
  const notification = document.createElement('div');
  notification.className = `inline-notification ${type}`;
  notification.innerHTML = `
    <div class="notification-content">
      <span class="notification-message">${message}</span>
      <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
    </div>
  `;
  
  document.body.appendChild(notification);
  
  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (notification.parentElement) {
      notification.remove();
    }
  }, 5000);
}

function showMessage(message, type = "info") {
  showInlineNotification(message, type);
}

function exportResults() {
  const resultsSection = document.getElementById("analysis-results");
  const content = resultsSection.innerText;
  
  // Create downloadable text file
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'protocol-analysis-results.txt';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  showMessage("Results exported successfully!", "success");
}

// Make functions globally available
window.toggleRealTimeAnalysis = toggleRealTimeAnalysis;
window.enableRealTimeAnalysis = enableRealTimeAnalysis;
window.exportResults = exportResults;