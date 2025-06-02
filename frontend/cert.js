// cert.js

const API_CERT = 'http://localhost:5003/certificates/';
const API_NOTIFY_EMAIL = 'http://localhost:5004/notify/certificate/';
const API_NOTIFY_SMS = 'http://localhost:5004/notify/sms/';

let accessToken = localStorage.getItem('accessToken');
let currentUser = JSON.parse(localStorage.getItem('currentUser'));
let editingCertId = null;

// Параметры выбранного пользователя (для менеджера) или текущего (для user)
let selectedUserId = null;
let selectedUsername = null;

window.addEventListener('load', () => {
  // --- 1) Проверяем авторизацию ---
  accessToken = localStorage.getItem('accessToken');
  currentUser = JSON.parse(localStorage.getItem('currentUser'));
  if (!accessToken || !currentUser) {
    window.location.href = 'login.html';
    return;
  }

  // --- 2) Парсим параметры из URL: ?user_id=...&username=---
  const params = new URLSearchParams(window.location.search);
  if (params.has('user_id') && params.has('username')) {
    selectedUserId = parseInt(params.get('user_id'));
    selectedUsername = decodeURIComponent(params.get('username'));
  }

  // --- 3) Если роль менеджера и нет выбранного пользователя — возвращаемся к списку ---
  if (currentUser.role === 'manager' && !selectedUserId) {
    window.location.href = 'users.html';
    return;
  }

  // --- 4) Если обычный пользователь, назначаем selectedUserId ---
  if (currentUser.role === 'user') {
    selectedUserId = currentUser.id;
  }

  // --- 5) Изменяем заголовок для менеджера и показываем кнопку «Добавить сертификат» ---
  if (currentUser.role === 'manager') {
    document.getElementById('page-title').innerText =
      `Certificate Tracker — сертификаты пользователя ${selectedUsername}`;
    document.getElementById('new-cert-btn').style.display = 'block';

    // Показываем блок «Экспорт/Импорт Excel»
    document.getElementById('excel-tools').style.display = 'block';
  }

  // --- 6) Загружаем сертификаты ---
  fetchCertificates();
});

// Функция «Назад» (возвращает на users.html)
function goBack() {
  window.location.href = 'users.html';
}

// Функция выхода (очистка localStorage + редирект)
function logout() {
  localStorage.clear();
  window.location.href = 'login.html';
}

// Загрузить все сертификаты и отфильтровать только по selectedUserId
async function fetchCertificates() {
  try {
    const resp = await fetch(API_CERT, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });
    const data = await resp.json();
    if (!resp.ok) {
      alert(data.msg || 'Ошибка при загрузке сертификатов');
      return;
    }
    const filtered = data.certificates.filter(c => c.owner_id === selectedUserId);
    renderCertificates(filtered);
  } catch (err) {
    alert('Ошибка при загрузке сертификатов.');
    console.error(err);
  }
}

// Отрисовать сертификаты в таблице
function renderCertificates(certs) {
  const tbody = document.getElementById('cert-body');
  tbody.innerHTML = '';
  if (certs.length === 0) {
    // Если нет записей, показываем строку «Нет сертификатов»
    tbody.innerHTML = '<tr><td colspan="7">Нет сертификатов.</td></tr>';
    return;
  }

  certs.forEach((c, index) => {
    // Рассчитываем дни до конца
    const today = new Date();
    const endDate = new Date(c.date_end);
    const diffTime = endDate - today;
    const daysLeft = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    // Сначала создаём сам <tr> и вставляем базовые ячейки
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${c.name}</td>
      <td>${c.date_start}</td>
      <td>${c.date_end}</td>
      <td>${daysLeft >= 0 ? daysLeft + ' дн.' : 'Истёк'}</td>
      <td></td>
      <td></td>
    `;

    // Колонка «Действия» (редактировать/удалить) – только для менеджера
    if (currentUser.role === 'manager') {
      const tdAction = tr.querySelector('td:nth-child(6)');

      const editBtn = document.createElement('button');
      editBtn.innerText = 'Редактировать';
      editBtn.style.marginRight = '5px';
      editBtn.onclick = () => editCert(c);
      tdAction.appendChild(editBtn);

      const delBtn = document.createElement('button');
      delBtn.innerText = 'Удалить';
      delBtn.style.marginRight = '5px';
      delBtn.onclick = () => deleteCert(c.id);
      tdAction.appendChild(delBtn);
    }

    // Колонка «Уведомление» – находим 7-ю ячейку один раз
    const tdNotify = tr.querySelector('td:nth-child(7)');

    // Кнопка для e-mail
    const notifyBtn = document.createElement('button');
    notifyBtn.innerText = 'Отправить email уведомление';
    notifyBtn.onclick = () => sendNotification(c.id);
    notifyBtn.style.marginRight = '5px';
    tdNotify.appendChild(notifyBtn);

    // Кнопка для SMS
    const smsBtn = document.createElement('button');
    smsBtn.innerText = 'Отправить SMS уведомление';
    smsBtn.onclick = () => sendSmsNotification(c.id);
    tdNotify.appendChild(smsBtn);

    tbody.appendChild(tr);
  });
}

// Показать форму создания/редактирования
function showCertForm(cert = null) {
  document.getElementById('cert-form').style.display = 'block';
  document.getElementById('new-cert-btn').style.display = 'none';
  if (cert) {
    editingCertId = cert.id;
    document.getElementById('cert-form-title').innerText = 'Редактировать сертификат';
    document.getElementById('cert-name').value = cert.name;
    document.getElementById('cert-date-start').value = c.date_start;
    document.getElementById('cert-date-end').value = c.date_end;
    document.getElementById('cert-submit').innerText = 'Сохранить';
  } else {
    editingCertId = null;
    document.getElementById('cert-form-title').innerText = 'Новый сертификат';
    document.getElementById('cert-name').value = '';
    document.getElementById('cert-date-start').value = '';
    document.getElementById('cert-date-end').value = '';
    document.getElementById('cert-submit').innerText = 'Создать';
  }
}

// Скрыть форму и вернуть кнопку «Добавить»
function cancelEdit() {
  document.getElementById('cert-form').style.display = 'none';
  document.getElementById('new-cert-btn').style.display = 'block';
  editingCertId = null;
}

// Создать или обновить сертификат
async function submitCert() {
  const name = document.getElementById('cert-name').value.trim();
  const date_start = document.getElementById('cert-date-start').value;
  const date_end = document.getElementById('cert-date-end').value;

  if (!name || !date_start || !date_end) {
    alert('Заполните все поля.');
    return;
  }

  let url = API_CERT;
  let method = 'POST';
  if (editingCertId) {
    url += editingCertId;
    method = 'PUT';
  }

  try {
    const resp = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        name,
        date_start,
        date_end,
        owner_id: selectedUserId // привязываем к выбранному пользователю
      })
    });
    const data = await resp.json();
    if (!resp.ok) {
      alert(data.msg || 'Ошибка при сохранении сертификата');
    } else {
      alert('Сертификат сохранён');
    }
    cancelEdit();
    fetchCertificates();
  } catch (err) {
    alert('Ошибка при обращении к серверу.');
    console.error(err);
  }
}

// Редактировать сертификат (заполняем форму)
function editCert(cert) {
  showCertForm(cert);
}

// Удалить сертификат
async function deleteCert(id) {
  if (!confirm('Удалить сертификат?')) return;
  try {
    const resp = await fetch(`${API_CERT}${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });
    const data = await resp.json();
    if (!resp.ok) {
      alert(data.msg || 'Ошибка при удалении');
    } else {
      alert('Сертификат удалён');
    }
    fetchCertificates();
  } catch (err) {
    alert('Ошибка при обращении к серверу.');
    console.error(err);
  }
}

