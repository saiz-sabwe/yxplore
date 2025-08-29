/**
 * ModuleFlight - Recherche de vols avec jQuery et AJAX
 * Utilise le système d'opérations (op) et le module de notifications global
 */

$(document).ready(function() {
    console.log('Flight Search JS loaded');
    
    // Initialisation
    const FlightSearch = {
        init: function() {
            this.bindEvents();
            this.setupDatePickers();
            this.setupAirportValidation();
        },

        bindEvents: function() {
            // Soumission du formulaire de recherche
            $('#flight-search-form').on('submit', this.handleSearchSubmit.bind(this));
            
            // Échange origine/destination
            $('#swap-airports').on('click', this.swapAirports.bind(this));
            
            // Gestion du type de vol
            $('input[name="trip_type"]').on('change', this.handleTripTypeChange.bind(this));
            
            // Validation des aéroports
            $('#origin, #destination').on('blur', this.validateAirportCode.bind(this));
            
            // Validation du nombre de passagers
            $('#passengers').on('change', this.validatePassengers.bind(this));
        },

        handleSearchSubmit: function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const $form = $(e.target);
            
            // Collecte des données du formulaire
            const searchData = {
                origin: $('#origin').val().trim().toUpperCase(),
                destination: $('#destination').val().trim().toUpperCase(),
                departure_date: $('#departure_date').val(),
                return_date: $('#return_date').val(),
                passengers: $('#passengers').val(),
                cabin_class: $('#cabin_class').val()
            };
            
            // Validation côté client
            if (!this.validateSearchForm(searchData)) {
                return;
            }
            
            // Préparation des données AJAX avec opération
            Object.keys(searchData).forEach(key => {
                if (searchData[key]) {
                    formData.append(key, searchData[key]);
                }
            });
            formData.append('op', 'search_flights');
            
            // Désactivation du bouton et affichage du loader
            const $submitBtn = $form.find('button[type="submit"]');
            const originalText = $submitBtn.text();
            $submitBtn.prop('disabled', true).text('Recherche...');
            
            // Requête AJAX
            $.ajax({
                type: 'POST',
                url: $('#flight-search-url').data('url') || '/flights/search/',
                dataType: 'json',
                headers: {
                    "X-CSRFToken": $('#csrf').data('csrf') || $('[name=csrfmiddlewaretoken]').val()
                },
                data: formData,
                contentType: false,
                processData: false,
                
                success: function(data) {
                    if (data.resultat === "SUCCESS") {
                        showSuccessFeedback(data.message || 'Recherche effectuée');
                        
                        if (data.redirect_url) {
                            setTimeout(function() {
                                window.location.href = data.redirect_url;
                            }, 800);
                        } else {
                            // Construction URL de résultats si pas de redirection
                            const searchParams = new URLSearchParams(searchData);
                            window.location.href = '/flights/results/?' + searchParams.toString();
                        }
                    } else {
                        showErrorFeedback(data.message || 'Erreur lors de la recherche');
                        $submitBtn.prop('disabled', false).text(originalText);
                    }
                },
                
                error: function(xhr) {
                    console.error("Erreur AJAX:", xhr.responseText);
                    let errorMsg = 'Une erreur est survenue lors de la recherche.';
                    
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMsg = xhr.responseJSON.message;
                    }
                    
                    showErrorFeedback(errorMsg);
                    $submitBtn.prop('disabled', false).text(originalText);
                }
            });
        },

        validateSearchForm: function(data) {
            // Validation des champs obligatoires
            if (!data.origin || !data.destination || !data.departure_date) {
                showErrorFeedback('Veuillez remplir tous les champs obligatoires');
                return false;
            }
            
            // Validation que l'origine et la destination sont différentes
            if (data.origin === data.destination) {
                showErrorFeedback('L\'origine et la destination doivent être différentes');
                return false;
            }
            
            // Validation du format des codes d'aéroport
            if (!this.validateIATACode(data.origin) || !this.validateIATACode(data.destination)) {
                showErrorFeedback('Les codes d\'aéroport doivent contenir 3 lettres (ex: CDG)');
                return false;
            }
            
            // Validation de la date de départ
            const today = new Date();
            const departureDate = new Date(data.departure_date);
            
            if (departureDate <= today) {
                showErrorFeedback('La date de départ doit être dans le futur');
                return false;
            }
            
            // Validation de la date de retour si présente
            if (data.return_date) {
                const returnDate = new Date(data.return_date);
                if (returnDate <= departureDate) {
                    showErrorFeedback('La date de retour doit être après la date de départ');
                    return false;
                }
            }
            
            // Validation du nombre de passagers
            const passengers = parseInt(data.passengers);
            if (passengers < 1 || passengers > 9) {
                showErrorFeedback('Le nombre de passagers doit être entre 1 et 9');
                return false;
            }
            
            return true;
        },

        swapAirports: function(e) {
            e.preventDefault();
            
            const $origin = $('#origin');
            const $destination = $('#destination');
            const originValue = $origin.val();
            const destinationValue = $destination.val();
            
            $origin.val(destinationValue);
            $destination.val(originValue);
            
            // Animation du bouton
            const $btn = $(e.currentTarget);
            $btn.addClass('rotating');
            setTimeout(() => {
                $btn.removeClass('rotating');
            }, 500);
            
            // Validation après échange
            this.validateAirportCode.call($origin[0]);
            this.validateAirportCode.call($destination[0]);
        },

        handleTripTypeChange: function(e) {
            const isRoundTrip = $(e.target).val() === 'round_trip';
            const $returnDateField = $('#return_date_field');
            const $returnInput = $('#return_date');
            
            if (isRoundTrip) {
                $returnDateField.show();
                $returnInput.prop('required', true);
            } else {
                $returnDateField.hide();
                $returnInput.prop('required', false).val('');
            }
        },

        validateAirportCode: function(e) {
            const $input = $(e ? e.target : this);
            const value = $input.val().toUpperCase().trim();
            
            if (value.length === 0) {
                $input.removeClass('is-valid is-invalid');
                return;
            }
            
            if (this.validateIATACode ? this.validateIATACode(value) : /^[A-Z]{3}$/.test(value)) {
                $input.val(value).removeClass('is-invalid').addClass('is-valid');
            } else {
                $input.removeClass('is-valid').addClass('is-invalid');
            }
        },

        validatePassengers: function(e) {
            const $input = $(e.target);
            const passengers = parseInt($input.val());
            
            if (passengers >= 1 && passengers <= 9) {
                $input.removeClass('is-invalid').addClass('is-valid');
            } else {
                $input.removeClass('is-valid').addClass('is-invalid');
                if (passengers > 0) { // Seulement si une valeur a été saisie
                    showErrorFeedback('Le nombre de passagers doit être entre 1 et 9');
                }
            }
        },

        setupDatePickers: function() {
            const today = new Date().toISOString().split('T')[0];
            
            $('#departure_date').attr('min', today);
            
            $('#departure_date').on('change', function() {
                const departureDate = $(this).val();
                $('#return_date').attr('min', departureDate);
                
                // Reset return date if it's before new departure date
                const currentReturnDate = $('#return_date').val();
                if (currentReturnDate && currentReturnDate <= departureDate) {
                    $('#return_date').val('');
                }
            });
        },

        setupAirportValidation: function() {
            // Autocomplete basique pour les aéroports courants
            const commonAirports = [
                { code: 'CDG', name: 'Paris Charles de Gaulle', city: 'Paris' },
                { code: 'ORY', name: 'Paris Orly', city: 'Paris' },
                { code: 'LHR', name: 'London Heathrow', city: 'London' },
                { code: 'JFK', name: 'John F. Kennedy', city: 'New York' },
                { code: 'LAX', name: 'Los Angeles International', city: 'Los Angeles' },
                { code: 'DXB', name: 'Dubai International', city: 'Dubai' },
                { code: 'NRT', name: 'Narita International', city: 'Tokyo' },
                { code: 'SIN', name: 'Singapore Changi', city: 'Singapore' }
            ];

            // Si jQuery UI est disponible, setup autocomplete
            if ($.fn.autocomplete) {
                $('#origin, #destination').autocomplete({
                    source: function(request, response) {
                        const term = request.term.toLowerCase();
                        const matches = commonAirports.filter(airport => 
                            airport.code.toLowerCase().includes(term) ||
                            airport.name.toLowerCase().includes(term) ||
                            airport.city.toLowerCase().includes(term)
                        );
                        
                        response(matches.map(airport => ({
                            label: `${airport.code} - ${airport.name} (${airport.city})`,
                            value: airport.code
                        })));
                    },
                    minLength: 2,
                    select: function(event, ui) {
                        $(this).val(ui.item.value);
                        return false;
                    }
                });
            }
        },

        validateIATACode: function(code) {
            return /^[A-Z]{3}$/.test(code);
        }
    };

    // Initialisation du module
    FlightSearch.init();

    // Exposition globale pour usage externe
    window.FlightSearch = FlightSearch;

    // Ajout des styles CSS nécessaires
    if (!$('#flight-search-styles').length) {
        $('<style id="flight-search-styles">')
            .text(`
                .rotating {
                    animation: rotate 0.5s linear;
                }
                
                @keyframes rotate {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(180deg); }
                }
                
                .is-valid {
                    border-color: #28a745 !important;
                }
                
                .is-invalid {
                    border-color: #dc3545 !important;
                }
            `)
            .appendTo('head');
    }
});