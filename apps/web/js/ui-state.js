/**
 * UI State Management and Utilities
 */
class UIState {
  constructor() {
    this.state = {
      currentProject: null,
      currentSimulation: null,
      isLoading: false,
      error: null,
      lastResults: null,
    };
  }

  /**
   * Set state
   */
  setState(updates) {
    this.state = { ...this.state, ...updates };
    this.dispatchStateChangeEvent();
  }

  /**
   * Get state
   */
  getState() {
    return { ...this.state };
  }

  /**
   * Dispatch state change event
   */
  dispatchStateChangeEvent() {
    window.dispatchEvent(
      new CustomEvent('statechange', { detail: this.state })
    );
  }

  /**
   * Set loading
   */
  setLoading(isLoading, message = null) {
    this.setState({ isLoading, loadingMessage: message });
  }

  /**
   * Set error
   */
  setError(error) {
    this.setState({ error });
    console.error('UI Error:', error);
  }

  /**
   * Clear error
   */
  clearError() {
    this.setState({ error: null });
  }
}

/**
 * UI Helper Functions
 */
class UIHelpers {
  /**
   * Show loader
   */
  static showLoader(message = 'Processing...') {
    const loader = document.getElementById('loader');
    const loaderText = document.getElementById('loader-text');
    
    if (loader) {
      loaderText.textContent = message;
      loader.style.display = 'flex';
    }
  }

  /**
   * Hide loader
   */
  static hideLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
      loader.style.display = 'none';
    }
  }

  /**
   * Show notification
   */
  static showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 16px 24px;
      background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
      color: white;
      border-radius: 8px;
      z-index: 9999;
      animation: slideIn 0.3s ease-out;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    `;

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      notification.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => notification.remove(), 300);
    }, 5000);
  }

  /**
   * Format number
   */
  static formatNumber(num, decimals = 2) {
    if (!num && num !== 0) return 'N/A';
    return parseFloat(num).toFixed(decimals);
  }

  /**
   * Format scientific notation
   */
  static formatScientific(num, decimals = 2) {
    if (!num && num !== 0) return 'N/A';
    return parseFloat(num).toExponential(decimals);
  }

  /**
   * Format percentage
   */
  static formatPercentage(num, decimals = 1) {
    if (!num && num !== 0) return 'N/A';
    return `${parseFloat(num).toFixed(decimals)}%`;
  }

  /**
   * Create circuit parameter table
   */
  static createParameterTable(params, title = 'Parameters') {
    const table = document.createElement('table');
    table.className = 'param-table';
    table.innerHTML = `
      <thead>
        <tr>
          <th>${title}</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        ${Object.entries(params || {})
          .map(([key, value]) => `
            <tr>
              <td>${this.formatKey(key)}</td>
              <td>${this.formatValue(value)}</td>
            </tr>
          `)
          .join('')}
      </tbody>
    `;
    return table;
  }

  /**
   * Format key from camelCase
   */
  static formatKey(key) {
    return key
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, (str) => str.toUpperCase())
      .trim();
  }

  /**
   * Format value
   */
  static formatValue(value) {
    if (typeof value === 'number') {
      if (value < 1e-6 || value > 1e6) {
        return this.formatScientific(value, 2);
      }
      return this.formatNumber(value);
    }
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  }

  /**
   * Enable/disable form
   */
  static enableForm(form, enabled = true) {
    const elements = form.querySelectorAll('input, button, select, textarea');
    elements.forEach((el) => {
      el.disabled = !enabled;
    });
  }

  /**
   * Get form data as object
   */
  static getFormData(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData) {
      if (value === '' || value === 'null') {
        data[key] = null;
      } else if (!isNaN(value) && value !== '') {
        data[key] = parseFloat(value);
      } else if (value === 'true') {
        data[key] = true;
      } else if (value === 'false') {
        data[key] = false;
      } else {
        data[key] = value;
      }
    }
    
    return data;
  }

  /**
   * Populate form from object
   */
  static populateForm(form, data) {
    Object.entries(data || {}).forEach(([key, value]) => {
      const input = form.elements[key];
      if (input) {
        if (input.type === 'checkbox') {
          input.checked = value === true;
        } else if (input.type === 'radio') {
          const radio = form.querySelector(`input[name="${key}"][value="${value}"]`);
          if (radio) radio.checked = true;
        } else {
          input.value = value;
        }
      }
    });
  }
}

// Global instances
window.uiState = new UIState();
window.UIHelpers = UIHelpers;

// Global event listener for state changes
window.addEventListener('statechange', (event) => {
  console.log('State updated:', event.detail);
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(400px);
      opacity: 0;
    }
  }

  .param-table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
  }

  .param-table th {
    background: #f3f4f6;
    padding: 12px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #e5e7eb;
  }

  .param-table td {
    padding: 12px;
    border-bottom: 1px solid #e5e7eb;
  }

  .param-table tr:hover {
    background: #f9fafb;
  }
`;
document.head.appendChild(style);
