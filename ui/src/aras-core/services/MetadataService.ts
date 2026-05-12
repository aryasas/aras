/**
 * Purpose: Central service for interacting with Aras Resource Metadata.
 * Context: Frontend Core. Consumes /metadata endpoints.
 * Impact: Provides the data needed for dynamic UI generation.
 */
import axios from 'axios';

const API_BASE = '/api/v1';

export const MetadataService = {
  /**
   * Fetches schema and layout for a given resource.
   */
  async getResourceMetadata(resourceName: string) {
    const response = await axios.get(`${API_BASE}/${resourceName}/metadata`);
    return response.data;
  },

  /**
   * Fetches data for a resource using the Query API.
   */
  async queryResource(resourceName: string, filters: any[] = []) {
    const response = await axios.post(`${API_BASE}/query/${resourceName}`, filters);
    return response.data;
  }
};
