button = document.getElementById('add-url');

button.addEventListener('click', async () => {
  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    const activeTab = tabs[0];
    const url = activeTab.url;
    const responseArea = document.getElementById('response-area');

    button.disabled = true;
    responseArea.innerHTML = `<p style="text-align: center;">Saving page...</p>`;
    try {
      const response = await fetch(`https://create-notion-page-ny7vkn2pgq-ew.a.run.app?url=${encodeURIComponent(url)}`);
      const result = await response.text();

      if (!response.ok) {
        throw new Error(result);
      } 
      
      console.log('Success:', result);
      message = `<p style="text-align: center;"><a href="${result}" target="_blank">New page created!</a></p>`;
    } catch (error) {
      console.error(error);
      message = `<p style="text-align: center;">There was an error: ${error.message}</p>`;
    }

    button.disabled = false;
    responseArea.innerHTML = message;
  });
});
