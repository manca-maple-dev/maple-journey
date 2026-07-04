const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  const target = "http://127.0.0.1:8000";

  app.use(
    ["/api", "/docs", "/openapi.json", "/redoc", "/health"],
    createProxyMiddleware({
      target,
      changeOrigin: true,
      ws: true,
      logLevel: "warn",
    })
  );
};
