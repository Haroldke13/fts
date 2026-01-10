const socket = io();
socket.on('file_update', (data) => {
    console.log('Files updated:', data.files);
    // Update UI dynamically
});
