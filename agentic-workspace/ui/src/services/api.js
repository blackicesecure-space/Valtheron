const API_BASE = import.meta.env.DEV ? 'http://localhost:3000/api' : '/api';

async function fetchAPI(endpoint) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  getHealth: () => fetchAPI('/health'),
  getWorkspaceConfig: () => fetchAPI('/workspace/config'),
  getAgents: () => fetchAPI('/agents'),
  getWorkflows: () => fetchAPI('/workflows'),
  getTasks: () => fetchAPI('/tasks'),
  getTools: () => fetchAPI('/tools'),
  getLogs: (limit = 100) => fetchAPI(`/logs?limit=${limit}`),
  getStats: () => fetchAPI('/stats')
};
