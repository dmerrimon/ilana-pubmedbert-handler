/*
 * Ilana Protocol Intelligence - Grammarly-style MVP
 * Real-time ICH-GCP + FDA compliance checking with inline highlights
 */

/* global document, Office, Word */

// Configuration - API keys will be loaded from backend API
const CONFIG = {
  PINECONE_INDEX_NAME: "llama-text-embed-v2-index",
  PINECONE_ENVIRONMENT: "gcp-starter",
  AZURE_OPENAI_ENDPOINT: "https://protocol-talk.openai.azure.com/",
  AZURE_OPENAI_DEPLOYMENT: "gpt-4o-deployment",
  PUBMEDBERT_ENDPOINT_URL: "https://usz78oxlybv4xfh2.eastus.azure.endpoints.huggingface.cloud",
  API_BACKEND_URL: "https://ilanalabs-add-in.onrender.com", // Your Render backend API
  REAL_TIME_DELAY: 2000, // 2 seconds after typing stops
  MAX_HIGHLIGHTS: 50 // Prevent performance issues
};

// Global state
let realTimeEnabled = true;
let currentIssues = [];
let typingTimer = null;
let highlightedRanges = [];
let isInitialized = false;


// Feedback system for AI improvement
async function submitFeedback(findingId, action, userFeedback) {
  try {
    // Get current document text for context
    let documentText = "";
    try {
      await Word.run(async (context) => {
        const body = context.document.body;
        context.load(body, "text");
        await context.sync();
        documentText = body.text;
      });
    } catch (error) {
      console.log("Could not get document text for feedback");
    }
    
    const response = await fetch(`${CONFIG.API_BACKEND_URL}/api/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        finding_id: findingId,
        action: action,
        user_feedback: userFeedback,
        protocol_text: documentText.substring(0, 1000) // Send sample for context
      })
    });

    if (!response.ok) {
      throw new Error(`Feedback submission failed: ${response.status}`);
    }

    const result = await response.json();
    console.log("Feedback submitted successfully:", result);
    return result;

  } catch (error) {
    console.error("Failed to submit feedback:", error);
    throw error;
  }
}

// Initialize when Office is ready
function initializeApp() {
  if (isInitialized) return;
  
  try {
    console.log("Ilana Protocol Intelligence initializing...");
    
    // Set up event listeners
    setupEventListeners();
    
    // Start real-time monitoring
    if (realTimeEnabled) {
      startRealTimeMonitoring();
    }
    
    // Initial scan
    scanDocument();
    
    isInitialized = true;
    console.log("Ilana Protocol Intelligence initialized successfully");
  } catch (error) {
    console.error("Initialization error:", error);
    showError("Failed to initialize. Please reload the add-in.");
  }
}

// Office initialization with error handling
if (typeof Office !== 'undefined') {
  Office.onReady((info) => {
    if (info.host === Office.HostType.Word) {
      initializeApp();
    }
  });
} else {
  // Fallback if Office.js isn't loaded
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
      if (typeof Office !== 'undefined') {
        Office.onReady((info) => {
          if (info.host === Office.HostType.Word) {
            initializeApp();
          }
        });
      } else {
        showError("Office.js not loaded. Please refresh the add-in.");
      }
    }, 1000);
  });
}

function setupEventListeners() {
  try {
    // Scan button
    const scanBtn = document.getElementById("scan-button");
    if (scanBtn) scanBtn.onclick = scanDocument;
    
    // Filter buttons
    document.querySelectorAll(".filter-btn").forEach(btn => {
      btn.onclick = () => filterIssues(btn.dataset.filter);
    });
    
    // Quick actions
    const acceptBtn = document.getElementById("accept-all-btn");
    const ignoreBtn = document.getElementById("ignore-all-btn");
    if (acceptBtn) acceptBtn.onclick = acceptAllSuggestions;
    if (ignoreBtn) ignoreBtn.onclick = ignoreAllSuggestions;
    
    // Status indicator toggle
    const statusIndicator = document.getElementById("status-indicator");
    if (statusIndicator) statusIndicator.onclick = toggleRealTime;
    
    console.log("Event listeners set up successfully");
  } catch (error) {
    console.error("Error setting up event listeners:", error);
  }
}

async function scanDocument() {
  showLoading(true);
  
  try {
    // Get document content
    const documentText = await getDocumentContent();
    
    // Analyze with your AI stack
    const issues = await analyzeProtocol(documentText);
    
    // Update UI
    updateQualityScores(issues.scores);
    updateAmendmentRisk(issues.amendmentRisk);
    displayIssues(issues.findings);
    
    // Add inline highlights
    await addInlineHighlights(issues.findings);
    
  } catch (error) {
    console.error("Scan failed:", error);
    showError("Analysis failed. Please try again.");
  } finally {
    showLoading(false);
  }
}

async function getDocumentContent() {
  if (typeof Word === 'undefined') {
    throw new Error('Word API not available');
  }
  
  return new Promise((resolve, reject) => {
    Word.run(async (context) => {
      try {
        const body = context.document.body;
        context.load(body, "text");
        await context.sync();
        resolve(body.text || '');
      } catch (error) {
        console.error("Error getting document content:", error);
        reject(error);
      }
    }).catch(error => {
      console.error("Word.run failed:", error);
      reject(error);
    });
  });
}

async function analyzeProtocol(text) {
  console.log("Analyzing protocol text:", text.substring(0, 100) + "...");
  
  try {
    console.log("Trying backend API...");
    
    // Call your backend API which handles all AI services securely
    const response = await fetch(`${CONFIG.API_BACKEND_URL}/api/analyze-protocol`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: text.substring(0, 5000) // Limit text size
      })
    });
    
    if (!response.ok) {
      throw new Error(`Backend API failed: ${response.status}`);
    }
    
    const aiAnalysis = await response.json();
    console.log("Backend API success:", aiAnalysis);
    
    return aiAnalysis;
  } catch (error) {
    console.error("Backend API failed:", error.message);
    
    // Return error state instead of mock data
    return {
      scores: {
        clarity: "?",
        regulatory: "?",
        feasibility: "?"
      },
      amendmentRisk: "unknown",
      findings: [
        {
          id: "connection-error",
          type: "compliance",
          severity: "high",
          title: "Analysis Service Unavailable",
          description: `Cannot connect to AI analysis service: ${error.message}. Please check your internet connection and try again.`,
          citation: "Service connectivity required for protocol analysis",
          location: { start: 0, length: 0 },
          suggestions: ["Check internet connection", "Retry analysis", "Contact support if problem persists"],
          quoted_text: "",
          evidence: "Network connectivity issue"
        }
      ]
    };
  }
}

// All AI analysis functions moved to backend API for security and accuracy

function updateQualityScores(scores) {
  // Update score badges
  Object.keys(scores).forEach(scoreType => {
    const badge = document.getElementById(`${scoreType}-badge`);
    const grade = document.getElementById(`${scoreType}-grade`);
    
    if (badge && grade) {
      // Remove existing grade classes
      badge.classList.remove("A", "B", "C", "D", "F");
      // Add new grade class
      badge.classList.add(scores[scoreType]);
      grade.textContent = scores[scoreType];
    }
  });
}

function updateAmendmentRisk(risk) {
  const riskElement = document.getElementById("risk-score");
  if (riskElement) {
    riskElement.textContent = risk.charAt(0).toUpperCase() + risk.slice(1);
    riskElement.className = `risk-score ${risk}`;
  }
}

function displayIssues(issues) {
  currentIssues = issues;
  const issuesList = document.getElementById("issues-list");
  const issueCount = document.getElementById("issue-count");
  
  // Update count
  issueCount.textContent = issues.length;
  
  // Clear existing issues
  issuesList.innerHTML = "";
  
  if (issues.length === 0) {
    issuesList.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">✅</div>
        <h4>No Issues Found</h4>
        <p>Your protocol meets current compliance standards.</p>
      </div>
    `;
    return;
  }
  
  // Display issues
  issues.forEach(issue => {
    const issueElement = createIssueElement(issue);
    issuesList.appendChild(issueElement);
  });
}

function createIssueElement(issue) {
  const div = document.createElement("div");
  div.className = `issue-item ${issue.type}`;
  
  // Build quoted text section if available
  const quotedTextHtml = issue.quoted_text ? `
    <div class="issue-quoted-text">
      <strong>Problematic Text:</strong> "${issue.quoted_text}"
    </div>
  ` : '';
  
  // Build evidence section if available
  const evidenceHtml = issue.evidence ? `
    <div class="issue-evidence">
      <strong>Regulatory Evidence:</strong> ${issue.evidence}
    </div>
  ` : '';
  
  div.innerHTML = `
    <div class="issue-header">
      <span class="issue-type ${issue.type}">${issue.type}</span>
      <span class="issue-severity ${issue.severity}">${issue.severity}</span>
    </div>
    <div class="issue-title">${issue.title}</div>
    <div class="issue-description">${issue.description}</div>
    ${quotedTextHtml}
    ${evidenceHtml}
    <div class="issue-citation">
      <strong>Source:</strong> ${issue.citation}
    </div>
    <div class="issue-actions">
      <button class="issue-action-btn accept" onclick="acceptSuggestion('${issue.id}')">
        Accept
      </button>
      <button class="issue-action-btn ignore" onclick="ignoreSuggestion('${issue.id}')">
        Ignore
      </button>
      <button class="issue-action-btn learn-more" onclick="learnMore('${issue.id}')">
        Learn More
      </button>
    </div>
  `;
  
  // Add click handler to highlight text
  div.onclick = () => highlightIssueInDocument(issue);
  
  return div;
}

async function addInlineHighlights(issues) {
  console.log(`Adding highlights for ${issues.length} issues`);
  
  return Word.run(async (context) => {
    try {
      // Clear existing highlights
      await clearHighlights(context);
      
      // Only add highlights for issues that have specific locations and quoted text
      const validIssues = issues.filter(issue => 
        issue.location && 
        issue.location.start >= 0 && 
        issue.location.length > 0 &&
        issue.quoted_text
      );
      
      console.log(`Found ${validIssues.length} valid issues with locations`);
      
      // Add new highlights for valid issues only
      for (const issue of validIssues.slice(0, CONFIG.MAX_HIGHLIGHTS)) {
        await addHighlight(context, issue);
      }
      
      await context.sync();
    } catch (error) {
      console.error("Highlighting failed:", error);
    }
  });
}

async function addHighlight(context, issue) {
  try {
    console.log(`Highlighting issue: ${issue.title} at position ${issue.location.start}-${issue.location.start + issue.location.length}`);
    
    const body = context.document.body;
    context.load(body, "text");
    await context.sync();
    
    // Create range from specific character positions
    const startPos = Math.max(0, issue.location.start);
    const endPos = Math.min(body.text.length, startPos + issue.location.length);
    
    if (startPos < endPos && startPos < body.text.length) {
      // Search for the quoted text around the specified location
      let searchText = issue.quoted_text;
      if (!searchText || searchText.length < 3) {
        // If no quoted text, use a portion of the document at that location
        searchText = body.text.substring(startPos, endPos).trim();
      }
      
      if (searchText.length > 0) {
        const searchResults = body.search(searchText, {
          matchCase: false,
          matchWholeWord: false
        });
        context.load(searchResults, "items");
        await context.sync();
        
        if (searchResults.items.length > 0) {
          const highlightRange = searchResults.items[0];
          
          // Apply Grammarly-style highlighting based on issue type
          const colorMap = {
            compliance: "#ffebee", // Light red background
            feasibility: "#fff8e1", // Light yellow background  
            clarity: "#e3f2fd" // Light blue background
          };
          
          const underlineMap = {
            compliance: "#f44336", // Red underline
            feasibility: "#ff9800", // Orange underline
            clarity: "#2196f3" // Blue underline
          };
          
          // Set background color and underline
          highlightRange.font.highlightColor = colorMap[issue.type] || "#e3f2fd";
          highlightRange.font.underline = Word.UnderlineType.single;
          highlightRange.font.underlineColor = underlineMap[issue.type] || "#2196f3";
          
          // Store reference for later removal
          highlightedRanges.push(highlightRange);
          
          console.log(`Successfully highlighted: "${searchText.substring(0, 50)}..."`);
        } else {
          console.log(`No match found for: "${searchText.substring(0, 50)}..."`);
        }
      }
    }
  } catch (error) {
    console.error(`Failed to highlight issue "${issue.title}":`, error);
  }
}

async function clearHighlights(context) {
  // Remove existing highlights
  highlightedRanges.forEach(range => {
    try {
      range.font.highlightColor = null;
      range.font.underline = Word.UnderlineType.none;
    } catch (error) {
      // Range might be invalid, ignore
    }
  });
  
  highlightedRanges = [];
}

function highlightIssueInDocument(issue) {
  if (!issue.location) return;
  
  Word.run(async (context) => {
    try {
      // Navigate to the issue location in document
      const range = context.document.body.getRange();
      range.select();
      await context.sync();
    } catch (error) {
      console.error("Navigation failed:", error);
    }
  });
}

function filterIssues(filterType) {
  // Update filter button states
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.classList.remove("active");
  });
  document.querySelector(`[data-filter="${filterType}"]`).classList.add("active");
  
  // Make sure currentIssues exists and has data
  if (!currentIssues || currentIssues.length === 0) {
    console.log("No current issues to filter");
    return;
  }
  
  // Filter issues
  let filteredIssues = currentIssues;
  if (filterType !== "all") {
    filteredIssues = currentIssues.filter(issue => issue.type === filterType);
  }
  
  console.log(`Filtering by ${filterType}: ${filteredIssues.length} issues found`);
  displayIssues(filteredIssues);
}

