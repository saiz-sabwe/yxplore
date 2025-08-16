// static/PonaCash/js/login.js


function submitLogin() {
    const formData = new FormData();
    
    const username = $('#username').val().trim();
    const password = $('#password').val().trim();

    if (!username || !password) {
        showErrorFeedback('Veuillez renseigner votre nom d\'utilisateur et votre mot de passe.');
        return;
    }

    formData.append("username", username);
    formData.append("password", password);
    formData.append('op', 'connexion');

    const $btn = $('#login-btn');
    $btn.prop('disabled', true).text('Connexion…');

    $.ajax({
        type: 'POST',
        url: $('#way').data('url_auth'),
        dataType: 'json',
        headers: {"X-CSRFToken": $('#csrf').data().csrf},
        data: formData,
        contentType: false,
        processData: false,

        success: function (data) {
            if (data.resultat === "SUCCESS") {

                showSuccessFeedback(data.message);

                if (data.redirect_url) {
                    setTimeout(function () {
                        window.location.href = data.redirect_url;
                    }, 800);
                }
            } else {
                showErrorFeedback(data.message);
                const $btn = $('#login-btn');
                $btn.prop('disabled', false).text('Connexion');
            }
        },

        error: function (xhr) {
            console.error("Erreur AJAX:", xhr.responseText);
            let msg = 'Une erreur est survenue lors de la connexion.';
            
            if (xhr.responseJSON && xhr.responseJSON.message) {
                msg = xhr.responseJSON.message;
            }
            
            showErrorFeedback(msg);
            const $btn = $('#login-btn');
            $btn.prop('disabled', false).text('Connexion');
        },
    });
}

function loginButton() {
    $('#login-btn').on('click', function (e) {
        e.preventDefault();
        submitLogin();
    });
}

// Fonction supprimée car nous utilisons email/username

$(document).ready(function () {
    loginButton();
});
