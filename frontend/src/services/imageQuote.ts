import axios from 'axios';

const API_BASE = 'https://4tgzh3l5-8004.inc1.devtunnels.ms';

export async function processImageForQuote(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post(`${API_BASE}/api/image/process-image`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}
