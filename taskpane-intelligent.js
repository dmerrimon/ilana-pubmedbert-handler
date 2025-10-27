/*
 * Ilana Protocol Intelligence - Intelligent Authoring Assistant
 * Real-time writing guidance with PubMedBERT meets Grammarly meets DMID reviewer
 */

/* global document, Office, Word */

// Enhanced Configuration
const CONFIG = {
  API_BACKEND_URL: "https://ilanalabs-add-in.onrender.com",
  INTELLIGENT_SUGGESTIONS_DELAY: 1500, // 1.5 seconds after typing stops
  MAX_SUGGESTIONS_PER_PARAGRAPH: 5,
  SUGGESTION_CONFIDENCE_THRESHOLD: 0.7
};

// Global state for intelligent features
let intelligentSuggestionsEnabled = true;
let currentSuggestions = [];
let typingTimer = null;
let suggestionBubbles = [];
let reviewerComments = [];

// Initialize the intelligent authoring assistant
Office.onReady((info) => {
  if (info.host === Office.HostType.Word) {
    document.getElementById("enable-intelligent-suggestions").onclick = toggleIntelligentSuggestions;
    document.getElementById("check-feasibility").onclick = runFeasibilityCheck;
    document.getElementById("categorize-comments").onclick = categorizeReviewerComments;
    
    // Set up real-time suggestions
    setupRealTimeSuggestions();
    
    console.log("Intelligent Authoring Assistant initialized");
  }
});

async function setupRealTimeSuggestions() {
  try {
    await Word.run(async (context) => {
      // Monitor content changes for real-time suggestions
      context.document.onContentChanged.add(handleContentChange);
      await context.sync();
    });
  } catch (error) {
    console.error("Failed to setup real-time suggestions:", error);
  }
}

async function handleContentChange() {
  if (!intelligentSuggestionsEnabled) return;
  
  // Clear existing timer
  if (typingTimer) {
    clearTimeout(typingTimer);
  }
  
  // Set new timer for delayed suggestions
  typingTimer = setTimeout(async () => {
    await generateIntelligentSuggestions();
  }, CONFIG.INTELLIGENT_SUGGESTIONS_DELAY);
}

async function generateIntelligentSuggestions() {
  try {
    await Word.run(async (context) => {
      // Get the current paragraph or selection
      const selection = context.document.getSelection();
      context.load(selection, "text");
      await context.sync();
      
      if (selection.text && selection.text.length > 10) {
        const suggestions = await getIntelligentSuggestions(selection.text, "general");
        
        if (suggestions.phrase_suggestions.length > 0 || 
            suggestions.feasibility_concerns.length > 0 || 
            suggestions.regulatory_flags.length > 0) {
          
          displayInlineSuggestions(suggestions, selection);
        }
      }
    });
  } catch (error) {
    console.error("Failed to generate intelligent suggestions:", error);
  }
}

