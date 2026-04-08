const functions = require('firebase-functions');
const http = require('http');

// Proxy API calls to the VM
exports.apiProxy = functions.https.onRequest((req, res) => {
  // Set CORS headers
  res.set('Access-Control-Allow-Origin', '*');
  res.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.set('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.status(204).send('');
    return;
  }

  const vmHost = '45.32.255.155';
  const vmPort = 8000;
  const path = req.path;
  const query = req.url.includes('?') ? req.url.split('?')[1] : '';
  
  const options = {
    hostname: vmHost,
    port: vmPort,
    path: path + (query ? '?' + query : ''),
    method: req.method,
    headers: {
      'Content-Type': 'application/json'
    }
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.status(proxyRes.statusCode);
    res.set('Content-Type', proxyRes.headers['content-type'] || 'application/json');
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (error) => {
    console.error('Proxy error:', error);
    res.status(500).json({ error: 'Proxy error', details: error.message });
  });

  if (req.body) {
    proxyReq.write(JSON.stringify(req.body));
  }
  
  proxyReq.end();
});