async function acceptSuggestion(issueId) {
  console.log("Accepting suggestion:", issueId);
  
  try {
    // Send feedback to backend for AI improvement
    await submitFeedback(issueId, "accept", "User accepted this suggestion");
    
    // Apply the suggested changes to the document
    // TODO: Implement actual document modification
    console.log("Suggestion accepted and feedback sent");
    
    // Remove issue from list
    removeIssue(issueId);
    
  } catch (error) {
    console.error("Error accepting suggestion:", error);
  }
}

async function ignoreSuggestion(issueId) {
  console.log("Ignoring suggestion:", issueId);
  
  try {
    // Send feedback to backend for AI improvement
    await submitFeedback(issueId, "ignore", "User ignored this suggestion");
    
    console.log("Suggestion ignored and feedback sent");
    
    // Remove issue from list
    removeIssue(issueId);
    
  } catch (error) {
    console.error("Error ignoring suggestion:", error);
    // Still remove from UI even if feedback fails
    removeIssue(issueId);
  }
}

function learnMore(issueId) {
  const issue = currentIssues.find(i => i.id === issueId);
  if (issue) {
    // TODO: Open learn more panel or external link
    console.log("Learn more about:", issue.title);
    alert(`Learn more about: ${issue.title}\\n\\n${issue.citation}`);
  }
}

