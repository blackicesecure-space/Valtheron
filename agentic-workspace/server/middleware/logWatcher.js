const chokidar = require('chokidar');
const fs = require('fs');
const path = require('path');
const { broadcast } = require('../websocket/websocketServer');

class LogWatcher {
  constructor() {
    this.watcher = null;
    this.logDir = path.join(__dirname, '../../logs');
    this.filePositions = new Map();
  }

  start(wss) {
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
      console.log(`Created logs directory: ${this.logDir}`);
    }

    console.log(`Starting log watcher on: ${this.logDir}`);

    this.watcher = chokidar.watch(this.logDir, {
      persistent: true,
      ignoreInitial: false,
      awaitWriteFinish: {
        stabilityThreshold: 500,
        pollInterval: 100
      }
    });

    this.watcher
      .on('add', filePath => this.handleFileAdd(filePath))
      .on('change', filePath => this.handleFileChange(filePath))
      .on('error', error => console.error('Log watcher error:', error));

    console.log('Log watcher started successfully');
  }

  handleFileAdd(filePath) {
    if (!filePath.endsWith('.json') && !filePath.endsWith('.log')) {
      return;
    }

    console.log(`New log file detected: ${filePath}`);

    try {
      const stats = fs.statSync(filePath);
      this.filePositions.set(filePath, stats.size);

      this.readNewLines(filePath, 0);
    } catch (error) {
      console.error(`Error handling file add for ${filePath}:`, error);
    }
  }

  handleFileChange(filePath) {
    if (!filePath.endsWith('.json') && !filePath.endsWith('.log')) {
      return;
    }

    try {
      const lastPosition = this.filePositions.get(filePath) || 0;
      this.readNewLines(filePath, lastPosition);

      const stats = fs.statSync(filePath);
      this.filePositions.set(filePath, stats.size);
    } catch (error) {
      console.error(`Error handling file change for ${filePath}:`, error);
    }
  }

  readNewLines(filePath, startPosition) {
    try {
      const stats = fs.statSync(filePath);

      if (stats.size <= startPosition) {
        return;
      }

      const stream = fs.createReadStream(filePath, {
        encoding: 'utf8',
        start: startPosition
      });

      let buffer = '';

      stream.on('data', chunk => {
        buffer += chunk;
        const lines = buffer.split('\n');

        buffer = lines.pop() || '';

        lines.forEach(line => {
          if (line.trim()) {
            this.processLogLine(line, filePath);
          }
        });
      });

      stream.on('end', () => {
        if (buffer.trim()) {
          this.processLogLine(buffer, filePath);
        }
      });

      stream.on('error', error => {
        console.error(`Error reading log file ${filePath}:`, error);
      });
    } catch (error) {
      console.error(`Error in readNewLines for ${filePath}:`, error);
    }
  }

  processLogLine(line, filePath) {
    let logEntry;

    if (filePath.endsWith('.json')) {
      try {
        logEntry = JSON.parse(line);
        logEntry.source = path.basename(filePath);
      } catch (error) {
        logEntry = {
          raw: line,
          source: path.basename(filePath),
          timestamp: new Date().toISOString(),
          parseError: true
        };
      }
    } else {
      logEntry = {
        raw: line,
        source: path.basename(filePath),
        timestamp: new Date().toISOString(),
        level: this.inferLogLevel(line)
      };
    }

    broadcast({
      type: 'log',
      data: logEntry,
      timestamp: Date.now()
    });
  }

  inferLogLevel(line) {
    const lowerLine = line.toLowerCase();
    if (lowerLine.includes('error') || lowerLine.includes('fail')) return 'error';
    if (lowerLine.includes('warn')) return 'warning';
    if (lowerLine.includes('info')) return 'info';
    if (lowerLine.includes('debug')) return 'debug';
    return 'info';
  }

  stop() {
    if (this.watcher) {
      console.log('Stopping log watcher');
      this.watcher.close();
      this.filePositions.clear();
    }
  }
}

const logWatcher = new LogWatcher();

module.exports = {
  logWatcher
};
