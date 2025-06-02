// auth.js

const API_AUTH = 'http://localhost:5001';

async function login() {
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value.trim();

  if (!username || !password) {
    alert('Введите username и password.');
    return;
  }

  try {
    const resp = await fetch(`${API_AUTH}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await resp.json();

    if (resp.ok && data.access_token) {
      localStorage.setItem('accessToken', data.access_token);
      localStorage.setItem('currentUser', JSON.stringify(data.user));

      // После входа проверяем роль
      if (data.user.role === 'manager') {
        window.location.href = 'users.html';
      } else {
        window.location.href = `certificates.html?user_id=${data.user.id}&username=${encodeURIComponent(data.user.username)}`;
      }
    } else {
      alert(data.msg || 'Неправильный username или password');
    }
  } catch (err) {
    alert('Сервер недоступен. Попробуйте позже.');
    console.error(err);
  }
}

async function register() {
  const username = document.getElementById('reg-username').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value.trim();
  const phone = document.getElementById('reg-phone').value.trim(); // новоё поле

  if (!username || !email || !password) {
    alert('Заполните все поля.');
    return;
  }

  try {
    const resp = await fetch(`${API_AUTH}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        email,
        password,
        phone,       // передаём phone
        role: 'user'
      })
    });
    const data = await resp.json();
    if (resp.ok) {
      alert('Регистрация прошла успешно. Перейдите для входа.');
      window.location.href = 'login.html';
    } else {
      alert(data.msg || 'Ошибка регистрации');
    }
  } catch (err) {
    alert('Сервер недоступен. Попробуйте позже.');
    console.error(err);
  }
}

// Если пользователь уже залогинен, сразу редиректим
window.addEventListener('load', () => {
  const token = localStorage.getItem('accessToken');
  const user = localStorage.getItem('currentUser');
  if (token && user) {
    const u = JSON.parse(user);
    if (u.role === 'manager') {
      window.location.href = 'users.html';
    } else {
      window.location.href = `certificates.html?user_id=${u.id}&username=${encodeURIComponent(u.username)}`;
    }
  }
});
