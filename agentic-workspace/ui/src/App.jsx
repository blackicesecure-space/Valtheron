import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { StatCard } from './components/StatCard';
import { LogViewer } from './components/LogViewer';
import { ConfigList } from './components/ConfigList';
import { useWebSocket } from './hooks/useWebSocket';
import { api } from './services/api';
import './App.css';

function App() {
  const { connectionStatus, logs } = useWebSocket();
  const [stats, setStats] = useState({ agents: 0, workflows: 0, tasks: 0, tools: 0 });
  const [agents, setAgents] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsData, agentsData, workflowsData, tasksData, toolsData] = await Promise.all([
        api.getStats(),
        api.getAgents(),
        api.getWorkflows(),
        api.getTasks(),
        api.getTools()
      ]);

      setStats(statsData);
      setAgents(agentsData);
      setWorkflows(workflowsData);
      setTasks(tasksData);
      setTools(toolsData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <Header connectionStatus={connectionStatus} />

      <main className="main-content">
        <div className="container">
          {loading ? (
            <div className="loading">Loading dashboard...</div>
          ) : (
            <>
              <section className="stats-section">
                <StatCard
                  title="Agents"
                  value={stats.agents}
                  icon="🤖"
                  color="#3b82f6"
                />
                <StatCard
                  title="Workflows"
                  value={stats.workflows}
                  icon="⚙️"
                  color="#10b981"
                />
                <StatCard
                  title="Tasks"
                  value={stats.tasks}
                  icon="📋"
                  color="#f59e0b"
                />
                <StatCard
                  title="Tools"
                  value={stats.tools}
                  icon="🔧"
                  color="#8b5cf6"
                />
              </section>

              <section className="main-grid">
                <div className="config-column">
                  <ConfigList
                    title="Agents"
                    items={agents}
                    icon="🤖"
                    color="#3b82f6"
                  />
                  <ConfigList
                    title="Workflows"
                    items={workflows}
                    icon="⚙️"
                    color="#10b981"
                  />
                  <ConfigList
                    title="Tasks"
                    items={tasks}
                    icon="📋"
                    color="#f59e0b"
                  />
                  <ConfigList
                    title="Tools"
                    items={tools}
                    icon="🔧"
                    color="#8b5cf6"
                  />
                </div>

                <div className="log-column">
                  <LogViewer logs={logs} />
                </div>
              </section>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
