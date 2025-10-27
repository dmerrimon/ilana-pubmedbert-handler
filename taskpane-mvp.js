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
    
    // Phase I: Core features only
    
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
  console.log("Analyzing protocol text with ALL sophisticated AI features:", text.substring(0, 100) + "...");
  
  try {
    console.log("🚀 Using ALL sophisticated analysis endpoints...");
    
    // Call ALL available sophisticated endpoints
    const [basicAnalysis, sophisticatedGuidance, intelligenceStatus] = await Promise.all([
      // Basic protocol analysis
      fetch(`${CONFIG.API_BACKEND_URL}/api/analyze-protocol`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.substring(0, 5000) })
      }),
      
      // Sophisticated authoring guidance (9.5/10 intelligence)
      fetch(`${CONFIG.API_BACKEND_URL}/api/sophisticated-authoring`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: text.substring(0, 3000),
          context: "protocol" 
        })
      }),
      
      // Get current intelligence status
      fetch(`${CONFIG.API_BACKEND_URL}/api/intelligence-status`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
    ]);
    
    if (!basicAnalysis.ok) {
      throw new Error(`Basic analysis failed: ${basicAnalysis.status}`);
    }
    
    const basicResult = await basicAnalysis.json();
    console.log("✅ Basic analysis success:", basicResult);
    
    // Get intelligence status
    let currentIntelligence = "basic";
    if (intelligenceStatus.ok) {
      try {
        const statusResult = await intelligenceStatus.json();
        currentIntelligence = statusResult.intelligence_level || statusResult.current_intelligence_level;
        console.log("✅ Intelligence status:", currentIntelligence);
        
        // Show intelligence level in UI
        updateIntelligenceStatus(statusResult);
      } catch (e) {
        console.warn("Could not get intelligence status:", e);
      }
    }
    
    // Get sophisticated guidance if available
    let sophisticatedFindings = [];
    if (sophisticatedGuidance.ok) {
      try {
        const sophisticatedResult = await sophisticatedGuidance.json();
        console.log("✅ Sophisticated guidance success:", sophisticatedResult);
        
        // Convert sophisticated guidance to findings format
        sophisticatedFindings = sophisticatedResult.map(guidance => ({
          id: guidance.suggestion_id,
          type: guidance.type,
          severity: guidance.severity,
          title: guidance.title,
          description: guidance.description,
          citation: guidance.evidence,
          location: { 
            start: guidance.text_span[0], 
            length: guidance.text_span[1] - guidance.text_span[0] 
          },
          suggestions: guidance.suggestions,
          quoted_text: guidance.original,
          evidence: `${guidance.rationale} (Confidence: ${(guidance.confidence * 100).toFixed(0)}%)`
        }));
        
        console.log(`✅ Converted ${sophisticatedFindings.length} sophisticated findings`);
      } catch (e) {
        console.warn("Sophisticated guidance parsing failed:", e);
      }
    } else {
      console.warn("Sophisticated guidance not available:", sophisticatedGuidance.status);
    }
    
    // Combine basic findings with sophisticated findings
    const allFindings = [...basicResult.findings, ...sophisticatedFindings];
    
    const enhancedResult = {
      ...basicResult,
      findings: allFindings,
      intelligence_level: sophisticatedFindings.length > 0 ? "sophisticated_9.5" : basicResult.intelligence_level || "basic"
    };
    
    console.log(`✅ Enhanced analysis complete: ${allFindings.length} total findings (${sophisticatedFindings.length} sophisticated)`);
    return enhancedResult;
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
  console.log("🎯 Navigating to issue:", issue.title, "at location:", issue.location);
  
  if (!issue.location || !issue.quoted_text) {
    console.warn("No location or quoted text for issue:", issue.id);
    return;
  }
  
  Word.run(async (context) => {
    try {
      const body = context.document.body;
      context.load(body, "text");
      await context.sync();
      
      // Search for the exact quoted text first
      let searchText = issue.quoted_text.trim();
      console.log(`🔍 Searching for: "${searchText}"`);
      
      const searchResults = body.search(searchText, {
        matchCase: false,
        matchWholeWord: false
      });
      context.load(searchResults, "items");
      await context.sync();
      
      if (searchResults.items.length > 0) {
        // Found the text - navigate to it
        const foundRange = searchResults.items[0];
        foundRange.select();
        
        // Scroll to make it visible
        foundRange.scrollIntoView();
        
        // Flash highlight to show user where it is
        foundRange.font.highlightColor = "#ffff00"; // Bright yellow
        
        setTimeout(() => {
          Word.run(async (ctx) => {
            try {
              foundRange.font.highlightColor = null;
              await ctx.sync();
            } catch (e) {
              console.log("Could not remove flash highlight");
            }
          });
        }, 2000);
        
        await context.sync();
        console.log("✅ Successfully navigated to issue location");
        
      } else {
        // If exact text not found, try to navigate by character position
        console.warn("Exact text not found, trying position-based navigation");
        
        const startPos = Math.max(0, issue.location.start);
        const endPos = Math.min(body.text.length, startPos + issue.location.length);
        
        if (startPos < body.text.length) {
          const range = body.getRange();
          const targetRange = range.getRange(Word.RangeLocation.start).expandTo(
            range.getRange(Word.RangeLocation.start).getRange(Word.RangeLocation.after, startPos)
          );
          
          targetRange.select();
          targetRange.scrollIntoView();
          await context.sync();
          console.log("✅ Navigated to approximate position");
        }
      }
      
    } catch (error) {
      console.error("❌ Navigation failed:", error);
      alert(`Could not navigate to issue: ${error.message}`);
    }
  });
}

