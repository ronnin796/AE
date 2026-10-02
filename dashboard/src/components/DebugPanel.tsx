import { useState } from "react";
import { useDebug, SystemEvent } from "../context/DebugContext";

export default function DebugPanel() {
  const { events, clearEvents } = useDebug();
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  const filteredEvents = filter === "all" 
    ? events 
    : events.filter(e => e.type === filter);

  const getEventColor = (type: string) => {
    switch (type) {
      case "connect": return "var(--accent-success)";
      case "disconnect": return "var(--accent-danger)";
      case "heartbeat": return "var(--accent-primary)";
      case "telemetry": return "var(--accent-info)";
      case "command": return "var(--accent-warning)";
      case "error": return "var(--accent-danger)";
      default: return "var(--text-secondary)";
    }
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case "connect": return "🔌";
      case "disconnect": return "🔌";
      case "heartbeat": return "💓";
      case "telemetry": return "📊";
      case "command": return "⚡";
      case "error": return "⚠️";
      default: return "📝";
    }
  };

  return (
    <div className="card debug-panel" style={{ maxHeight: '400px', display: 'flex', flexDirection: 'column' }}>
      <header className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <h3 className="card-title" style={{ marginBottom: 0 }}>Debug Panel</h3>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}>
            <input 
              type="checkbox" 
              checked={autoScroll} 
              onChange={(e) => setAutoScroll(e.target.checked)} 
            />
            Auto-scroll
          </label>
          <select 
            className="input select" 
            style={{ width: 'auto', minWidth: '120px', fontSize: '0.75rem' }}
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All Events</option>
            <option value="connect">Connections</option>
            <option value="disconnect">Disconnections</option>
            <option value="heartbeat">Heartbeats</option>
            <option value="telemetry">Telemetry</option>
            <option value="command">Commands</option>
            <option value="error">Errors</option>
          </select>
          <button className="btn btn-secondary btn-sm" onClick={clearEvents} style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}>
            Clear
          </button>
        </div>
      </header>

      <div 
        className="debug-events" 
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          maxHeight: '300px',
          fontSize: '0.75rem',
          fontFamily: 'var(--font-mono)',
        }}
        role="log"
        aria-live="polite"
      >
        {filteredEvents.length === 0 ? (
          <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-tertiary)' }}>
            No events yet. Start nodes to see activity.
          </div>
        ) : (
          filteredEvents.slice().reverse().map((event) => (
            <div 
              key={event.id}
              className="debug-event"
              style={{ 
                padding: '0.375rem 0.5rem', 
                borderBottom: '1px solid var(--border-primary)',
                display: 'flex',
                gap: '0.5rem',
                alignItems: 'flex-start',
              }}
            >
              <span style={{ color: 'var(--text-tertiary)', whiteSpace: 'nowrap', minWidth: '80px' }}>
                {new Date(event.timestamp).toLocaleTimeString()}
              </span>
              <span style={{ color: getEventColor(event.type), whiteSpace: 'nowrap', minWidth: '16px' }}>
                {getEventIcon(event.type)}
              </span>
              <span style={{ color: 'var(--accent-primary)', whiteSpace: 'nowrap', minWidth: '80px' }}>
                {event.node_id}
              </span>
              <span style={{ color: 'var(--text-secondary)', flex: 1 }}>
                {event.message}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}