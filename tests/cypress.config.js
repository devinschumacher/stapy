const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    "baseUrl": "http://127.0.0.1:1985/",
    "viewportWidth": 1280,
    "viewportHeight": 1080,
    "supportFile": false
  },
});
