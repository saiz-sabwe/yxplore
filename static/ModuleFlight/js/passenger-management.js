/**
 * Gestion des passagers pour la réservation de vol
 * Compatible avec l'API Duffel
 */

// Configuration des passagers
let currentPassengers = {
	adults: 1,
	children: 0,
	infants: 0
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
	console.log('Passenger management JS loaded - Initializing...');
	// Initialiser le formulaire immédiatement
	updatePassengerForm();
});

// Initialisation alternative si DOMContentLoaded n'a pas fonctionné
window.addEventListener('load', function() {
	console.log('Window loaded - Checking passenger form...');
	// Vérifier si le formulaire est déjà généré
	const container = document.getElementById('passenger-forms-container');
	if (container && container.children.length === 0) {
		console.log('No passenger forms found, initializing...');
		updatePassengerForm();
	}
});

// Mise à jour du formulaire de passagers
function updatePassengerForm() {
	console.log('Updating passenger form...');
	
	const adultCount = parseInt(document.getElementById('adult-count').value);
	const childCount = parseInt(document.getElementById('child-count').value);
	const infantCount = parseInt(document.getElementById('infant-count').value);

	console.log('Counts - Adults:', adultCount, 'Children:', childCount, 'Infants:', infantCount);

	currentPassengers = {
		adults: adultCount,
		children: childCount,
		infants: infantCount
	};

	// Validation : au moins 1 adulte
	if (adultCount < 1) {
		if (typeof showNotification === 'function') {
			showNotification('Erreur', 'Au moins 1 adulte est requis', 'error');
		}
		document.getElementById('adult-count').value = 1;
		currentPassengers.adults = 1;
	}

	// Validation : pas plus de 5 adultes
	if (adultCount > 5) {
		if (typeof showNotification === 'function') {
			showNotification('Erreur', 'Maximum 5 adultes autorisés', 'error');
		}
		document.getElementById('adult-count').value = 5;
		currentPassengers.adults = 5;
	}

	// Validation : pas plus d'infants que d'adultes
	if (infantCount > adultCount) {
		if (typeof showNotification === 'function') {
			showNotification('Erreur', 'Le nombre de bébés ne peut pas dépasser le nombre d\'adultes', 'error');
		}
		document.getElementById('infant-count').value = adultCount;
		currentPassengers.infants = adultCount;
	}

	// Mise à jour du total
	const totalElement = document.getElementById('total-passengers');
	if (totalElement) {
		totalElement.textContent = adultCount + childCount + infantCount;
	}

	// Génération des formulaires
	generatePassengerForms();
}

// Génération des formulaires de passagers
function generatePassengerForms() {
	const container = document.getElementById('passenger-forms-container');
	container.innerHTML = '';

	// Génération des formulaires pour adultes
	for (let i = 0; i < currentPassengers.adults; i++) {
		container.appendChild(createPassengerForm('adult', i + 1, 'Adulte'));
	}

	// Génération des formulaires pour enfants
	for (let i = 0; i < currentPassengers.children; i++) {
		container.appendChild(createPassengerForm('child', i + 1, 'Enfant'));
	}

	// Génération des formulaires pour bébés
	for (let i = 0; i < currentPassengers.infants; i++) {
		container.appendChild(createPassengerForm('infant', i + 1, 'Bébé'));
	}
}

