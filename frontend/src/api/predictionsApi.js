import client from "./axiosClient";

export const predictionsApi = {
  getLatest: async (studentId) => {
    const { data } = await client.get(`/predictions/${studentId}`);
    return data;
  },
  getHistory: async (studentId) => {
    const { data } = await client.get(`/predictions/${studentId}/history`);
    return data;
  },
  simulate: async (studentId, overrides) => {
    const { data } = await client.post(`/predictions/${studentId}/simulate`, overrides);
    return data;
  },
};