function filterIssues(filterType) {
  console.log(`Filter clicked: ${filterType}, currentIssues:`, currentIssues);
  
  // Update filter button states
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.classList.remove("active");
  });
  
  const filterButton = document.querySelector(`[data-filter="${filterType}"]`);
  if (filterButton) {
    filterButton.classList.add("active");
  }
  
  // Make sure currentIssues exists and has data
  if (!currentIssues || currentIssues.length === 0) {
    console.log("No current issues to filter");
    const issuesList = document.getElementById("issues-list");
    if (issuesList) {
      issuesList.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">📋</div>
          <h4>No Issues to Filter</h4>
          <p>Run a scan first to find protocol issues.</p>
        </div>
      `;
    }
    return;
  }
  
  // Filter issues based on type
  let filteredIssues = currentIssues;
  if (filterType !== "all") {
    filteredIssues = currentIssues.filter(issue => {
      console.log(`Checking issue type: ${issue.type} against filter: ${filterType}`);
      return issue.type === filterType;
    });
  }
  
  console.log(`Filtering by ${filterType}: ${filteredIssues.length} of ${currentIssues.length} issues shown`);
  
  // Update the display
  displayFilteredIssues(filteredIssues, filterType);
}

function displayFilteredIssues(issues, filterType) {
  const issuesList = document.getElementById("issues-list");
  const issueCount = document.getElementById("issue-count");
  
  // Update count to show filtered vs total
  if (filterType === "all") {
    issueCount.textContent = issues.length;
  } else {
    issueCount.textContent = `${issues.length} of ${currentIssues.length}`;
  }
  
  // Clear existing issues
  issuesList.innerHTML = "";
  
  if (issues.length === 0) {
    const filterMessage = filterType === "all" 
      ? "No issues found in this document." 
      : `No ${filterType} issues found.`;
      
    issuesList.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <h4>No Issues</h4>
        <p>${filterMessage}</p>
      </div>
    `;
    return;
  }
  
  // Display filtered issues
  issues.forEach(issue => {
    const issueElement = createIssueElement(issue);
    issuesList.appendChild(issueElement);
  });
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
  if (!issue) {
    console.error("Issue not found:", issueId);
    return;
  }
  
  console.log("📚 Learn more about:", issue.title);
  
  // First, navigate to the issue location in the document
  highlightIssueInDocument(issue);
  
  // Then show detailed information panel
  showDetailedIssueInfo(issue);
}

