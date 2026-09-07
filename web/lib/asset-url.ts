/** Public files must resolve inside the GitHub Pages project path. */
export function assetUrl(path: string): string {
  return path.startsWith('/')
    ? `${process.env.NEXT_PUBLIC_BASE_PATH || ''}${path}`
    : path;
}
