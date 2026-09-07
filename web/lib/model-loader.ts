import {
  GLTFLoader,
  type GLTF,
} from 'three/examples/jsm/loaders/GLTFLoader.js';

/** Gzip is lossless: geometry, morph targets and animation tracks stay intact. */
export async function loadPublicModel(
  url: string,
  onLoad: (model: GLTF) => void,
  onProgress: (event: { loaded: number; total: number }) => void,
  onError: (error: unknown) => void,
  signal: AbortSignal,
) {
  try {
    const compressedUrl = url.replace(/\.glb(?=\?|$)/, '.glb.gz');
    const response = await fetch(compressedUrl, { signal });
    if (!response.ok || !response.body)
      throw new Error(`Model HTTP ${response.status}`);
    const total = Number(response.headers.get('content-length')) || 0;
    let loaded = 0;
    const stream = response.body.pipeThrough(
      new TransformStream<Uint8Array, Uint8Array>({
        transform(chunk, controller) {
          loaded += chunk.byteLength;
          onProgress({ loaded, total });
          controller.enqueue(chunk);
        },
      }),
    );
    const bytes = await new Response(
      new Response(stream).body!.pipeThrough(new DecompressionStream('gzip')),
    ).arrayBuffer();
    if (signal.aborted) return;
    const model = await new GLTFLoader().parseAsync(
      bytes,
      new URL('.', response.url).href,
    );
    onLoad(model);
  } catch (error) {
    if (!signal.aborted) onError(error);
  }
}