// Création d'un formulaire de passager
function createPassengerForm(passengerType, index, label) {
	const formDiv = document.createElement('div');
	formDiv.className = 'border rounded p-4 mb-3';
	formDiv.innerHTML = `
		<h6 class="mb-3">${label} ${index}</h6>
		<div class="row">
			<div class="col-md-2">
				<label class="form-label">Civilité *</label>
				<select class="form-select" name="passenger_${passengerType}_${index}_title" required>
					<option value="">Sélectionner</option>
					<option value="mr">M.</option>
					<option value="mrs">Mme</option>
					<option value="ms">Mlle</option>
				</select>
			</div>
			<div class="col-md-5">
				<label class="form-label">Prénom *</label>
				<input type="text" class="form-control" name="passenger_${passengerType}_${index}_given_name" required>
			</div>
			<div class="col-md-5">
				<label class="form-label">Nom de famille *</label>
				<input type="text" class="form-control" name="passenger_${passengerType}_${index}_family_name" required>
			</div>
		</div>
		<div class="row mt-3">
			<div class="col-md-3">
				<label class="form-label">Genre *</label>
				<select class="form-select" name="passenger_${passengerType}_${index}_gender" required>
					<option value="">Sélectionner</option>
					<option value="m">Masculin</option>
					<option value="f">Féminin</option>
					<option value="x">Autre</option>
				</select>
			</div>
			<div class="col-md-3">
				<label class="form-label">Date de naissance *</label>
				<input type="date" class="form-control" name="passenger_${passengerType}_${index}_date_of_birth" required>
			</div>
			<div class="col-md-3">
				<label class="form-label">Nationalité *</label>
				<select class="form-select" name="passenger_${passengerType}_${index}_nationality" required>
					<option value="">Sélectionner</option>
					<option value="FR">France</option>
					<option value="DE">Allemagne</option>
					<option value="NL">Pays-Bas</option>
					<option value="BE">Belgique</option>
					<option value="CH">Suisse</option>
					<option value="IT">Italie</option>
					<option value="ES">Espagne</option>
					<option value="GB">Royaume-Uni</option>
					<option value="US">États-Unis</option>
					<option value="CA">Canada</option>
				</select>
			</div>
			<div class="col-md-3">
				<label class="form-label">Type de passager</label>
				<input type="text" class="form-control" name="passenger_${passengerType}_${index}_type" value="${passengerType}" readonly>
			</div>
		</div>
		<div class="row mt-3">
			<div class="col-md-4">
				<label class="form-label">Type de document *</label>
				<select class="form-select" name="passenger_${passengerType}_${index}_identity_document_type" required>
					<option value="">Sélectionner</option>
					<option value="passport">Passeport</option>
				</select>
			</div>
			<div class="col-md-4">
				<label class="form-label">Numéro de document *</label>
				<input type="text" class="form-control" name="passenger_${passengerType}_${index}_identity_document_number" required>
			</div>
			<div class="col-md-4">
				<label class="form-label">Pays d'émission *</label>
				<select class="form-select" name="passenger_${passengerType}_${index}_identity_document_country" required>
					<option value="">Sélectionner</option>
					<option value="FR">France</option>
					<option value="DE">Allemagne</option>
					<option value="NL">Pays-Bas</option>
					<option value="BE">Belgique</option>
					<option value="CH">Suisse</option>
					<option value="IT">Italie</option>
					<option value="ES">Espagne</option>
					<option value="GB">Royaume-Uni</option>
					<option value="US">États-Unis</option>
					<option value="CA">Canada</option>
				</select>
			</div>
		</div>
		<div class="row mt-3">
			<div class="col-md-6">
				<label class="form-label">Date d'expiration *</label>
				<input type="date" class="form-control" name="passenger_${passengerType}_${index}_identity_document_expiry" required>
			</div>
			<div class="col-md-6">
				<label class="form-label">Pays de résidence</label>
				<select class="form-select" name="passenger_${passengerType}_${index}_residence_country">
					<option value="">Sélectionner</option>
					<option value="FR">France</option>
					<option value="DE">Allemagne</option>
					<option value="NL">Pays-Bas</option>
					<option value="BE">Belgique</option>
					<option value="CH">Suisse</option>
					<option value="IT">Italie</option>
					<option value="ES">Espagne</option>
					<option value="GB">Royaume-Uni</option>
					<option value="US">États-Unis</option>
					<option value="CA">Canada</option>
				</select>
			</div>
		</div>
	`;

	return formDiv;
}

// Validation du formulaire
function validatePassengerForm() {
	const requiredFields = document.querySelectorAll('[required]');
	let isValid = true;
	let missingFields = [];

	requiredFields.forEach(field => {
		if (!field.value.trim()) {
			isValid = false;
			field.classList.add('is-invalid');
			const fieldName = field.previousElementSibling?.textContent || 'Champ';
			missingFields.push(fieldName);
		} else {
			field.classList.remove('is-invalid');
		}
	});

	if (!isValid) {
		showNotification('Validation', `Veuillez remplir tous les champs obligatoires : ${missingFields.join(', ')}`, 'warning');
	}

	return isValid;
}

