const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const yaml = require('js-yaml');

const YAML_PATH = path.resolve(__dirname, '../docs/mapping/customer_mapping.yaml');

function createWindow() {
    const win = new BrowserWindow({
        width: 1000,
        height: 700,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        }
    });
    win.loadFile('index.html');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

// IPC handlers for reading/writing YAML
ipcMain.handle('load-customers', async () => {
    const file = fs.readFileSync(YAML_PATH, 'utf8');
    const data = yaml.load(file);
    return data.customers || [];
});

ipcMain.handle('save-customers', async (event, customers) => {
    const file = fs.readFileSync(YAML_PATH, 'utf8');
    const data = yaml.load(file);
    data.customers = customers;
    fs.writeFileSync(YAML_PATH, yaml.dump(data, { lineWidth: -1 }));
    return true;
});
