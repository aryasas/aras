/**
 * Purpose: Central service for interacting with Aras Resource Metadata.
 * Context: Frontend Core. Consumes /metadata endpoints.
 * Impact: Provides the data needed for dynamic UI generation.
 */
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';

const _cache = new Map<string, unknown>();

export const MetadataService = {
  async getResourceMetadata(resourcePath: string) {
    const cleanPath = cleanResourcePath(resourcePath);
    if (_cache.has(cleanPath)) return _cache.get(cleanPath);
    const response = await api.get(`/metadata/${cleanPath}`);
    _cache.set(cleanPath, response.data);
    return response.data;
  },

  clearCache() {
    _cache.clear();
  },

  invalidate(resourcePath: string) {
    _cache.delete(cleanResourcePath(resourcePath));
  },

  async queryResource(resourceName: string, filters: unknown[] = []) {
    const response = await api.post(`/${resourceName}/query`, { filters });
    return response.data.items;
  }
};
