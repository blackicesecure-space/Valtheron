const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const workspaceRoot = path.join(__dirname, '../..');

function readJSONFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    console.error(`Error reading JSON file ${filePath}:`, error);
    return null;
  }
}

function readYAMLFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return yaml.load(content);
  } catch (error) {
    console.error(`Error reading YAML file ${filePath}:`, error);
    return null;
  }
}

function readConfigDirectory(dirName) {
  const dirPath = path.join(workspaceRoot, dirName);
  const items = [];

  try {
    if (!fs.existsSync(dirPath)) {
      return items;
    }

    const files = fs.readdirSync(dirPath);

    files.forEach(file => {
      if (file.startsWith('.') || file.endsWith('.schema.json')) {
        return;
      }

      const filePath = path.join(dirPath, file);
      let content = null;

      if (file.endsWith('.json')) {
        content = readJSONFile(filePath);
      } else if (file.endsWith('.yaml') || file.endsWith('.yml')) {
        content = readYAMLFile(filePath);
      }

      if (content) {
        items.push({
          filename: file,
          path: filePath,
          ...content
        });
      }
    });
  } catch (error) {
    console.error(`Error reading directory ${dirName}:`, error);
  }

  return items;
}

function readRecentLogs(limit = 100) {
  const logsDir = path.join(workspaceRoot, 'logs');
  const logs = [];

  try {
    if (!fs.existsSync(logsDir)) {
      return logs;
    }

    const files = fs.readdirSync(logsDir)
      .filter(f => f.endsWith('.json') || f.endsWith('.log'))
      .sort((a, b) => {
        const statA = fs.statSync(path.join(logsDir, a));
        const statB = fs.statSync(path.join(logsDir, b));
        return statB.mtime - statA.mtime;
      });

    for (const file of files.slice(0, 5)) {
      const filePath = path.join(logsDir, file);
      const content = fs.readFileSync(filePath, 'utf8');

      if (file.endsWith('.json')) {
        content.split('\n').filter(line => line.trim()).forEach(line => {
          try {
            logs.push(JSON.parse(line));
          } catch (e) {
            logs.push({ raw: line, error: 'Failed to parse JSON' });
          }
        });
      } else {
        content.split('\n').filter(line => line.trim()).forEach(line => {
          logs.push({ raw: line, timestamp: new Date().toISOString() });
        });
      }

      if (logs.length >= limit) {
        break;
      }
    }
  } catch (error) {
    console.error('Error reading logs:', error);
  }

  return logs.slice(0, limit);
}

function setupAPIRoutes(app) {
  app.get('/api/health', (req, res) => {
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime()
    });
  });

  app.get('/api/workspace/config', (req, res) => {
    const configPath = path.join(workspaceRoot, 'config', 'workspace.json');
    const config = readJSONFile(configPath);
    res.json(config || { error: 'Failed to load workspace config' });
  });

  app.get('/api/agents', (req, res) => {
    const agents = readConfigDirectory('agents');
    res.json(agents);
  });

  app.get('/api/workflows', (req, res) => {
    const workflows = readConfigDirectory('workflows');
    res.json(workflows);
  });

  app.get('/api/tasks', (req, res) => {
    const tasks = readConfigDirectory('tasks');
    res.json(tasks);
  });

  app.get('/api/tools', (req, res) => {
    const tools = readConfigDirectory('tools');
    res.json(tools);
  });

  app.get('/api/logs', (req, res) => {
    const limit = parseInt(req.query.limit) || 100;
    const logs = readRecentLogs(limit);
    res.json(logs);
  });

  app.get('/api/stats', (req, res) => {
    const agents = readConfigDirectory('agents');
    const workflows = readConfigDirectory('workflows');
    const tasks = readConfigDirectory('tasks');
    const tools = readConfigDirectory('tools');

    res.json({
      agents: agents.length,
      workflows: workflows.length,
      tasks: tasks.length,
      tools: tools.length,
      timestamp: new Date().toISOString()
    });
  });
}

module.exports = {
  setupAPIRoutes
};