async function getIntelligentSuggestions(text, context) {
  try {
    const response = await fetch(`${CONFIG.API_BACKEND_URL}/api/intelligent-suggestions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: text,
        context: context
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Error getting intelligent suggestions:", error);
    return { phrase_suggestions: [], feasibility_concerns: [], regulatory_flags: [] };
  }
}

function displayInlineSuggestions(suggestions, selection) {
  // Clear previous suggestions
  clearSuggestionBubbles();
  
  // Create suggestion panel
  const suggestionsHtml = createSuggestionPanel(suggestions);
  
  // Update the suggestions display
  const suggestionsContainer = document.getElementById("intelligent-suggestions");
  if (suggestionsContainer) {
    suggestionsContainer.innerHTML = suggestionsHtml;
    suggestionsContainer.style.display = "block";
  }
  
  // Store current suggestions for potential application
  currentSuggestions = suggestions;
}

function createSuggestionPanel(suggestions) {
  let html = '<div class="suggestion-panel">';
  
  // Phrase suggestions
  if (suggestions.phrase_suggestions.length > 0) {
    html += '<div class="suggestion-category">';
    html += '<h4>💡 Writing Improvements</h4>';
    
    suggestions.phrase_suggestions.forEach((suggestion, index) => {
      const severityClass = suggestion.severity === 'high' ? 'high-priority' : 
                          suggestion.severity === 'medium' ? 'medium-priority' : 'low-priority';
      
      html += `
        <div class="suggestion-item ${severityClass}">
          <div class="suggestion-header">
            <span class="original-phrase">"${suggestion.original}"</span>
            <span class="category-badge ${suggestion.category}">${suggestion.category}</span>
          </div>
          <div class="suggestion-rationale">${suggestion.rationale}</div>
          <div class="suggestion-options">
            ${suggestion.suggestions.map((opt, optIndex) => 
              `<button class="suggestion-option" onclick="applySuggestion('${suggestion.original}', '${opt}', ${index})">${opt}</button>`
            ).join('')}
          </div>
        </div>
      `;
    });
    
    html += '</div>';
  }
  
  // Feasibility concerns
  if (suggestions.feasibility_concerns.length > 0) {
    html += '<div class="suggestion-category">';
    html += '<h4>⚠️ Feasibility Concerns</h4>';
    
    suggestions.feasibility_concerns.forEach((concern, index) => {
      html += `
        <div class="feasibility-concern">
          <div class="concern-title">${concern.concern}</div>
          <div class="concern-suggestions">
            ${concern.suggestions.map(s => `<li>${s}</li>`).join('')}
          </div>
        </div>
      `;
    });
    
    html += '</div>';
  }
  
  // Regulatory flags
  if (suggestions.regulatory_flags.length > 0) {
    html += '<div class="suggestion-category">';
    html += '<h4>🚩 Regulatory Alerts</h4>';
    
    suggestions.regulatory_flags.forEach(flag => {
      html += `<div class="regulatory-flag">${flag}</div>`;
    });
    
    html += '</div>';
  }
  
  html += '</div>';
  return html;
}

async function applySuggestion(originalPhrase, newPhrase, suggestionIndex) {
  try {
    await Word.run(async (context) => {
      // Find and replace the original phrase with the suggestion
      const searchResults = context.document.body.search(originalPhrase, {
        matchCase: false,
        matchWholeWord: false
      });
      
      context.load(searchResults, 'items');
      await context.sync();
      
      if (searchResults.items.length > 0) {
        // Replace the first occurrence
        searchResults.items[0].insertText(newPhrase, Word.InsertLocation.replace);
        await context.sync();
        
        // Remove the applied suggestion from display
        removeSuggestionFromDisplay(suggestionIndex);
        
        console.log(`Applied suggestion: "${originalPhrase}" → "${newPhrase}"`);
      }
    });
  } catch (error) {
    console.error("Failed to apply suggestion:", error);
  }
}

function removeSuggestionFromDisplay(index) {
  // Remove the suggestion from the current display
  // This could be enhanced to smoothly animate the removal
  const suggestionItems = document.querySelectorAll('.suggestion-item');
  if (suggestionItems[index]) {
    suggestionItems[index].style.opacity = '0.5';
    suggestionItems[index].style.textDecoration = 'line-through';
  }
}

async function runFeasibilityCheck() {
  try {
    showLoadingState("Analyzing operational feasibility...");
    
    await Word.run(async (context) => {
      const body = context.document.body;
      context.load(body, "text");
      await context.sync();
      
      const response = await fetch(`${CONFIG.API_BACKEND_URL}/api/feasibility-check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: body.text
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      displayFeasibilityResults(result.concerns);
    });
    
  } catch (error) {
    console.error("Feasibility check failed:", error);
    showError("Feasibility check failed. Please try again.");
  } finally {
    hideLoadingState();
  }
}

function displayFeasibilityResults(concerns) {
  const resultsContainer = document.getElementById("feasibility-results");
  
  if (concerns.length === 0) {
    resultsContainer.innerHTML = '<div class="success-message">✅ No major feasibility concerns identified!</div>';
    return;
  }
  
  let html = '<div class="feasibility-analysis"><h3>Feasibility Analysis Results</h3>';
  
  concerns.forEach(concern => {
    html += `
      <div class="feasibility-item concern">
        <div class="concern-header">
          <span class="concern-type">${concern.type.replace('_', ' ').toUpperCase()}</span>
        </div>
        <div class="concern-description">${concern.concern}</div>
        <div class="concern-suggestions">
          <strong>Recommendations:</strong>
          <ul>
            ${concern.suggestions.map(s => `<li>${s}</li>`).join('')}
          </ul>
        </div>
      </div>
    `;
  });
  
  html += '</div>';
  resultsContainer.innerHTML = html;
}

