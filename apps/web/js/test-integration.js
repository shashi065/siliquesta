/**
 * SILIQUESTA Integration Test Suite
 * 
 * Run tests in browser console:
 * 1. Open frontend in browser (http://localhost:3000)
 * 2. Open DevTools Console (F12)
 * 3. Paste: fetch('/js/test-integration.js').then(r=>r.text()).then(js=>eval(js))
 * 4. Run tests: await runAllTests()
 * 
 * Or manually run individual tests:
 *   - await testImageBackendConnection()
 *   - await testAuthentication()
 *   - await testProjectManagement()
 *   - await testProjectSharing()
 *   - await testSimulation()
 */

const TEST_CONFIG = {
  backendUrl: 'http://localhost:5000/api/v1',
  aiServiceUrl: 'http://localhost:8000',
  timeout: 10000,
  testUser: {
    email: `test-${Date.now()}@integration.test`,
    password: 'TestPassword123!',
    name: 'Integration Test User'
  },
  testUser2: {
    email: `colleague-${Date.now()}@integration.test`,
    password: 'TestPassword123!',
    name: 'Colleague User'
  }
};

// Store test results
let testResults = {
  passed: 0,
  failed: 0,
  errors: [],
  logs: []
};

/**
 * API Helper
 */
class TestClient {
  constructor(baseUrl = TEST_CONFIG.backendUrl) {
    this.baseUrl = baseUrl;
    this.token = null;
    this.userId = null;
  }

  async request(method, endpoint, body = null) {
    const url = `${this.baseUrl}${endpoint}`;
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: TEST_CONFIG.timeout
    };

    if (this.token) {
      options.headers['Authorization'] = `Bearer ${this.token}`;
    }

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    const data = await response.json();

    return {
      status: response.status,
      ok: response.ok,
      data
    };
  }

  async signup(email, password, name) {
    const result = await this.request('POST', '/auth/signup', {
      email,
      password,
      name
    });

    if (result.ok) {
      this.token = result.data.accessToken;
      this.userId = result.data.user.id;
    }

    return result;
  }

  async login(email, password) {
    const result = await this.request('POST', '/auth/login', {
      email,
      password
    });

    if (result.ok) {
      this.token = result.data.accessToken;
      this.userId = result.data.user.id;
    }

    return result;
  }

  async getCurrentUser() {
    return this.request('GET', '/auth/me');
  }

  async createProject(name, description = '') {
    return this.request('POST', '/projects', {
      name,
      description
    });
  }

  async listProjects() {
    return this.request('GET', '/projects');
  }

  async getProject(projectId) {
    return this.request('GET', `/projects/${projectId}`);
  }

  async shareProject(projectId, collaboratorEmail, role = 'editor') {
    return this.request('POST', `/projects/${projectId}/share`, {
      collaborator_email: collaboratorEmail,
      role
    });
  }

  async listCollaborators(projectId) {
    return this.request('GET', `/projects/${projectId}/shares`);
  }

  async getSharedProjects() {
    return this.request('GET', '/projects/shared');
  }

  async runSimulation(projectId, parameters) {
    return this.request('POST', '/simulate', {
      project_id: projectId,
      parameters
    });
  }

  async getSimulationStatus(jobId) {
    return this.request('GET', `/jobs/${jobId}`);
  }

  async callAIService(endpoint, body) {
    return this.request('POST', endpoint, body);
  }
}

/**
 * Test Utilities
 */
