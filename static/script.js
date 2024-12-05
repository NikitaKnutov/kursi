function toggleRegistrationForm() {
    const form = document.querySelector('.registration-form');
    const overlay = document.querySelector('.overlay');
    form.classList.toggle('active');
    overlay.classList.toggle('active');
}

async function registerUser() {
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (!name || !email || !password) {
        alert('Пожалуйста, заполните все поля!');
        return;
    }

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        });

        if (response.ok) {
            alert('Регистрация успешна!');
            toggleRegistrationForm();
        } else {
            alert('Ошибка регистрации!');
        }
    } catch (error) {
        console.error('Ошибка при отправке запроса:', error);
        alert('Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.');
    }
}