/*
 * Ilana Protocol Intelligence - Grammarly-style MVP
 * Real-time ICH-GCP + FDA compliance checking with inline highlights
 */

/* global document, Office, Word */

// Configuration
const CONFIG = {
  PINECONE_API_KEY: "pcsk_6UYhbF_UDVavrrjgpxC6W9fn8vaUdCZ6MbboBhmYum18isurrr8DrFFxMzYYexuzwA1YZT",
  PINECONE_INDEX_NAME: "llama-text-embed-v2-index",
  PINECONE_ENVIRONMENT: "gcp-starter",
  AZURE_OPENAI_ENDPOINT: "https://protocol-talk.openai.azure.com/",
  AZURE_OPENAI_API_KEY: "9yC9Uoz4EQ5BFxkzjOjSaEtrLoKEJ5sIQIQXrvUadTqliTcoZVq9JQQJ99BJACYeBjFXJ3w3AAABACOGwV3",
  AZURE_OPENAI_DEPLOYMENT: "gpt-4o-deployment",
  PUBMEDBERT_ENDPOINT_URL: "https://usz78oxlybv4xfh2.eastus.azure.endpoints.huggingface.cloud",
  REAL_TIME_DELAY: 2000, // 2 seconds after typing stops
  MAX_HIGHLIGHTS: 50 // Prevent performance issues
};

// Global state
let realTimeEnabled = true;
let currentIssues = [];
let typingTimer = null;
let highlightedRanges = [];
let isInitialized = false;

// Prevent page refresh crashes
window.addEventListener('beforeunload', function(e) {
  e.preventDefault();
  e.returnValue = '';
  return 'Refreshing will close the add-in. Are you sure?';
});

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
  // TODO: Connect to your Vector DB and AI stack
  // For now, return mock data with your MVP features
  
  return {
    scores: {
      clarity: calculateClarityScore(text),
      regulatory: calculateRegulatoryScore(text),
      feasibility: calculateFeasibilityScore(text)
    },
    amendmentRisk: calculateAmendmentRisk(text),
    findings: generateFindings(text)
  };
}

function calculateClarityScore(text) {
  // Mock scoring - replace with your AI analysis
  const wordCount = text.split(/\\s+/).length;
  const sentences = text.split(/[.!?]+/).length;
  const avgWordsPerSentence = wordCount / sentences;
  
  if (avgWordsPerSentence < 15) return "A";
  if (avgWordsPerSentence < 20) return "B";
  if (avgWordsPerSentence < 25) return "C";
  if (avgWordsPerSentence < 30) return "D";
  return "F";
}

function calculateRegulatoryScore(text) {
  // Mock regulatory compliance check
  const requiredSections = [
    "informed consent",
    "adverse event",
    "data safety monitoring",
    "statistical analysis",
    "inclusion criteria",
    "exclusion criteria"
  ];
  
  const foundSections = requiredSections.filter(section => 
    text.toLowerCase().includes(section)
  );
  
  const compliance = foundSections.length / requiredSections.length;
  
  if (compliance >= 0.9) return "A";
  if (compliance >= 0.8) return "B";
  if (compliance >= 0.7) return "C";
  if (compliance >= 0.6) return "D";
  return "F";
}

function calculateFeasibilityScore(text) {
  // Mock feasibility analysis
  const riskFactors = [
    "rare disease",
    "pediatric",
    "international",
    "multiple endpoints",
    "complex intervention"
  ];
  
  const foundRisks = riskFactors.filter(risk => 
    text.toLowerCase().includes(risk)
  );
  
  if (foundRisks.length === 0) return "A";
  if (foundRisks.length === 1) return "B";
  if (foundRisks.length === 2) return "C";
  if (foundRisks.length === 3) return "D";
  return "F";
}

function calculateAmendmentRisk(text) {
  // Mock amendment risk prediction
  const riskFactors = [
    "unclear endpoint",
    "broad inclusion",
    "complex protocol",
    "multiple sites",
    "novel intervention"
  ];
  
  const foundRisks = riskFactors.filter(risk => 
    text.toLowerCase().includes(risk.replace(" ", ""))
  );
  
  if (foundRisks.length === 0) return "low";
  if (foundRisks.length <= 2) return "medium";
  return "high";
}

