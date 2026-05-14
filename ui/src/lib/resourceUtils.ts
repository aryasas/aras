/** Strips a leading slash from a resource path for consistent API calls. */
export function cleanResourcePath(resource: string): string {
  return resource.startsWith('/') ? resource.substring(1) : resource
}
