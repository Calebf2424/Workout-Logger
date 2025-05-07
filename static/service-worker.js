self.addEventListener("install", (event) => {
    console.log("Service worker installed.");
  });
  
  self.addEventListener("fetch", (event) => {
    // Default: just let network handle it
  });
  