function generateFindings(text) {
  // Mock findings generation - replace with your AI analysis
  const findings = [];
  
  // Compliance issues
  if (!text.toLowerCase().includes("informed consent")) {
    findings.push({
      id: "ic-missing",
      type: "compliance",
      severity: "high",
      title: "Missing Informed Consent Section",
      description: "Protocol must include detailed informed consent procedures.",
      citation: "ICH E6 (R3) §4.8: Informed consent is a process by which a subject voluntarily confirms his or her willingness to participate in a particular trial.",
      location: { start: 0, length: 20 }, // Character positions for highlighting
      suggestions: ["Add informed consent section", "Include consent form templates"]
    });
  }
  
  // Feasibility issues
  if (text.toLowerCase().includes("rare disease")) {
    findings.push({
      id: "rare-disease-risk",
      type: "feasibility", 
      severity: "medium",
      title: "Rare Disease Enrollment Challenge",
      description: "Rare disease studies often face recruitment difficulties that may require protocol amendments.",
      citation: "FDA Rare Disease Guidance: Consider alternative study designs and endpoints for rare disease populations.",
      location: { start: text.toLowerCase().indexOf("rare disease"), length: 12 },
      suggestions: ["Consider adaptive design", "Plan for extended recruitment", "Include patient registries"]
    });
  }
  
  // Clarity issues
  const longSentences = findLongSentences(text);
  if (longSentences.length > 0) {
    findings.push({
      id: "clarity-sentences",
      type: "clarity",
      severity: "low", 
      title: "Complex Sentence Structure",
      description: "Several sentences exceed recommended length for regulatory clarity.",
      citation: "FDA Plain Language Guidelines: Use clear, concise language in regulatory documents.",
      location: longSentences[0],
      suggestions: ["Break into shorter sentences", "Use active voice", "Simplify technical terms"]
    });
  }
  
  return findings;
}

function findLongSentences(text) {
  // Find sentences longer than 30 words
  const sentences = text.split(/[.!?]+/);
  const longSentences = [];
  
  let currentPos = 0;
  sentences.forEach(sentence => {
    const wordCount = sentence.trim().split(/\\s+/).length;
    if (wordCount > 30) {
      longSentences.push({
        start: currentPos,
        length: sentence.length
      });
    }
    currentPos += sentence.length + 1;
  });
  
  return longSentences;
}

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
  div.innerHTML = `
    <div class="issue-header">
      <span class="issue-type ${issue.type}">${issue.type}</span>
      <span class="issue-severity ${issue.severity}">${issue.severity}</span>
    </div>
    <div class="issue-title">${issue.title}</div>
    <div class="issue-description">${issue.description}</div>
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
  return Word.run(async (context) => {
    try {
      // Clear existing highlights
      await clearHighlights(context);
      
      // Add new highlights
      for (const issue of issues.slice(0, CONFIG.MAX_HIGHLIGHTS)) {
        if (issue.location) {
          await addHighlight(context, issue);
        }
      }
      
      await context.sync();
    } catch (error) {
      console.error("Highlighting failed:", error);
    }
  });
}

async function addHighlight(context, issue) {
  try {
    const range = context.document.body.getRange();
    context.load(range, "text");
    await context.sync();
    
    // Find the text to highlight
    const searchResults = range.search(issue.location.text || "", {
      matchCase: false,
      matchWholeWord: false
    });
    context.load(searchResults, "items");
    await context.sync();
    
    if (searchResults.items.length > 0) {
      const highlightRange = searchResults.items[0];
      
      // Apply Grammarly-style highlighting
      const colorMap = {
        compliance: "#f5574e", // Red underline
        feasibility: "#ffd93d", // Yellow underline  
        clarity: "#4285f4" // Blue underline
      };
      
      highlightRange.font.highlightColor = colorMap[issue.type] || "#4285f4";
      highlightRange.font.underline = Word.UnderlineType.single;
      
      // Store reference for later removal
      highlightedRanges.push(highlightRange);
    }
  } catch (error) {
    console.error("Individual highlight failed:", error);
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
  
  // Filter issues
  let filteredIssues = currentIssues;
  if (filterType !== "all") {
    filteredIssues = currentIssues.filter(issue => issue.type === filterType);
  }
  
  displayIssues(filteredIssues);
}

function acceptSuggestion(issueId) {
  console.log("Accepting suggestion:", issueId);
  // TODO: Implement suggestion acceptance
  // This would apply the suggested changes to the document
  
  // Remove issue from list
  removeIssue(issueId);
}

function ignoreSuggestion(issueId) {
  console.log("Ignoring suggestion:", issueId);
  // TODO: Store ignored suggestions to avoid re-showing
  
  // Remove issue from list
  removeIssue(issueId);
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