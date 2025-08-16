// static/YXPLORE_NODE/js/register.js

function submitRegister() {
    const formData = new FormData();
    
    // Récupération des données du formulaire
    const accountType = $('#account_type').val();
    const email = $('#email').val().trim();
    const password = $('#password').val();
    const passwordConfirm = $('#password_confirm').val();
    const terms = $('#terms').is(':checked');

    // Validation côté client
    if (!accountType) {
        showErrorFeedback('Veuillez sélectionner un type de compte.');
        return;
    }

    if (!email || !validateEmail(email)) {
        showErrorFeedback('Veuillez renseigner une adresse email valide.');
        return;
    }

    if (!password || password.length < 6) {
        showErrorFeedback('Le mot de passe doit contenir au moins 6 caractères.');
        return;
    }

    if (password !== passwordConfirm) {
        showErrorFeedback('Les mots de passe ne correspondent pas.');
        return;
    }

    if (!terms) {
        showErrorFeedback('Vous devez accepter les conditions générales.');
        return;
    }

    // Ajout des données
    formData.append("account_type", accountType);
    formData.append("email", email);
    formData.append("password", password);
    formData.append('op', 'inscription');

    const $btn = $('#register-btn');
    $btn.prop('disabled', true).text('Création en cours…');

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
                const $btn = $('#register-btn');
                $btn.prop('disabled', false).text('Créer mon compte');
            }
        },

        error: function (xhr) {
            console.error("Erreur AJAX:", xhr.responseText);
            let msg = 'Une erreur est survenue lors de l\'inscription.';
            
            if (xhr.responseJSON && xhr.responseJSON.message) {
                msg = xhr.responseJSON.message;
            }
            
            showErrorFeedback(msg);
            const $btn = $('#register-btn');
            $btn.prop('disabled', false).text('Créer mon compte');
        },
    });
}

function registerButton() {
    $('#register-btn').on('click', function (e) {
        e.preventDefault();
        submitRegister();
    });
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function setupPasswordValidation() {
    $('#password, #password_confirm').on('keyup', function() {
        const password = $('#password').val();
        const confirm = $('#password_confirm').val();
        
        if (confirm && password !== confirm) {
            $('#password_confirm').addClass('is-invalid');
        } else {
            $('#password_confirm').removeClass('is-invalid');
        }
    });
}

function setupEmailValidation() {
    $('#email').on('blur', function() {
        const email = $(this).val();
        if (email && !validateEmail(email)) {
            $(this).addClass('is-invalid');
        } else {
            $(this).removeClass('is-invalid');
        }
    });
}

$(document).ready(function () {
    registerButton();
    setupPasswordValidation();
    setupEmailValidation();
});