// Отправить уведомление на почту по конкретному сертификату
async function sendNotification(certId) {
  if (!confirm('Отправить уведомление на почту об этом сертификате?')) return;

  accessToken = localStorage.getItem('accessToken');
  if (!accessToken) {
    alert('Ошибка: отсутствует токен в localStorage');
    return;
  }

  try {
    const resp = await fetch(`${API_NOTIFY_EMAIL}${certId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    const data = await resp.json();
    if (!resp.ok) {
      alert(data.msg || 'Ошибка при отправке уведомления');
    } else {
      alert(data.msg);
    }
  } catch (err) {
    alert('Ошибка при обращении к серверу уведомлений.');
    console.error(err);
  }
}

// Отправить SMS-уведомление по конкретному сертификату
async function sendSmsNotification(certId) {
  if (!confirm('Отправить SMS-уведомление об этом сертификате?')) return;

  const token = localStorage.getItem('accessToken');  // JWT менеджера
  if (!token) {
    alert('Ошибка: отсутствует токен в localStorage');
    return;
  }

  try {
    const resp = await fetch(`${API_NOTIFY_SMS}${certId}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await resp.json();
    if (!resp.ok) {
      alert(data.msg || 'Ошибка при отправке SMS');
    } else {
      alert(data.msg);
    }
  } catch (err) {
    alert('Ошибка при запросе к серверу уведомлений.');
    console.error(err);
  }
}

// ======= Обработчики «Экспорт» и «Импорт» =======
window.addEventListener('DOMContentLoaded', () => {
  // Экспорт
  const exportBtn = document.getElementById('export-btn');
  if (exportBtn) {
    exportBtn.addEventListener('click', async () => {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        alert("Требуется авторизация");
        return;
      }

      const response = await fetch('http://localhost:5003/certificates/export', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        alert("Ошибка при экспорте");
        return;
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = "certificates_export.xlsx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    });
  }

  // Импорт
  const importForm = document.getElementById('import-form');
  if (importForm) {
    importForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fileInput = document.getElementById('import-file-input');
      if (!fileInput || fileInput.files.length === 0) {
        alert("Выберете файл .xlsx");
        return;
      }

      const token = localStorage.getItem('accessToken');
      if (!token) {
        alert("Требуется авторизация");
        return;
      }

      // Вытаскиваем user_id из URL (параметр ?user_id=)
      const params = new URLSearchParams(window.location.search);
      const userId = params.has('user_id')
        ? parseInt(params.get('user_id'))
        : null;

      if (!userId) {
        alert("Не указан пользователь для импорта");
        return;
      }

      const fd = new FormData();
      fd.append('file', fileInput.files[0]);
      fd.append('user_id', userId); // передаём в форму ID владельца

      const response = await fetch('http://localhost:5003/certificates/import', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: fd
      });

      const data = await response.json();
      if (!response.ok) {
        alert("Ошибка при импорте: " + (data.error || JSON.stringify(data)));
        return;
      }

      let msg = "Импорт завершён.\n\nСозданы сертификаты:\n";
      data.created.forEach(item => {
        msg += `— Строка ${item.row}: ${item.name}\n`;
      });
      if (data.errors.length > 0) {
        msg += "\nОшибки:\n" + data.errors.join("\n");
      }
      alert(msg);

      // Обновляем список сертификатов
      fetchCertificates();
    });
  }
});
