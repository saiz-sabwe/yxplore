/**
 * ModuleProfils KYC JavaScript
 * Gestion des formulaires KYC pour clients et marchands
 */

class KYCHandler {
    constructor() {
        this.initializeDropzones();
        this.initializeForms();
        this.initializeDatePickers();
        this.setupSubmitButtons();
    }

    /**
     * Initialise les dropzones pour l'upload de documents
     */
    initializeDropzones() {
        // Vérifier si Dropzone est disponible
        if (typeof Dropzone === 'undefined') {
            console.warn('Dropzone non disponible - upload de fichiers désactivé');
            return;
        }

        // Configuration commune pour toutes les dropzones
        const dropzoneConfig = {
            url: '#',
            autoProcessQueue: false,
            maxFiles: 1,
            acceptedFiles: '.pdf,.jpg,.jpeg,.png',
            addRemoveLinks: true,
            dictDefaultMessage: 'Glissez votre document ici ou cliquez pour sélectionner',
            dictFileTooBig: 'Fichier trop volumineux ({{filesize}}MB). Taille max: {{maxFilesize}}MB.',
            dictInvalidFileType: 'Type de fichier non autorisé.',
            dictResponseError: 'Erreur lors de l\'upload.',
            dictCancelUpload: 'Annuler',
            dictCancelUploadConfirmation: 'Êtes-vous sûr de vouloir annuler cet upload?',
            dictRemoveFile: 'Supprimer',
            dictMaxFilesExceeded: 'Vous ne pouvez pas uploader plus de fichiers.',
            maxFilesize: 10, // 10MB max
            thumbnailWidth: 120,
            thumbnailHeight: 120
        };

        // Initialiser les dropzones existantes
        this.initializeSpecificDropzones(dropzoneConfig);
    }

    /**
     * Initialise les dropzones spécifiques selon le type de profil
     */
    initializeSpecificDropzones(config) {
        // Dropzone pour document d'identité (client)
        const idDocumentDropzone = document.getElementById('idDocumentDropzone');
        if (idDocumentDropzone) {
            this.createDropzone(idDocumentDropzone, config, 'document');
        }

        // Dropzone pour licence commerciale (merchant)
        const businessLicenseDropzone = document.getElementById('businessLicenseDropzone');
        if (businessLicenseDropzone) {
            this.createDropzone(businessLicenseDropzone, config, 'business_license');
        }

        // Dropzone pour document d'enregistrement (merchant)
        const registrationDocDropzone = document.getElementById('registrationDocDropzone');
        if (registrationDocDropzone) {
            this.createDropzone(registrationDocDropzone, config, 'company_registration_doc');
        }

        // Dropzone pour certificat fiscal (merchant)
        const taxCertDropzone = document.getElementById('taxCertDropzone');
        if (taxCertDropzone) {
            this.createDropzone(taxCertDropzone, config, 'tax_certificate');
        }
    }

    /**
     * Crée une dropzone avec gestion des fichiers
     */
    createDropzone(element, config, fieldName) {
        const dropzone = new Dropzone(element, {
            ...config,
            init: function() {
                this.on('addedfile', function(file) {
                    KYCHandler.createHiddenFileInput(fieldName, file);
                });
                
                this.on('removedfile', function(file) {
                    KYCHandler.removeHiddenFileInput(fieldName);
                });

                this.on('error', function(file, errorMessage) {
                    if (typeof showErrorFeedback === 'function') {
                        showErrorFeedback(`Erreur avec ${file.name}: ${errorMessage}`);
                    } else {
                        console.error(`Erreur avec ${file.name}: ${errorMessage}`);
                    }
                });

                this.on('success', function(file) {
                    console.log(`Fichier ${file.name} ajouté avec succès`);
                });
            }
        });

        // Stocker la référence
        element.dropzone = dropzone;
    }

    /**
     * Initialise les formulaires KYC
     */
    initializeForms() {
        // Les formulaires sont maintenant gérés par setupSubmitButtons() avec jQuery
        // Ancienne méthode désactivée pour éviter les conflits
    }

    /**
     * Configure la soumission des formulaires (ancienne méthode - désactivée)
     */
    setupFormSubmission(form, profileType) {
        // Ancienne méthode désactivée - maintenant géré par setupSubmitButtons()
        console.log('setupFormSubmission() désactivée - utilise setupSubmitButtons() à la place');
    }

