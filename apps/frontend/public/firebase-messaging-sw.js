// Firebase Cloud Messaging Service Worker
// This file is required for Firebase Cloud Messaging to work properly

// Import Firebase scripts (if needed in the future)
// importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
// importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

// Currently a placeholder service worker
// If you plan to use Firebase Cloud Messaging, configure it here

self.addEventListener('install', (event) => {
  console.log('Firebase messaging service worker installed');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('Firebase messaging service worker activated');
  event.waitUntil(self.clients.claim());
});

// Handle background messages (when app is not in focus)
self.addEventListener('push', (event) => {
  console.log('Background message received:', event);
  
  // You can add custom push notification handling here if needed
  // For now, this prevents the 404 error
});
