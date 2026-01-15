const http = require('http');

console.log('Testing Agentic Workspace Dashboard...\n');

const tests = [
  { name: 'Health Check', path: '/api/health' },
  { name: 'Workspace Config', path: '/api/workspace/config' },
  { name: 'Agents', path: '/api/agents' },
  { name: 'Workflows', path: '/api/workflows' },
  { name: 'Tasks', path: '/api/tasks' },
  { name: 'Tools', path: '/api/tools' },
  { name: 'Stats', path: '/api/stats' },
  { name: 'Logs', path: '/api/logs?limit=10' }
];

function testEndpoint(test) {
  return new Promise((resolve) => {
    const req = http.get(`http://localhost:3000${test.path}`, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log(`✓ ${test.name}: OK (${res.statusCode})`);
          resolve(true);
        } else {
          console.log(`✗ ${test.name}: FAILED (${res.statusCode})`);
          resolve(false);
        }
      });
    });

    req.on('error', (error) => {
      console.log(`✗ ${test.name}: ERROR - ${error.message}`);
      resolve(false);
    });

    req.setTimeout(5000, () => {
      console.log(`✗ ${test.name}: TIMEOUT`);
      req.destroy();
      resolve(false);
    });
  });
}

async function runTests() {
  console.log('Running API endpoint tests...\n');

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    const result = await testEndpoint(test);
    if (result) {
      passed++;
    } else {
      failed++;
    }
  }

  console.log(`\nTest Results: ${passed} passed, ${failed} failed`);

  if (failed === 0) {
    console.log('✓ All tests passed!');
  } else {
    console.log('✗ Some tests failed. Check the output above.');
  }
}

runTests();
