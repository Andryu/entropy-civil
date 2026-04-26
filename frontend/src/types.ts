export interface AgentState {
  id: string;
  name: string;
  x: number;
  y: number;
  emotion: string;
  action: string;
  speech: string;
}

export interface SandboxState {
  turn: number;
  agents: AgentState[];
}

export interface UniverseParticleData {
  id: string;
  text: string;
  position: [number, number, number];
  importance: number;
  isLegend: boolean;
  agent_id: string;
}

export interface UniverseResponse {
  data?: UniverseParticleData[];
  error?: string;
}

export interface HistoryLog {
  id: number;
  turn: number;
  type: string;
  content: string;
}

export interface HistoryResponse {
  logs?: HistoryLog[];
}

export interface Epoch {
  id: number;
  name: string;
  turn_start: number;
  turn_end?: number | null;
  master_prompt?: string | null;
  image_url?: string | null;
}

export interface EpochsResponse {
  epochs?: Epoch[];
}
