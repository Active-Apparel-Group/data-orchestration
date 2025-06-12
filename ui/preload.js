const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    loadCustomers: () => ipcRenderer.invoke('load-customers'),
    saveCustomers: (customers) => ipcRenderer.invoke('save-customers', customers)
});
