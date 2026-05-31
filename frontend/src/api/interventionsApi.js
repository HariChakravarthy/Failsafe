import client from "./axiosClient";

export const interventionsApi = {
  list: async (params) => {
    const { data } = await client.get("/interventions", { params });
    return data;
  },
  getByStudent: async (studentId) => {
    const { data } = await client.get(`/interventions/${studentId}`);
    return data;
  },
  updateStatus: async (id, status, notes, outcome, outcomeNotes) => {
    const { data } = await client.patch(`/interventions/${id}/status`, {
      status,
      notes,
      outcome,
      outcome_notes: outcomeNotes,
    });
    return data;
  },
  create: async (payload) => {
    const { data } = await client.post("/interventions", payload);
    return data;
  },
};

export const dashboardApi = {
  summary: async () => {
    const { data } = await client.get("/dashboard/summary");
    return data;
  },
  trends: async () => {
    const { data } = await client.get("/dashboard/trends");
    return data;
  },
};
