import express from 'express';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createProxyMiddleware } from 'http-proxy-middleware';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const port = process.env.PORT || 3000;
const apiTarget = process.env.API_TARGET || 'http://127.0.0.1:5000';

app.use(createProxyMiddleware({ target: apiTarget, changeOrigin: true, pathFilter: '/api' }));
app.use(express.static(path.join(__dirname, 'public')));

app.listen(port, () => {
  console.log(`radiocalico web listening on http://localhost:${port} (proxying /api to ${apiTarget})`);
});
