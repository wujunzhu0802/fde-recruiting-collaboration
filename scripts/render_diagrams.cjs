// Usage: node scripts/render_diagrams.cjs [path-to-@resvg/resvg-js]
// Optional build tool only; the application itself has no npm dependencies.
const fs = require('node:fs');
const path = require('node:path');
const { Resvg } = require(process.argv[2] || '@resvg/resvg-js');
const root = path.resolve(__dirname, '..');
const source = path.join(root, 'docs/diagrams/as-is-no-ai.svg');
const renderer = new Resvg(fs.readFileSync(source), {
  font: { loadSystemFonts: true, defaultFontFamily: 'Microsoft YaHei' }
});
const result = renderer.render();
fs.writeFileSync(source.replace(/\.svg$/, '.png'), result.asPng());
console.log(`Rendered PNG: ${result.width} × ${result.height}`);