function removeIssue(issueId) {
  currentIssues = currentIssues.filter(issue => issue.id !== issueId);
  displayIssues(currentIssues);
  
  // Update scores if needed
  // TODO: Recalculate scores after issue resolution
}

function acceptAllSuggestions() {
  console.log("Accepting all suggestions");
  // TODO: Batch apply all suggestions
  currentIssues = [];
  displayIssues(currentIssues);
}

function ignoreAllSuggestions() {
  console.log("Ignoring all suggestions");
  currentIssues = [];
  displayIssues(currentIssues);
}

function toggleRealTime() {
  realTimeEnabled = !realTimeEnabled;
  const indicator = document.getElementById("status-indicator");
  const dot = indicator.querySelector(".status-dot");
  const text = indicator.querySelector(".status-text");
  
  if (realTimeEnabled) {
    dot.classList.add("active");
    text.textContent = "Real-time checking active";
    startRealTimeMonitoring();
  } else {
    dot.classList.remove("active");
    text.textContent = "Real-time checking paused";
    stopRealTimeMonitoring();
  }
}

function startRealTimeMonitoring() {
  if (!realTimeEnabled) return;
  
  // TODO: Set up document change listeners
  console.log("Real-time monitoring started");
  
  // Mock implementation - in real version, listen to document changes
  // and call scanDocument() after typing stops
}

function stopRealTimeMonitoring() {
  console.log("Real-time monitoring stopped");
  if (typingTimer) {
    clearTimeout(typingTimer);
    typingTimer = null;
  }
}

function showLoading(show) {
  const overlay = document.getElementById("loading-overlay");
  overlay.style.display = show ? "flex" : "none";
}

function showError(message) {
  // TODO: Implement proper error UI
  console.error(message);
  alert(message);
}

// Export for global access
window.acceptSuggestion = acceptSuggestion;
window.ignoreSuggestion = ignoreSuggestion;
window.learnMore = learnMore;