function logTest(name, passed, details = '') {
  const icon = passed ? '✅' : '❌';
  const message = `${icon} ${name}`;
  const fullMessage = details ? `${message}\n   ${details}` : message;
  
  console.log(fullMessage);
  testResults.logs.push(fullMessage);
  
  if (passed) {
    testResults.passed++;
  } else {
    testResults.failed++;
    testResults.errors.push({ test: name, details });
  }
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

/**
 * Integration Tests
 */

// ========================================
// Test 1: Backend Connection
// ========================================
async function testBackendConnection() {
  console.log('\n📋 Testing Backend Connection...\n');
  
  try {
    const response = await fetch(`${TEST_CONFIG.backendUrl.replace('/api/v1', '')}/health`);
    const data = await response.json();
    
    assert(response.ok, 'Backend health check failed');
    assert(data.status === 'ok' || data.status === 'degraded', 'Backend status not ok');
    
    logTest('Backend Health Check', true, `Status: ${data.status}`);
    return true;
  } catch (error) {
    logTest('Backend Health Check', false, error.message);
    return false;
  }
}

// ========================================
// Test 2: AI Service Connection
// ========================================
async function testAIServiceConnection() {
  console.log('\n📋 Testing AI Service Connection...\n');
  
  try {
    const response = await fetch(`${TEST_CONFIG.aiServiceUrl}/health`);
    const data = await response.json();
    
    assert(response.ok, 'AI service health check failed');
    assert(data.status === 'ok', `AI service status: ${data.status}`);
    
    logTest('AI Service Health Check', true, `Status: ${data.status}`);
    return true;
  } catch (error) {
    logTest('AI Service Health Check', false, error.message);
    return false;
  }
}

// ========================================
// Test 3: Authentication Flow
// ========================================
async function testAuthentication() {
  console.log('\n🔐 Testing Authentication...\n');
  
  const client = new TestClient();
  
  try {
    // Test signup
    const signupResult = await client.signup(
      TEST_CONFIG.testUser.email,
      TEST_CONFIG.testUser.password,
      TEST_CONFIG.testUser.name
    );
    
    assert(signupResult.ok, 'Signup failed');
    assert(signupResult.data.accessToken, 'No access token returned');
    logTest('User Signup', true, `User ID: ${signupResult.data.user.id}`);
    
    // Test get current user
    const meResult = await client.getCurrentUser();
    assert(meResult.ok, 'Get current user failed');
    assert(meResult.data.email === TEST_CONFIG.testUser.email, 'Email mismatch');
    logTest('Get Current User', true, `Email: ${meResult.data.email}`);
    
    // Test logout (clear token) and login
    client.token = null;
    const loginResult = await client.login(
      TEST_CONFIG.testUser.email,
      TEST_CONFIG.testUser.password
    );
    
    assert(loginResult.ok, 'Login failed');
    assert(loginResult.data.accessToken, 'No access token returned');
    logTest('User Login', true, `Token received`);
    
    return { client, userId: signupResult.data.user.id };
  } catch (error) {
    logTest('Authentication Flow', false, error.message);
    return null;
  }
}

// ========================================
// Test 4: Project Management
// ========================================
async function testProjectManagement() {
  console.log('\n📁 Testing Project Management...\n');
  
  const authResult = await testAuthentication();
  if (!authResult) return null;
  
  const { client } = authResult;
  
  try {
    // Create project
    const createResult = await client.createProject(
      'Integration Test Project',
      'Testing all system features'
    );
    
    assert(createResult.ok, 'Create project failed');
    assert(createResult.data.id, 'No project ID returned');
    logTest('Create Project', true, `Project ID: ${createResult.data.id}`);
    
    const projectId = createResult.data.id;
    
    // Get project
    const getResult = await client.getProject(projectId);
    assert(getResult.ok, 'Get project failed');
    assert(getResult.data.name === 'Integration Test Project', 'Project name mismatch');
    logTest('Get Project', true, `Name: ${getResult.data.name}`);
    
    // List projects
    const listResult = await client.listProjects();
    assert(listResult.ok, 'List projects failed');
    assert(Array.isArray(listResult.data), 'Projects should be array');
    logTest('List Projects', true, `Found ${listResult.data.length} projects`);
    
    return { client, projectId };
  } catch (error) {
    logTest('Project Management', false, error.message);
    return null;
  }
}

// ========================================
// Test 5: Project Sharing
// ========================================
async function testProjectSharing() {
  console.log('\n👥 Testing Project Sharing...\n');
  
  const projectResult = await testProjectManagement();
  if (!projectResult) return false;
  
  const { client, projectId } = projectResult;
  
  try {
    // Create second user for sharing
    const client2 = new TestClient();
    const signupResult = await client2.signup(
      TEST_CONFIG.testUser2.email,
      TEST_CONFIG.testUser2.password,
      TEST_CONFIG.testUser2.name
    );
    
    assert(signupResult.ok, 'Second user signup failed');
    logTest('Second User Signup', true, `User ID: ${signupResult.data.user.id}`);
    
    // Share project
    const shareResult = await client.shareProject(
      projectId,
      TEST_CONFIG.testUser2.email,
      'editor'
    );
    
    assert(shareResult.ok, 'Share project failed');
    assert(shareResult.data.role === 'editor', 'Role mismatch');
    logTest('Share Project', true, `Role: ${shareResult.data.role}`);
    
    // List collaborators
    const listResult = await client.listCollaborators(projectId);
    assert(listResult.ok, 'List collaborators failed');
    assert(Array.isArray(listResult.data), 'Collaborators should be array');
    logTest('List Collaborators', true, `Found ${listResult.data.length} collaborators`);
    
    // Second user views shared projects
    const sharedResult = await client2.getSharedProjects();
    assert(sharedResult.ok, 'Get shared projects failed');
    assert(Array.isArray(sharedResult.data), 'Shared projects should be array');
    logTest('View Shared Projects', true, `Found ${sharedResult.data.length} shared projects`);
    
    return true;
  } catch (error) {
    logTest('Project Sharing', false, error.message);
    return false;
  }
}

// ========================================
// Test 6: Simulation Submission
// ========================================
async function testSimulation() {
  console.log('\n⚡ Testing Simulation...\n');
  
  const projectResult = await testProjectManagement();
  if (!projectResult) return false;
  
  const { client, projectId } = projectResult;
  
  try {
    // Run simulation
    const simResult = await client.runSimulation(projectId, {
      wn: 0.5,
      wp: 1.0,
      vdd: 1.2,
      temp: 27,
      years: 10
    });
    
    assert(simResult.ok, 'Simulation submission failed');
    assert(simResult.data.job_id, 'No job ID returned');
    logTest('Submit Simulation', true, `Job ID: ${simResult.data.job_id}`);
    
    const jobId = simResult.data.job_id;
    
    // Check job status (may still be queued)
    const statusResult = await client.getSimulationStatus(jobId);
    assert(statusResult.ok, 'Get job status failed');
    logTest('Get Job Status', true, `Status: ${statusResult.data.status}`);
    
    return true;
  } catch (error) {
    logTest('Simulation', false, error.message);
    return false;
  }
}

// ========================================
// Test 7: AI Service Integration
// ========================================
async function testAIServiceIntegration() {
  console.log('\n🤖 Testing AI Service Integration...\n');
  
  try {
    const response = await fetch(`${TEST_CONFIG.aiServiceUrl}/optimize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        wn: 0.5,
        wp: 1.0,
        vdd: 1.2,
        temp: 27
      })
    });
    
    const data = await response.json();
    assert(response.ok, `AI optimization failed: ${data.detail || data.error}`);
    assert(data.optimized_params, 'No optimized params returned');
    logTest('AI Optimization', true, `Optimized WN: ${data.optimized_params.wn}`);
    
    return true;
  } catch (error) {
    logTest('AI Service Integration', false, error.message);
    return false;
  }
}

// ========================================
// Test 8: Error Handling
// ========================================
async function testErrorHandling() {
  console.log('\n⚠️ Testing Error Handling...\n');
  
  const client = new TestClient();
  
  try {
    // Test unauthenticated request
    const unauthResult = await client.listProjects();
    assert(unauthResult.status === 401, 'Should reject unauthenticated request');
    logTest('Unauthenticated Request Rejection', true, `Status: ${unauthResult.status}`);
    
    // Test invalid project
    const testUser = await client.signup(
      `errortest-${Date.now()}@test.com`,
      'TestPassword123!',
      'Error Test User'
    );
    
    if (testUser.ok) {
      const invalidResult = await client.getProject(99999);
      assert(!invalidResult.ok, 'Should fail for invalid project');
      logTest('Invalid Project Handling', true, `Status: ${invalidResult.status}`);
    }
    
    return true;
  } catch (error) {
    logTest('Error Handling', false, error.message);
    return false;
  }
}

// ========================================
// Main Test Runner
// ========================================
async function runAllTests() {
  console.clear();
  console.log('🚀 SILIQUESTA Integration Test Suite');
  console.log('═'.repeat(50));
  
  testResults = { passed: 0, failed: 0, errors: [], logs: [] };
  
  // Run tests
  await testBackendConnection();
  await testAIServiceConnection();
  await testAuthentication();
  await testProjectManagement();
  await testProjectSharing();
  await testSimulation();
  await testAIServiceIntegration();
  await testErrorHandling();
  
  // Print summary
  console.log('\n' + '═'.repeat(50));
  console.log('📊 Test Summary:');
  console.log(`✅ Passed: ${testResults.passed}`);
  console.log(`❌ Failed: ${testResults.failed}`);
  console.log('═'.repeat(50));
  
  if (testResults.errors.length > 0) {
    console.log('\n❌ Failed Tests:');
    testResults.errors.forEach(error => {
      console.log(`\n- ${error.test}`);
      console.log(`  ${error.details}`);
    });
  }
  
  // Overall result
  const allPassed = testResults.failed === 0;
  const resultIcon = allPassed ? '✅' : '❌';
  console.log(`\n${resultIcon} Overall: ${allPassed ? 'PASSED' : 'FAILED'}`);
  
  return {
    passed: testResults.passed,
    failed: testResults.failed,
    allPassed,
    logs: testResults.logs,
    errors: testResults.errors
  };
}

// Export for use
console.log('🧪 Integration tests loaded! Run: runAllTests()');
