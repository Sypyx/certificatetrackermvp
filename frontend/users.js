// users.js

const API_AUTH_REGISTER = 'http://localhost:5001/auth/register';
const API_USERS = 'http://localhost:5002/users/';
const API_NOTIFY_USER = 'http://localhost:5004/notify/user/';

let accessToken = localStorage.getItem('accessToken');
let currentUser = JSON.parse(localStorage.getItem('currentUser'));

// Проверка, что менеджер залогинен
window.addEventListener('load', () => {
  accessToken = localStorage.getItem('accessToken');
  currentUser = JSON.parse(localStorage.getItem('currentUser'));
  if (!accessToken || !currentUser) {
    window.location.href = 'login.html';
    return;
  }

  // Если роль не менеджер — запрещаем заходить сюда
  if (currentUser.role !== 'manager') {
    alert('Доступ запрещён');
    window.location.href = 'login.html';
    return;
  }

  fetchUsers();
});

// Функция выхода
function logout() {
  localStorage.clear();
  window.location.href = 'login.html';
}

// Получаем список всех пользователей и рисуем таблицу
async function fetchUsers() {
  try {
    const resp = await fetch(API_USERS, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    const data = await resp.json();
    if (!resp.ok) {
      alert(data.msg || 'Ошибка при загрузке пользователей');
      return;
    }
    renderUsers(data.users);
  } catch (err) {
    alert('Ошибка при загрузке пользователей');
    console.error(err);
  }
}

// Рисуем таблицу пользователей
function renderUsers(users) {
  const tbody = document.getElementById('users-body');
  tbody.innerHTML = '';
  if (users.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8">Нет пользователей.</td></tr>';
    return;
  }

  users.forEach((u, index) => {
    const tr = document.createElement('tr');

    // Ячейка ID (скрыта CSS-классом .col-id)
    const tdId = document.createElement('td');
    tdId.classList.add('col-id');
    tdId.innerText = u.id;
    tr.appendChild(tdId);

    // Ячейка ФИО → здесь создаём ссылку на certificates.html
    const tdUsername = document.createElement('td');
    const a = document.createElement('a');
    const encodedName = encodeURIComponent(u.username);
    a.href = `certificates.html?user_id=${u.id}&username=${encodedName}`;
    a.innerText = u.username;
    tdUsername.appendChild(a);
    tr.appendChild(tdUsername);

    // Ячейка Email
    const tdEmail = document.createElement('td');
    tdEmail.innerText = u.email;
    tr.appendChild(tdEmail);

    // Ячейка Телефон (новая)
    const tdPhone = document.createElement('td');
    tdPhone.innerText = u.phone || '—';
    tr.appendChild(tdPhone);

    // Ячейка Role (скрыта CSS-классом .col-role)
    const tdRole = document.createElement('td');
    tdRole.classList.add('col-role');
    tdRole.innerText = u.role;
    tr.appendChild(tdRole);

    // Ячейка «Ближайший сертификат» (если такой field есть)
    const tdNextCert = document.createElement('td');
    tdNextCert.innerText = u.next_certificate || '—';
    tr.appendChild(tdNextCert);

    // Ячейка «Дней до конца» (если field days_left есть)
    const tdDaysLeft = document.createElement('td');
    tdDaysLeft.innerText = u.days_left !== undefined ? `${u.days_left} дн.` : '—';
    tr.appendChild(tdDaysLeft);

    // Колонка «Уведомление» — кнопка «Уведомить»
    const tdNotify = document.createElement('td');
    const notifyBtn = document.createElement('button');
    notifyBtn.innerText = 'Уведомить';
    notifyBtn.onclick = () => sendNotificationToUser(u.id);
    tdNotify.appendChild(notifyBtn);
    tr.appendChild(tdNotify);

    tbody.appendChild(tr);
  });
}

// Отправляет уведомление о ближайшем сертификате конкретному пользователю
async function sendNotificationToUser(userId) {
  if (!confirm('Отправить уведомление пользователю?')) return;

  const token = localStorage.getItem('accessToken');
  if (!token) {
    alert('Ошибка: отсутствует токен');
    return;
  }

  try {
    const resp = await fetch(`${API_NOTIFY_USER}${userId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const data = await resp.json();
    if (!resp.ok) {
      alert(data.msg || 'Ошибка при отправке уведомления');
    } else {
      alert(data.msg);
    }
  } catch (err) {
    alert('Ошибка при обращении к серверу уведомлений');
    console.error(err);
  }
}

// Функция-фильтр для поиска по имени (ФИО)
function filterUsers() {
  const keyword = document.getElementById('search-input').value.toLowerCase();
  const rows = document.querySelectorAll('#users-body tr');
  rows.forEach(row => {
    const nameCell = row.querySelector('td:nth-child(2)');
    if (nameCell) {
      const name = nameCell.innerText.toLowerCase();
      row.style.display = name.includes(keyword) ? '' : 'none';
    }
  });
}

// Переключает видимость формы добавления
function toggleAddForm() {
  const form = document.getElementById('add-user-form');
  form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

// Создаёт нового пользователя (через POST /auth/register)
async function submitNewUser() {
  const username = document.getElementById('new-username').value.trim();
  const email = document.getElementById('new-email').value.trim();
  const password = document.getElementById('new-password').value;
  const phone = document.getElementById('new-phone').value.trim();  // новое поле
  const role = document.getElementById('new-role').value;

  if (!username || !email || !password) {
    alert('Заполните все поля');
    return;
  }

  try {
    const resp = await fetch(API_AUTH_REGISTER, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`  // токен manager
      },
      body: JSON.stringify({ username, email, password, phone, role })
    });
    const data = await resp.json();
    if (!resp.ok) {
      alert(data.msg || 'Ошибка при создании пользователя');
    } else {
      alert('Пользователь добавлен');
      toggleAddForm();
      fetchUsers();
    }
  } catch (err) {
    alert('Ошибка при создании пользователя');
    console.error(err);
  }
}
