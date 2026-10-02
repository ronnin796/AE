export interface Node {
  id: number;
  node_id: string;
  hostname: string;
  os: string;
  os_version?: string;
  kernel_version?: string;
  cpu_brand?: string;
  cpu_cores?: number;
  total_memory?: number;
  version?: string;
  arch?: string;
  capabilities?: string[];
  tags?: Record<string, string> | null;
  status: 'online' | 'offline' | 'degraded' | 'maintenance';
  last_seen: string;
  created_at: string;
  updated_at: string;
}

export interface Telemetry {
  id: number;
  node_id: string;
  timestamp: string;
  cpu_usage?: number;
  cpu_per_core?: number[];
  memory_usage?: number;
  memory_total?: number;
  memory_available?: number;
  memory_used?: number;
  temperature?: number;
  temperatures?: number[];
  uptime?: number;
  load_1?: number;
  load_5?: number;
  load_15?: number;
  processes_running?: number;
  processes_total?: number;
}

export interface NodeListResponse {
  nodes: Node[];
  total: number;
  page: number;
  page_size: number;
}

export interface TelemetryAggregated {
  node_id: string;
  timestamps: number[];
  cpu_usage: (number | null)[];
  memory_usage: (number | null)[];
  temperature: (number | null)[];
  load_1: (number | null)[];
}

export interface TelemetryStats {
  node_id: string;
  count: number;
  avg_cpu?: number;
  max_cpu?: number;
  avg_memory?: number;
  max_memory?: number;
  avg_temperature?: number;
  max_temperature?: number;
  latest_timestamp?: number;
}