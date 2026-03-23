importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyDDXa_QG5im7rGD5aHQd4AyZRPBYFrcEXk",
  authDomain: "hkjc-v2.firebaseapp.com",
  projectId: "hkjc-v2",
  storageBucket: "hkjc-v2.firebasestorage.app",
  messagingSenderId: "543594191307",
  appId: "1:543594191307:web:866299dce445c71a39f99f",
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/favicon.ico'
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});
