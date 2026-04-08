const API_BASE_URL = "http://127.0.0.1:8000";

export const API_ENDPOINTS = {
  UPLOAD_CONTRACT: `${API_BASE_URL}/api/contracts/upload`,
  GET_CONTRACT: (id: string) => `${API_BASE_URL}/api/contracts/${id}`,
  GET_VIN: (vin: string, contractId?: string) => 
    `${API_BASE_URL}/api/vehicles/vin/${vin}${contractId ? `?contract_id=${contractId}` : ""}`,
  CHAT: (contractId: string) => `${API_BASE_URL}/api/contracts/${contractId}/chat`,
};

export default API_BASE_URL;