    /**
     * Configure les boutons de soumission avec jQuery (style login)
     */
    setupSubmitButtons() {
        // Vérifier si jQuery est disponible
        if (typeof $ === 'undefined') {
            console.error('jQuery non disponible - boutons KYC non initialisés');
            return;
        }

        console.log('Formulaires KYC initialisés via jQuery dans setupSubmitButtons()');

        // Bouton KYC Client
        $('#submitKYCClientBtn').on('click', (e) => {
            e.preventDefault();
            this.submitKYCForm('client');
        });

        // Bouton KYC Merchant  
        $('#submitKYCMerchantBtn').on('click', (e) => {
            e.preventDefault();
            this.submitKYCForm('merchant');
        });

        // Gestion de la touche Entrée dans les formulaires
        $('#kycClientForm, #kycMerchantForm').on('keypress', (e) => {
            if (e.which === 13) { // Touche Entrée
                e.preventDefault();
                const formId = $(e.target).closest('form').attr('id');
                const profileType = formId.includes('Client') ? 'client' : 'merchant';
                this.submitKYCForm(profileType);
            }
        });
    }

    /**
     * Soumission KYC avec style login (jQuery + SweetAlert2)
     */
    submitKYCForm(profileType) {
        const formId = profileType === 'client' ? '#kycClientForm' : '#kycMerchantForm';
        const btnId = profileType === 'client' ? '#submitKYCClientBtn' : '#submitKYCMerchantBtn';
        const form = $(formId);
        const $btn = $(btnId);

        // Validation des champs obligatoires
        if (!this.validateFormFields(form)) {
            showErrorFeedback('Veuillez remplir tous les champs obligatoires.');
            return;
        }

        // Préparer les données
        const formData = new FormData();
        
        // Ajouter tous les champs du formulaire
        form.find('input, select, textarea').each(function() {
            const $field = $(this);
            const name = $field.attr('name');
            const value = $field.val();
            
            if (name && value) {
                if ($field.attr('type') === 'file' && $field[0].files.length > 0) {
                    formData.append(name, $field[0].files[0]);
                } else if ($field.attr('type') !== 'file') {
                    formData.append(name, value);
                }
            }
        });

        // Ajouter l'opération
        formData.append('op', 'submit_kyc');
        formData.append('profile_type', profileType);

        // Animation du bouton (style login)
        const originalText = $btn.text();
        $btn.prop('disabled', true).html('<i class="bi bi-hourglass-split me-2"></i>Validation en cours...');

        // Requête AJAX
        $.ajax({
            type: 'POST',
            url: window.location.href,
            dataType: 'json',
            headers: {
                "X-CSRFToken": $('[name=csrfmiddlewaretoken]').val(),
                "X-Requested-With": "XMLHttpRequest"
            },
            data: formData,
            contentType: false,
            processData: false,

            success: (data) => {
                console.log("SUCCESS Response:", data);
                
                if (data && data.resultat === "SUCCESS") {
                    showSuccessFeedback(data.message || 'Validation KYC soumise avec succès !');
                    
                    // Recharger la page après succès
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    console.warn("Response data:", data);
                    showErrorFeedback(data?.message || 'Erreur lors de la validation KYC.');
                    $btn.prop('disabled', false).text(originalText);
                }
            },

            error: (xhr) => {
                console.error("Erreur AJAX:", xhr);
                console.error("Status:", xhr.status);
                console.error("Response Text:", xhr.responseText);
                console.error("Response JSON:", xhr.responseJSON);
                
                let msg = 'Une erreur est survenue lors de la validation KYC.';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    msg = xhr.responseJSON.message;
                } else if (xhr.responseText) {
                    // Si c'est du HTML au lieu de JSON, essayer de parser une erreur
                    if (xhr.responseText.includes('Profil KYC mis à jour avec succès')) {
                        showSuccessFeedback('Profil KYC mis à jour avec succès !');
                        setTimeout(() => {
                            window.location.reload();
                        }, 1500);
                        return;
                    }
                    msg = 'Erreur serveur: ' + xhr.status;
                }
                
                showErrorFeedback(msg);
                $btn.prop('disabled', false).text(originalText);
            }
        });
    }

    /**
     * Ancienne méthode supprimée - remplacée par submitKYCForm()
     */

    /**
     * Valide les champs du formulaire avec jQuery (style login)
     */
    validateFormFields(form) {
        let isValid = true;
        
        // Vérifier tous les champs requis
        form.find('[required]').each(function() {
            const $field = $(this);
            const value = $field.val();
            
            if (!value || value.trim() === '') {
                $field.addClass('is-invalid');
                isValid = false;
            } else {
                $field.removeClass('is-invalid');
            }
        });

        // Validation spéciale pour les emails
        form.find('input[type="email"]').each(function() {
            const $field = $(this);
            const value = $field.val();
            
            if (value && !KYCHandler.isValidEmail(value)) {
                $field.addClass('is-invalid');
                isValid = false;
            }
        });
        
        return isValid;
    }

    /**
     * Valide le formulaire (ancienne méthode - gardée pour compatibilité)
     */
    validateForm(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        return isValid;
    }

    /**
     * Ancienne méthode supprimée - remplacée par $.ajax dans submitKYCForm()
     */

    /**
     * Initialise les sélecteurs de date
     */
    initializeDatePickers() {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            if (window.flatpickr) {
                flatpickr(input, {
                    dateFormat: 'Y-m-d',
                    maxDate: new Date(),
                    locale: 'fr',
                    allowInput: true
                });
            }
        });
    }

    /**
     * Crée un input caché pour un fichier
     */
    static createHiddenFileInput(name, file) {
        const input = document.createElement('input');
        input.type = 'file';
        input.name = name;
        input.style.display = 'none';
        
        const dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;
        
        // Supprimer l'ancien input s'il existe
        const oldInput = document.querySelector(`input[name="${name}"]`);
        if (oldInput) oldInput.remove();
        
        // Ajouter le nouveau
        const form = document.querySelector('form[id*="kyc"]');
        if (form) {
            form.appendChild(input);
        }
    }

    /**
     * Supprime un input caché de fichier
     */
    static removeHiddenFileInput(name) {
        const input = document.querySelector(`input[name="${name}"]`);
        if (input) input.remove();
    }

    /**
     * Validation d'email
     */
    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Affiche un message de succès (utilise les fonctions globales SweetAlert2)
     */
    static showSuccessMessage(message) {
        if (typeof showSuccessFeedback === 'function') {
            showSuccessFeedback(message);
        } else {
            console.log('SUCCESS:', message);
        }
    }

    /**
     * Affiche un message d'erreur (utilise les fonctions globales SweetAlert2)
     */
    static showErrorMessage(message) {
        if (typeof showErrorFeedback === 'function') {
            showErrorFeedback(message);
        } else {
            console.error('ERROR:', message);
        }
    }

    /**
     * Affiche un message d'avertissement
     */
    static showWarningMessage(message) {
        if (typeof showAlertFeedback === 'function') {
            showAlertFeedback(message);
        } else {
            console.warn('WARNING:', message);
        }
    }

    /**
     * Affiche un message d'information
     */
    static showInfoMessage(message) {
        if (typeof showAlertFeedback === 'function') {
            showAlertFeedback(message);
        } else {
            console.info('INFO:', message);
        }
    }

    /**
     * Met à jour la barre de progression KYC
     */
    static updateKYCProgress(percentage) {
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
            
            const percentageText = progressBar.parentElement.nextElementSibling;
            if (percentageText) {
                percentageText.textContent = `${percentage}% complété`;
            }
        }
    }

    /**
     * Rafraîchit les données du profil
     */
    static async refreshProfileData() {
        try {
            const response = await fetch('', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: 'op=profile_data'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.resultat === 'SUCCESS') {
                    this.updateKYCProgress(data.profile.kyc_completion_percentage);
                    this.updateKYCStatus(data.profile.kyc_status);
                }
            }
        } catch (error) {
            console.error('Erreur lors du rafraîchissement:', error);
        }
    }

    /**
     * Met à jour le statut KYC affiché
     */
    static updateKYCStatus(status) {
        const statusBadge = document.querySelector('.badge.bg-light');
        if (statusBadge) {
            const statusTexts = {
                0: 'En attente',
                1: 'KYC1 Approuvé',
                2: 'KYC2 Approuvé',
                3: 'Rejeté'
            };
            statusBadge.textContent = statusTexts[status] || 'Inconnu';
        }
    }
}

// Initialisation automatique quand le DOM est prêt
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si nous sommes sur une page KYC
    const kycForm = document.querySelector('form[id*="kyc"]');
    if (kycForm) {
        try {
            window.kycHandler = new KYCHandler();
            console.log('ModuleProfils KYC initialisé');
        } catch (error) {
            console.error('Erreur lors de l\'initialisation KYC:', error);
        }
    } else {
        console.log('Pas de formulaire KYC trouvé sur cette page');
    }
});

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KYCHandler;
}
