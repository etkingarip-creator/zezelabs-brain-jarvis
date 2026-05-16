const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    title: "JARVIS PRO — Zezelabs Holding",
    backgroundColor: '#05080F',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    // Menü çubuğunu gizle (Unicorn estetiği için)
    autoHideMenuBar: true,
  });

  // Vite dev server'a bağlan (veya build edilmiş dosyayı yükle)
  win.loadURL('http://localhost:5173');
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
