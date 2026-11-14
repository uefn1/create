// Minecraft コンテンツを取得して HTML に埋め込む
fetch('data.json')
    .then(response => response.json())
    .then(data => {
        const contentDiv = document.getElementById('minecraft-content');
        data.forEach(item => {
            const contentElement = document.createElement('pre');
            contentElement.textContent = item.content;
            contentDiv.appendChild(contentElement);
        });
    })
    .catch(error => console.error('Error fetching data:', error));