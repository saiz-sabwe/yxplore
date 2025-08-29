// Module de notification pour SweetAlert2
// file static/YXPLORE_NODE/js/module_notification.js


// Configuration par défaut des Toasts
const defaultToastOptions = {
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
};

// Fonction générique pour les toasts
function showToast(icon, title, options = {}) {
    const config = {
        ...defaultToastOptions,
        icon: icon,
        title: title,
        ...options
    };

    Swal.fire(config);
}

// Fonction générique pour les popups (non toast)
function showPopup(icon, title, text = '', options = {}) {
    const config = {
        icon: icon,
        title: title,
        text: text,
        confirmButtonText: 'Fermer',
        ...options
    };

    Swal.fire(config);
}

// Interface simple et paramétrable
function showSuccessFeedback(message = 'Réponse enregistrée', options = {}) {
    showToast('success', message, options);
}

function showErrorFeedback(message = 'Erreur lors de l\'envoi', options = {}) {
    showToast('error', message, options);
}

function showAlertFeedback(message = 'Information', options = {}) {
    showToast('info', message, options);
}

function showCustomAlert(icon = 'info', title = 'Information', text = '', options = {}) {
    showPopup(icon, title, text, options);
}

// Fonction showNotification pour la compatibilité avec passenger-management.js
function showNotification(title, message, icon = 'info', options = {}) {
    const config = {
        icon: icon,
        title: title,
        text: message,
        confirmButtonText: 'OK',
        timer: icon === 'success' ? 3000 : undefined,
        timerProgressBar: icon === 'success',
        ...options
    };

    Swal.fire(config);
}