function showDetailedIssueInfo(issue) {
  // Create a detailed popup with issue information
  const modal = document.createElement('div');
  modal.className = 'issue-detail-modal';
  modal.innerHTML = `
    <div class="modal-overlay" onclick="closeIssueDetail()">
      <div class="modal-content" onclick="event.stopPropagation()">
        <div class="modal-header">
          <h3>${issue.title}</h3>
          <button class="close-btn" onclick="closeIssueDetail()">✕</button>
        </div>
        <div class="modal-body">
          <div class="issue-meta">
            <span class="issue-type-badge ${issue.type}">${issue.type}</span>
            <span class="issue-severity-badge ${issue.severity}">${issue.severity}</span>
          </div>
          
          <div class="issue-description">
            <h4>Description</h4>
            <p>${issue.description}</p>
          </div>
          
          ${issue.quoted_text ? `
            <div class="issue-quoted">
              <h4>Problematic Text</h4>
              <blockquote>"${issue.quoted_text}"</blockquote>
            </div>
          ` : ''}
          
          ${issue.suggestions && issue.suggestions.length > 0 ? `
            <div class="issue-suggestions">
              <h4>Suggested Improvements</h4>
              <ul>
                ${issue.suggestions.map(s => `<li>${s}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
          
          <div class="issue-evidence">
            <h4>Regulatory Evidence</h4>
            <p>${issue.evidence || issue.citation}</p>
          </div>
          
          <div class="modal-actions">
            <button class="btn primary" onclick="acceptSuggestion('${issue.id}'); closeIssueDetail();">
              Accept Suggestion
            </button>
            <button class="btn secondary" onclick="ignoreSuggestion('${issue.id}'); closeIssueDetail();">
              Ignore
            </button>
            <button class="btn tertiary" onclick="navigateToIssue('${issue.id}');">
              Show in Document
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Add styles if not already present
  if (!document.querySelector('#issue-detail-styles')) {
    const styles = document.createElement('style');
    styles.id = 'issue-detail-styles';
    styles.textContent = `
      .issue-detail-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 1000;
      }
      .modal-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
      }
      .modal-content {
        background: white;
        border-radius: 8px;
        max-width: 500px;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      }
      .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px;
        border-bottom: 1px solid #eee;
      }
      .modal-header h3 {
        margin: 0;
        color: #333;
      }
      .close-btn {
        background: none;
        border: none;
        font-size: 20px;
        cursor: pointer;
        color: #666;
      }
      .modal-body {
        padding: 20px;
      }
      .issue-meta {
        margin-bottom: 15px;
      }
      .issue-type-badge, .issue-severity-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 8px;
      }
      .issue-type-badge.compliance { background: #ffebee; color: #c62828; }
      .issue-type-badge.feasibility { background: #fff8e1; color: #ef6c00; }
      .issue-type-badge.clarity { background: #e3f2fd; color: #1565c0; }
      .issue-severity-badge.high { background: #f44336; color: white; }
      .issue-severity-badge.medium { background: #ff9800; color: white; }
      .issue-severity-badge.low { background: #4caf50; color: white; }
      .modal-actions {
        display: flex;
        gap: 10px;
        margin-top: 20px;
      }
      .btn {
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
      }
      .btn.primary { background: #2196f3; color: white; }
      .btn.secondary { background: #757575; color: white; }
      .btn.tertiary { background: #e0e0e0; color: #333; }
    `;
    document.head.appendChild(styles);
  }
  
  document.body.appendChild(modal);
}

function closeIssueDetail() {
  const modal = document.querySelector('.issue-detail-modal');
  if (modal) {
    modal.remove();
  }
}

function navigateToIssue(issueId) {
  const issue = currentIssues.find(i => i.id === issueId);
  if (issue) {
    highlightIssueInDocument(issue);
  }
}

function updateIntelligenceStatus(statusResult) {
  // Add intelligence level indicator to the UI
  const statusIndicator = document.getElementById("status-indicator");
  const statusText = statusIndicator.querySelector(".status-text");
  
  if (statusResult && statusResult.intelligence_level) {
    const intelligenceLevel = statusResult.intelligence_level;
    let displayText = "Basic analysis";
    let color = "#666";
    
    if (intelligenceLevel.includes("9.5")) {
      displayText = "🧠 Sophisticated AI (9.5/10)";
      color = "#4CAF50";
    } else if (intelligenceLevel.includes("8.5")) {
      displayText = "🤖 Advanced AI (8.5/10)";
      color = "#2196F3";
    } else if (intelligenceLevel.includes("7.5")) {
      displayText = "🔧 Enhanced AI (7.5/10)";
      color = "#FF9800";
    }
    
    // Update the status text to show intelligence level
    if (!realTimeEnabled) {
      statusText.textContent = displayText;
      statusText.style.color = color;
    }
    
    console.log(`🧠 Intelligence level displayed: ${displayText}`);
  }
}

// Phase I: Document change tracking removed (moved to Phase II)

// Phase I: Reviewer comment analysis removed (moved to Phase II)

// Phase I: Collaborative Review & Version Intelligence removed (moved to Phase II)

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
  
  console.log("✅ Real-time sophisticated monitoring started");
  
  // Set up actual document change listeners for real-time guidance
  try {
    Word.run(async (context) => {
      // Monitor document changes
      context.document.onSelectionChanged.add(async () => {
        if (typingTimer) clearTimeout(typingTimer);
        
        typingTimer = setTimeout(async () => {
          try {
            console.log("📝 Document changed - getting real-time guidance");
            await getRealtimeGuidance();
          } catch (error) {
            console.error("Real-time guidance failed:", error);
          }
        }, CONFIG.REAL_TIME_DELAY);
      });
      
      await context.sync();
      console.log("✅ Document change listeners active");
    });
  } catch (error) {
    console.warn("Could not set up real-time monitoring:", error);
  }
}

async function getRealtimeGuidance() {
  try {
    // Get current selection or recent text
    const currentText = await getDocumentContent();
    
    if (currentText.length < 50) return; // Skip very short text
    
    // Get sophisticated authoring guidance for current context
    const response = await fetch(`${CONFIG.API_BACKEND_URL}/api/sophisticated-authoring`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        text: currentText.substring(0, 1000), // Smaller chunk for real-time
        context: "protocol" 
      })
    });
    
    if (response.ok) {
      const guidance = await response.json();
      if (guidance.length > 0) {
        // Show real-time suggestions
        showRealtimeGuidance(guidance);
        console.log(`📋 Real-time: ${guidance.length} sophisticated suggestions`);
      }
    }
  } catch (error) {
    console.error("Real-time guidance error:", error);
  }
}

function showRealtimeGuidance(guidance) {
  // Update the status bar to show real-time guidance count
  const statusText = document.querySelector(".status-text");
  if (statusText && guidance.length > 0) {
    statusText.textContent = `${guidance.length} live suggestions`;
    
    // Flash the status to indicate new guidance
    statusText.style.color = "#4CAF50";
    setTimeout(() => {
      statusText.style.color = "";
    }, 1000);
  }
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
window.closeIssueDetail = closeIssueDetail;
window.navigateToIssue = navigateToIssue;
// Phase I: Collaborative review features removed