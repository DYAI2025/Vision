export type Service = {
  id: string;
  name: string;
  healthPath: string;
};

export const services: Service[] = [
  {
    id: "whatsorga-ingest",
    name: "Intake",
    healthPath: "/v1/health/whatsorga-ingest",
  },
  {
    id: "hermes-runtime",
    name: "Intelligence",
    healthPath: "/v1/health/hermes-runtime",
  },
  {
    id: "backlog-core",
    name: "Truth Store",
    healthPath: "/v1/health/backlog-core",
  },
  {
    id: "gbrain-bridge",
    name: "Vault Bridge",
    healthPath: "/v1/health/gbrain-bridge",
  },
  {
    id: "kanban-sync",
    name: "Kanban Sync",
    healthPath: "/v1/health/kanban-sync",
  },
];