// Collecte des données des passagers
function collectPassengerData() {
	const passengers = [];
	let passengerIndex = 0;

	// Collecte des adultes
	for (let i = 0; i < currentPassengers.adults; i++) {
		const passenger = collectSinglePassengerData('adult', i + 1, passengerIndex);
		if (passenger) {
			passengers.push(passenger);
			passengerIndex++;
		}
	}

	// Collecte des enfants
	for (let i = 0; i < currentPassengers.children; i++) {
		const passenger = collectSinglePassengerData('child', i + 1, passengerIndex);
		if (passenger) {
			passengers.push(passenger);
			passengerIndex++;
		}
	}

	// Collecte des bébés
	for (let i = 0; i < currentPassengers.infants; i++) {
		const passenger = collectSinglePassengerData('infant', i + 1, passengerIndex);
		if (passenger) {
			passengers.push(passenger);
			passengerIndex++;
		}
	}

	return passengers;
}

// Collecte des données d'un passager individuel
function collectSinglePassengerData(passengerType, index, passengerIndex) {
	const prefix = `passenger_${passengerType}_${index}`;
	
	const passenger = {
		type: passengerType,
		title: document.querySelector(`[name="${prefix}_title"]`)?.value,
		given_name: document.querySelector(`[name="${prefix}_given_name"]`)?.value,
		family_name: document.querySelector(`[name="${prefix}_family_name"]`)?.value,
		gender: document.querySelector(`[name="${prefix}_gender"]`)?.value,
		date_of_birth: document.querySelector(`[name="${prefix}_date_of_birth"]`)?.value,
		nationality: document.querySelector(`[name="${prefix}_nationality"]`)?.value,
		identity_documents: [{
			type: document.querySelector(`[name="${prefix}_identity_document_type"]`)?.value,
			unique_identifier: document.querySelector(`[name="${prefix}_identity_document_number"]`)?.value,
			issuing_country_code: document.querySelector(`[name="${prefix}_identity_document_country"]`)?.value,
			expiry_date: document.querySelector(`[name="${prefix}_identity_document_expiry"]`)?.value
		}]
	};

	// Ajout du pays de résidence si spécifié
	const residenceCountry = document.querySelector(`[name="${prefix}_residence_country"]`)?.value;
	if (residenceCountry) {
		passenger.country_code = residenceCountry;
	}

	return passenger;
}

// Soumission de la réservation
function submitBooking() {
	if (!validatePassengerForm()) {
		return;
	}

	const passengers = collectPassengerData();
	if (passengers.length === 0) {
		if (typeof showNotification === 'function') {
			showNotification('Erreur', 'Aucun passager valide trouvé', 'error');
		}
		return;
	}

	// Récupération des données de l'offre depuis le bouton de réservation
	const bookButton = document.querySelector('button[onclick="submitBooking()"]');
	const offerId = bookButton?.getAttribute('data-offer-id') || '{{ offer.id }}';
	const totalAmount = bookButton?.getAttribute('data-total-amount') || '{{ offer.total_amount }}';
	const totalCurrency = bookButton?.getAttribute('data-total-currency') || '{{ offer.total_currency }}';

	console.log('Booking data:', { offerId, totalAmount, totalCurrency, passengers });

	// Données de la réservation
	const bookingData = {
		offer_id: offerId,
		passengers: passengers,
		total_amount: totalAmount,
		total_currency: totalCurrency
	};

	// Affichage du loading
	if (typeof showNotification === 'function') {
		showNotification('Réservation en cours...', 'Veuillez patienter', 'info');
	}

	// Envoi AJAX
	$.ajax({
		url: '/flights/book/',
		type: 'POST',
		data: JSON.stringify(bookingData),
		contentType: 'application/json',
		headers: {
			'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
		},
		success: function(response) {
			console.log('Booking response:', response);
			if (response.resultat === 'SUCCESS') {
				if (typeof showNotification === 'function') {
					showNotification('Succès !', 'Réservation créée avec succès', 'success');
				}
				// Redirection vers la page de paiement
				setTimeout(() => {
					window.location.href = response.redirect_url;
				}, 2000);
			} else {
				if (typeof showNotification === 'function') {
					showNotification('Erreur', response.message || 'Erreur lors de la réservation', 'error');
				}
			}
		},
		error: function(xhr, status, error) {
			console.error('Erreur AJAX:', error);
			console.error('Response:', xhr.responseText);
			if (typeof showNotification === 'function') {
				showNotification('Erreur', 'Erreur lors de la communication avec le serveur', 'error');
			}
		}
	});
}