async function categorizeReviewerComments() {
  try {
    showLoadingState("Analyzing reviewer comments...");
    
    await Word.run(async (context) => {
      // Look for comments in the document
      const comments = context.document.body.getComments();
      context.load(comments, 'items');
      await context.sync();
      
      if (comments.items.length === 0) {
        showError("No comments found in the document.");
        return;
      }
      
      const categorizedComments = [];
      
      for (let comment of comments.items) {
        context.load(comment, 'content');
        await context.sync();
        
        const response = await fetch(`${CONFIG.API_BACKEND_URL}/api/categorize-comment`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            comment_text: comment.content
          })
        });
        
        if (response.ok) {
          const category = await response.json();
          categorizedComments.push({
            content: comment.content,
            category: category.category,
            confidence: category.confidence,
            suggested_actions: category.suggested_actions
          });
        }
      }
      
      displayCategorizedComments(categorizedComments);
    });
    
  } catch (error) {
    console.error("Comment categorization failed:", error);
    showError("Comment categorization failed. Please try again.");
  } finally {
    hideLoadingState();
  }
}

function displayCategorizedComments(comments) {
  const resultsContainer = document.getElementById("comment-analysis-results");
  
  let html = '<div class="comment-analysis"><h3>Reviewer Comment Analysis</h3>';
  
  // Group comments by category
  const groupedComments = {};
  comments.forEach(comment => {
    if (!groupedComments[comment.category]) {
      groupedComments[comment.category] = [];
    }
    groupedComments[comment.category].push(comment);
  });
  
  Object.keys(groupedComments).forEach(category => {
    html += `
      <div class="comment-category">
        <h4>${category.replace('_', ' ').toUpperCase()}</h4>
        ${groupedComments[category].map(comment => `
          <div class="comment-item">
            <div class="comment-content">"${comment.content}"</div>
            <div class="confidence-badge ${comment.confidence}">${comment.confidence} confidence</div>
            <div class="suggested-actions">
              <strong>Suggested Actions:</strong>
              <ul>
                ${comment.suggested_actions.map(action => `<li>${action}</li>`).join('')}
              </ul>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  });
  
  html += '</div>';
  resultsContainer.innerHTML = html;
}

function toggleIntelligentSuggestions() {
  intelligentSuggestionsEnabled = !intelligentSuggestionsEnabled;
  
  const button = document.getElementById("enable-intelligent-suggestions");
  const suggestionsContainer = document.getElementById("intelligent-suggestions");
  
  if (intelligentSuggestionsEnabled) {
    button.textContent = "🔧 Disable Smart Suggestions";
    button.classList.add("active");
    suggestionsContainer.style.display = "block";
  } else {
    button.textContent = "🔧 Enable Smart Suggestions";
    button.classList.remove("active");
    suggestionsContainer.style.display = "none";
    clearSuggestionBubbles();
  }
}

function clearSuggestionBubbles() {
  const suggestionsContainer = document.getElementById("intelligent-suggestions");
  if (suggestionsContainer) {
    suggestionsContainer.innerHTML = "";
    suggestionsContainer.style.display = "none";
  }
}

function showLoadingState(message) {
  const loadingDiv = document.getElementById("loading");
  if (loadingDiv) {
    loadingDiv.textContent = message;
    loadingDiv.style.display = "block";
  }
}

function hideLoadingState() {
  const loadingDiv = document.getElementById("loading");
  if (loadingDiv) {
    loadingDiv.style.display = "none";
  }
}

function showError(message) {
  const errorDiv = document.getElementById("error-message");
  if (errorDiv) {
    errorDiv.textContent = message;
    errorDiv.style.display = "block";
    setTimeout(() => {
      errorDiv.style.display = "none";
    }, 5000);
  }
}