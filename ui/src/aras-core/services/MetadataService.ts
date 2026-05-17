/**
 * Purpose: Central service for interacting with Aras Resource Metadata.
 * Context: Frontend Core. Consumes /metadata endpoints.
 * Impact: Provides the data needed for dynamic UI generation.
 */
import api from '../../lib/api';

const _cache = new Map<string, unknown>();

export const MetadataService = {
  async getResourceMetadata(resourcePath: string) {
    if (_cache.has(resourcePath)) return _cache.get(resourcePath);
    const response = await api.get(`/metadata/${resourcePath}`);
    _cache.set(resourcePath, response.data);
    return response.data;
  },

  clearCache() {
    _cache.clear();
  },

  invalidate(resourcePath: string) {
    _cache.delete(resourcePath);
  },

  async queryResource(resourceName: string, filters: unknown[] = []) {
    const response = await api.post(`/${resourceName}/query`, { filters });
    return response.data.items;
  }
};
