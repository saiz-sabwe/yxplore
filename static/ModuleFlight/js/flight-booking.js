/**
 * ModuleFlight - Réservation de vols avec jQuery et AJAX
 * Utilise le système d'opérations (op) et le module de notifications global
 */

$(document).ready(function() {
    console.log('Flight Booking JS loaded');
    
    // Gestionnaire principal des réservations
    const FlightBooking = {
        init: function() {
            this.bindEvents();
        },

        bindEvents: function() {
            // Réservation d'un vol
            $(document).on('click', '.book-flight-btn', this.handleBookingClick.bind(this));
            
            // Paiement d'une réservation
            $(document).on('click', '.pay-booking-btn', this.handlePaymentClick.bind(this));
            
            // Annulation d'une réservation
            $(document).on('click', '.cancel-booking-btn', this.handleCancelClick.bind(this));
            
            // Voir les détails d'une réservation
            $(document).on('click', '.view-booking-details', this.handleViewDetails.bind(this));
        },

        handleBookingClick: function(e) {
            e.preventDefault();
            
            const $btn = $(e.currentTarget);
            const offerId = $btn.data('offer-id');
            const price = $btn.data('price');
            const currency = $btn.data('currency');
            
            // Vérifier si l'utilisateur est connecté
            if (!this.isUserAuthenticated()) {
                this.showLoginRequired();
                return;
            }
            
            // Démarrer le processus de réservation
            this.startBookingProcess(offerId, price, currency);
        },

        isUserAuthenticated: function() {
            // Vérifier via data attribute, classe ou variable globale
            return $('body').hasClass('authenticated') || 
                   window.userAuthenticated === true ||
                   $('#user-status').data('authenticated') === true;
        },

        showLoginRequired: function() {
            showAlertFeedback('Vous devez être connecté pour effectuer une réservation', {
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Se connecter',
                cancelButtonText: 'Annuler'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = $('#login-url').data('url') || '/profils/login/';
                }
            });
        },

        startBookingProcess: function(offerId, price, currency) {
            // Étape 1: Charger les agences disponibles
            this.loadAgenciesAndShowForm(offerId, price, currency);
        },

        loadAgenciesAndShowForm: function(offerId, price, currency) {
            const formData = new FormData();
            formData.append('op', 'get_agencies');
            
            $.ajax({
                type: 'POST',
                url: $('#booking-url').data('url') || '/flights/book/',
                dataType: 'json',
                headers: {
                    "X-CSRFToken": $('#csrf').data('csrf') || $('[name=csrfmiddlewaretoken]').val()
                },
                data: formData,
                contentType: false,
                processData: false,
                
                success: (data) => {
                    if (data.resultat === "SUCCESS") {
                        this.showBookingForm(offerId, price, currency, data.agencies);
                    } else {
                        showErrorFeedback(data.message || 'Erreur lors du chargement des agences');
                    }
                },
                
                error: (xhr) => {
                    console.error("Erreur AJAX:", xhr.responseText);
                    showErrorFeedback('Erreur lors du chargement des agences');
                }
            });
        },

        showBookingForm: function(offerId, price, currency, agencies) {
            // Construire les options d'agences
            let agencyOptions = '<option value="">Sélectionner une agence...</option>';
            agencies.forEach(agency => {
                agencyOptions += `<option value="${agency.uuid || agency.id}">
                    ${agency.name} - ${agency.city}
                </option>`;
            });

            // Utiliser un template existant ou HTML minimal
            const formHtml = `
                <div class="booking-form">
                    <div class="mb-3">
                        <label for="agency-select" class="form-label">Choisir une agence</label>
                        <select id="agency-select" class="form-select" required>
                            ${agencyOptions}
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="passenger-count" class="form-label">Nombre de passagers</label>
                        <input type="number" id="passenger-count" class="form-control" 
                               min="1" max="9" value="1" required>
                    </div>
                    <div class="alert alert-info">
                        <strong>Prix total :</strong> ${price} ${currency}
                    </div>
                </div>
            `;

            showPopup('question', 'Réserver ce vol', '', {
                html: formHtml,
                showCancelButton: true,
                confirmButtonText: 'Continuer',
                cancelButtonText: 'Annuler',
                preConfirm: () => {
                    const agencyId = $('#agency-select').val();
                    const passengerCount = $('#passenger-count').val();
                    
                    if (!agencyId) {
                        showErrorFeedback('Veuillez sélectionner une agence');
                        return false;
                    }
                    
                    if (!passengerCount || passengerCount < 1 || passengerCount > 9) {
                        showErrorFeedback('Nombre de passagers invalide');
                        return false;
                    }
                    
                    return {
                        agencyId: agencyId,
                        passengerCount: parseInt(passengerCount)
                    };
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    this.showPassengerForm(offerId, result.value.agencyId, 
                                         result.value.passengerCount, price, currency);
                }
            });
        },

        showPassengerForm: function(offerId, agencyId, passengerCount, price, currency) {
            // Générer les champs pour chaque passager
            let passengerFields = '';
            
            for (let i = 1; i <= passengerCount; i++) {
                passengerFields += `
                    <div class="passenger-form mb-4" data-passenger="${i}">
                        <h6>Passager ${i}</h6>
                        <div class="row">
                            <div class="col-md-2">
                                <label class="form-label">Titre</label>
                                <select class="form-select passenger-title" required>
                                    <option value="">--</option>
                                    <option value="Mr">M.</option>
                                    <option value="Mrs">Mme</option>
                                    <option value="Ms">Mlle</option>
                                </select>
                            </div>
                            <div class="col-md-5">
                                <label class="form-label">Prénom</label>
                                <input type="text" class="form-control passenger-firstname" required>
                            </div>
                            <div class="col-md-5">
                                <label class="form-label">Nom</label>
                                <input type="text" class="form-control passenger-lastname" required>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-md-6">
                                <label class="form-label">Date de naissance</label>
                                <input type="date" class="form-control passenger-birthdate" required>
                                                    </div>
                        <div class="col-md-6">
                            <label class="form-label">Genre</label>
                            <select class="form-select passenger-gender" required>
                                <option value="">--</option>
                                <option value="m">Masculin</option>
                                <option value="f">Féminin</option>
                            </select>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-6">
                            <label class="form-label">Email</label>
                            <input type="email" class="form-control passenger-email" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Téléphone</label>
                            <input type="tel" class="form-control passenger-phone" placeholder="+33123456789" required>
                        </div>
                    </div>
                </div>
                `;
            }

            const passengerFormHtml = `
                <div class="passenger-forms">
                    ${passengerFields}
                    <div class="alert alert-warning">
                        <small>Veuillez saisir les noms exactement comme sur vos passeports</small>
                    </div>
                </div>
            `;

            showPopup('info', 'Informations des passagers', '', {
                html: passengerFormHtml,
                showCancelButton: true,
                confirmButtonText: 'Réserver',
                cancelButtonText: 'Retour',
                width: '80%',
                preConfirm: () => {
                    const passengers = [];
                    let isValid = true;
                    
                    $('.passenger-form').each(function() {
                        const passengerNum = $(this).data('passenger');
                        const title = $(this).find('.passenger-title').val();
                        const firstName = $(this).find('.passenger-firstname').val().trim();
                                            const lastName = $(this).find('.passenger-lastname').val().trim();
                    const birthDate = $(this).find('.passenger-birthdate').val();
                    const gender = $(this).find('.passenger-gender').val();
                    const email = $(this).find('.passenger-email').val().trim();
                    const phone = $(this).find('.passenger-phone').val().trim();
                    
                    if (!title || !firstName || !lastName || !birthDate || !gender || !email || !phone) {
                        showErrorFeedback(`Veuillez remplir tous les champs pour le passager ${passengerNum}`);
                        isValid = false;
                        return false;
                    }
                    
                    passengers.push({
                        title: title,
                        given_name: firstName,
                        family_name: lastName,
                        born_on: birthDate,
                        gender: gender,
                        email: email,
                        phone_number: phone
                    });
                    });
                    
                    return isValid ? passengers : false;
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    this.processBooking(offerId, agencyId, result.value, price, currency);
                }
            });
        },

        processBooking: function(offerId, agencyId, passengerData, price, currency) {
            const formData = new FormData();
            formData.append('op', 'create_booking');
            formData.append('offer_id', offerId);
            formData.append('agency_id', agencyId);
            formData.append('passenger_data', JSON.stringify(passengerData));
            
            // Affichage du loader
            showPopup('info', 'Création de la réservation...', 'Veuillez patienter', {
                allowOutsideClick: false,
                showConfirmButton: false,
                willOpen: () => {
                    Swal.showLoading();
                }
            });
            
            $.ajax({
                type: 'POST',
                url: $('#booking-url').data('url') || '/flights/book/',
                dataType: 'json',
                headers: {
                    "X-CSRFToken": $('#csrf').data('csrf') || $('[name=csrfmiddlewaretoken]').val()
                },
                data: formData,
                contentType: false,
                processData: false,
                
                success: (data) => {
                    if (data.resultat === "SUCCESS") {
                        this.showBookingSuccess(data.data, currency);
                    } else {
                        showErrorFeedback(data.message || 'Erreur lors de la réservation');
                    }
                },
                
                error: (xhr) => {
                    console.error("Erreur AJAX:", xhr.responseText);
                    let errorMessage = 'Erreur interne du serveur';
                    
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMessage = xhr.responseJSON.message;
                    }
                    
                    showErrorFeedback(errorMessage);
                }
            });
        },

        showBookingSuccess: function(bookingData, currency) {
            const successHtml = `
                <p>Votre réservation a été créée avec succès.</p>
                <p><strong>Référence :</strong> ${bookingData.booking_reference}</p>
                <p><strong>Statut :</strong> ${bookingData.status}</p>
                <p><strong>Prix :</strong> ${bookingData.price} ${currency}</p>
            `;

            showPopup('success', 'Réservation créée !', '', {
                html: successHtml,
                showCancelButton: true,
                confirmButtonText: 'Procéder au paiement',
                cancelButtonText: 'Plus tard'
            }).then((result) => {
                if (result.isConfirmed) {
                    this.processPayment(bookingData.booking_id, bookingData.price, currency);
                } else {
                    // Rediriger vers la page des réservations
                    const bookingsUrl = $('#bookings-url').data('url') || '/flights/api/bookings/my_bookings/';
                    window.location.href = bookingsUrl;
                }
            });
        },

        handlePaymentClick: function(e) {
            e.preventDefault();
            
            const $btn = $(e.currentTarget);
            const bookingId = $btn.data('booking-id');
            const amount = $btn.data('amount');
            const currency = $btn.data('currency');
            
            this.processPayment(bookingId, amount, currency);
        },

        processPayment: function(bookingId, amount, currency) {
            const paymentHtml = `
                <div class="payment-summary">
                    <p><strong>Montant à payer :</strong> ${amount} ${currency}</p>
                    <p class="text-muted">Il s'agit d'un paiement fictif à des fins de démonstration.</p>
                </div>
            `;

            showPopup('question', 'Confirmer le paiement', '', {
                html: paymentHtml,
                showCancelButton: true,
                confirmButtonText: 'Payer maintenant',
                cancelButtonText: 'Annuler'
            }).then((result) => {
                if (result.isConfirmed) {
                    this.submitPayment(bookingId, amount, currency);
                }
            });
        },

        submitPayment: function(bookingId, amount, currency) {
            const formData = new FormData();
            formData.append('op', 'pay_booking');
            formData.append('booking_id', bookingId);
            
            // Affichage du loader
            showPopup('info', 'Traitement du paiement...', 'Veuillez patienter', {
                allowOutsideClick: false,
                showConfirmButton: false,
                willOpen: () => {
                    Swal.showLoading();
                }
            });
            
            $.ajax({
                type: 'POST',
                url: $('#payment-url').data('url') || `/flights/pay/${bookingId}/`,
                dataType: 'json',
                headers: {
                    "X-CSRFToken": $('#csrf').data('csrf') || $('[name=csrfmiddlewaretoken]').val()
                },
                data: formData,
                contentType: false,
                processData: false,
                
                success: (data) => {
                    if (data.resultat === "SUCCESS") {
                        const successHtml = `
                            <p>Votre paiement a été traité avec succès.</p>
                            <p><strong>Référence :</strong> ${data.data.booking_reference}</p>
                            <p><strong>Statut :</strong> ${data.data.status}</p>
                            <p><strong>Montant payé :</strong> ${data.data.total_paid} ${currency}</p>
                        `;

                        showPopup('success', 'Paiement réussi !', '', {
                            html: successHtml,
                            confirmButtonText: 'OK'
                        }).then(() => {
                            location.reload();
                        });
                    } else {
                        showErrorFeedback(data.message || 'Erreur lors du paiement');
                    }
                },
                
                error: (xhr) => {
                    console.error("Erreur AJAX:", xhr.responseText);
                    let errorMessage = 'Erreur interne du serveur';
                    
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMessage = xhr.responseJSON.message;
                    }
                    
                    showErrorFeedback(errorMessage);
                }
            });
        },

        handleCancelClick: function(e) {
            e.preventDefault();
            
            const $btn = $(e.currentTarget);
            const bookingId = $btn.data('booking-id');
            const bookingRef = $btn.data('booking-ref');
            
            const confirmHtml = `
                <p>Êtes-vous sûr de vouloir annuler la réservation <strong>${bookingRef}</strong> ?</p>
                <p class="text-warning">Cette action est irréversible.</p>
            `;

            showPopup('warning', 'Confirmer l\'annulation', '', {
                html: confirmHtml,
                showCancelButton: true,
                confirmButtonText: 'Oui, annuler',
                cancelButtonText: 'Non, garder',
                confirmButtonColor: '#d33'
            }).then((result) => {
                if (result.isConfirmed) {
                    this.submitCancellation(bookingId);
                }
            });
        },

        submitCancellation: function(bookingId) {
            const formData = new FormData();
            formData.append('op', 'cancel_booking');
            formData.append('booking_id', bookingId);
            
            $.ajax({
                type: 'POST',
                url: $('#cancel-url').data('url') || '/flights/cancel/',
                dataType: 'json',
                headers: {
                    "X-CSRFToken": $('#csrf').data('csrf') || $('[name=csrfmiddlewaretoken]').val()
                },
                data: formData,
                contentType: false,
                processData: false,
                
                success: (data) => {
                    if (data.resultat === "SUCCESS") {
                        showSuccessFeedback('Réservation annulée avec succès');
                        setTimeout(() => {
                            location.reload();
                        }, 1500);
                    } else {
                        showErrorFeedback(data.message || 'Erreur lors de l\'annulation');
                    }
                },
                
                error: (xhr) => {
                    console.error("Erreur AJAX:", xhr.responseText);
                    let errorMessage = 'Erreur interne du serveur';
                    
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMessage = xhr.responseJSON.message;
                    }
                    
                    showErrorFeedback(errorMessage);
                }
            });
        },

        handleViewDetails: function(e) {
            e.preventDefault();
            
            const $btn = $(e.currentTarget);
            const bookingId = $btn.data('booking-id');
            
            const formData = new FormData();
            formData.append('op', 'get_booking_details');
            formData.append('booking_id', bookingId);
            
            $.ajax({
                type: 'POST',
                url: $('#booking-details-url').data('url') || `/flights/api/bookings/${bookingId}/`,
                dataType: 'json',
                headers: {
                    "X-CSRFToken": $('#csrf').data('csrf') || $('[name=csrfmiddlewaretoken]').val()
                },
                data: formData,
                contentType: false,
                processData: false,
                
                success: (data) => {
                    if (data.resultat === "SUCCESS") {
                        this.showBookingDetails(data.booking);
                    } else {
                        showErrorFeedback(data.message || 'Erreur lors du chargement des détails');
                    }
                },
                
                error: (xhr) => {
                    console.error("Erreur AJAX:", xhr.responseText);
                    showErrorFeedback('Impossible de charger les détails de la réservation');
                }
            });
        },

        showBookingDetails: function(booking) {
            const passengerList = booking.passenger_data.map(p => 
                `<li>${p.title} ${p.given_name} ${p.family_name}</li>`
            ).join('');
            
            const detailsHtml = `
                <div class="booking-details text-start">
                    <p><strong>Statut :</strong> ${booking.status}</p>
                    <p><strong>Paiement :</strong> ${booking.payment_status}</p>
                    <p><strong>Vol :</strong> ${booking.origin} → ${booking.destination}</p>
                    <p><strong>Départ :</strong> ${new Date(booking.departure_date).toLocaleString('fr-FR')}</p>
                    <p><strong>Passagers :</strong></p>
                    <ul>${passengerList}</ul>
                    <p><strong>Prix :</strong> ${booking.price} ${booking.currency}</p>
                    <p><strong>Commission :</strong> ${booking.commission_amount} ${booking.currency}</p>
                    <p><strong>Total :</strong> ${booking.total_with_commission} ${booking.currency}</p>
                </div>
            `;

            showPopup('info', `Réservation ${booking.booking_reference}`, '', {
                html: detailsHtml,
                width: '60%',
                confirmButtonText: 'Fermer'
            });
        }
    };

    // Initialisation du module
    FlightBooking.init();

    // Exposition globale pour usage externe
    window.FlightBooking = FlightBooking;
});