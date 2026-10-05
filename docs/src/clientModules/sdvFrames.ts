import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';

// Sizes the iframes that show a notebook's interactive outputs. tools/render_notebooks.py writes each output as a
// standalone page under static/outputs/ and frames it as <iframe class="sdv-frame" height="480">; the page posts
// {sdvplotFrameHeight} to this window on load, on resize and when asked. Without JavaScript a frame keeps its
// height attribute.
const frames = (): NodeListOf<HTMLIFrameElement> => document.querySelectorAll('iframe.sdv-frame');

if (ExecutionEnvironment.canUseDOM) {
  window.addEventListener('message', (event: MessageEvent) => {
    const height = event.data?.sdvplotFrameHeight;
    if (event.origin !== window.location.origin || typeof height !== 'number' || !(height > 0)) return;
    for (const frame of frames()) {
      if (frame.contentWindow === event.source) {
        frame.style.height = `${Math.ceil(height)}px`;
        return;
      }
    }
  });
}

// A frame that loaded before this module ran, or before a client-side navigation finished, reported to no one: ask.
export function onRouteDidUpdate(): void {
  for (const frame of frames()) frame.contentWindow?.postMessage('sdvplot:height?', window.location.origin);
}
