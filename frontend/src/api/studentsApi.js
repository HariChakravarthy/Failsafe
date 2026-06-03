import client from "./axiosClient";

export const studentsApi = {
  list: async (params) => {
    const { data } = await client.get("/students", { params });
    return data;
  },
  get: async (id) => {
    const { data } = await client.get(`/students/${id}`);
    return data;
  },
  upload: async (file, weekNumber = 1, phase = 0) => {
    const form = new FormData();
    form.append("file", file);
    const { data } = await client.post(
      `/students/upload?week_number=${weekNumber}&phase=${phase}`,
      form,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return data;
  },
  update: async (id, payload) => {
    const { data } = await client.patch(`/students/${id}`, payload);
    return data;
  },
  downloadReport: async (id) => {
    const response = await client.get(`/students/${id}/report`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

