/**
 * Purpose: Central service for interacting with Aras Resource Metadata.
 * Context: Frontend Core. Consumes /metadata endpoints.
 * Impact: Provides the data needed for dynamic UI generation.
 */
import api from '../../lib/api';

export const MetadataService = {
  /**
   * Fetches schema and layout for a given resource.
   */
  async getResourceMetadata(resourcePath: string) {
    const cleanPath = resourcePath.startsWith('/') ? resourcePath.substring(1) : resourcePath;
    const response = await api.get(`/metadata/${cleanPath}`);
    return response.data;
  }
,

  /**
   * Fetches data for a resource using the Query API.
   * resourceName should be the table name (without app prefix in the URL path for /query).
   */
  async queryResource(resourceName: string, filters: any[] = []) {
    const response = await api.post(`/${resourceName}/query`, { filters });
    return response.data.items;
  }
};
