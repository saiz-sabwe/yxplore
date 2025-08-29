"""
Service pour les appels API Duffel
Encapsule toutes les interactions avec l'API Duffel
"""

import requests
import json
from datetime import datetime, date
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class DuffelAPIError(Exception):
    """Exception personnalisée pour les erreurs API Duffel"""
    pass


class DuffelService:
    """Service pour interagir avec l'API Duffel"""
    
    def __init__(self):
        # Configuration depuis settings
        self.live_mode = getattr(settings, 'DUFFEL_LIVE_MODE', False)
        self.api_key = getattr(settings, 'DUFFEL_API_KEY_LIVE' if self.live_mode else 'DUFFEL_API_KEY', None)
        self.base_url = getattr(settings, 'DUFFEL_BASE_URL', 'https://api.duffel.com/air')
        self.api_version = getattr(settings, 'DUFFEL_API_VERSION', 'v2')
        
        # Configuration avancée
        self.config = getattr(settings, 'DUFFEL_CONFIG', {})
        self.timeout = self.config.get('REQUEST_TIMEOUT', 30)
        self.max_retries = self.config.get('MAX_RETRIES', 3)
        self.retry_delay = self.config.get('RETRY_DELAY', 1)
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Duffel-Version': self.api_version,
            'User-Agent': 'YXplore-Flight-Module/1.0'
        }
        
        if not self.api_key:
            logger.warning(f"DUFFEL_API_KEY non configurée pour le mode {'production' if self.live_mode else 'test'}")
            
        logger.info(f"DuffelService initialisé - Mode: {'LIVE' if self.live_mode else 'TEST'}")
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Effectue une requête HTTP vers l'API Duffel"""
        try:
            url = f"{self.base_url}/{endpoint}"
            
            logger.info(f"=== REQUÊTE DUFFEL DÉTAILLÉE ===")
            logger.info(f"Méthode: {method}")
            logger.info(f"URL: {url}")
            logger.info(f"Headers: {json.dumps(self.headers, indent=2)}")
            if data:
                logger.info(f"Body: {json.dumps(data, indent=2)}")
            if params:
                logger.info(f"Params: {params}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=self.timeout
            )
            
            logger.info(f"=== RÉPONSE DUFFEL ===")
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code >= 400:
                error_data = {}
                try:
                    if response.content:
                        error_data = response.json()
                        logger.error(f"Erreur API Duffel: {response.status_code} - {json.dumps(error_data, indent=2)}")
                    else:
                        logger.error(f"Erreur API Duffel: {response.status_code} - Pas de contenu")
                except:
                    logger.error(f"Erreur API Duffel: {response.status_code} - Contenu non-JSON: {response.text}")
                
                # Log du contenu brut pour debug
                logger.error(f"Contenu brut de la réponse: {response.text}")
                
                raise DuffelAPIError(f"Erreur API Duffel: {response.status_code} - {error_data.get('errors', [{}])[0].get('message', 'Erreur inconnue') if error_data.get('errors') else 'Pas de détails'}")
            
            # Succès
            response_data = response.json()
            logger.info(f"Réponse réussie: {len(response_data.get('data', []))} éléments")
            logger.info("=== FIN REQUÊTE DUFFEL ===")
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion Duffel: {str(e)}")
            raise DuffelAPIError(f"Erreur de connexion: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON: {str(e)}")
            logger.error(f"Contenu reçu: {response.text if 'response' in locals() else 'Pas de réponse'}")
            raise DuffelAPIError("Réponse invalide de l'API Duffel")
    
    def search_flights(self, origin, destination, departure_date, return_date=None, 
                      passengers=1, cabin_class='economy'):
        """
        Recherche des vols via l'API Duffel
        
        Args:
            origin (str): Code IATA de l'aéroport de départ
            destination (str): Code IATA de l'aéroport d'arrivée
            departure_date (date): Date de départ
            return_date (date, optional): Date de retour pour aller-retour
            passengers (int): Nombre de passagers
            cabin_class (str): Classe de cabine
        
        Returns:
            dict: Données de l'offre request et des offres
        """
        try:
            logger.info(f"=== DÉBUT RECHERCHE DUFFEL ===")
            logger.info(f"Origin: {origin}, Destination: {destination}")
            logger.info(f"Departure: {departure_date} (type: {type(departure_date)})")
            logger.info(f"Return: {return_date} (type: {type(return_date)})")
            logger.info(f"Passengers: {passengers}, Cabin: {cabin_class}")
            
            # Préparation des données de recherche
            slices = [
                {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date.isoformat()
                }
            ]
            
            # Ajouter le vol retour si spécifié
            if return_date:
                slices.append({
                    "origin": destination,
                    "destination": origin,
                    "departure_date": return_date.isoformat()
                })
            
            # Configuration des passagers
            passenger_config = []
            for _ in range(passengers):
                passenger_config.append({
                    "type": "adult"
                })
            
            search_data = {
                "data": {
                    "slices": slices,
                    "passengers": passenger_config,
                    "cabin_class": cabin_class
                }
            }
            
            logger.info(f"Données de recherche: {json.dumps(search_data, indent=2)}")
            logger.info(f"Headers: {self.headers}")
            
            # Créer la demande d'offre
            logger.info("Création de la demande d'offre...")
            logger.info(f"Endpoint: offer_requests")
            logger.info(f"URL complète: {self.base_url}/offer_requests")
            
            offer_request_response = self._make_request(
                'POST', 
                'offer_requests',
                data=search_data
            )
            
            logger.info(f"Demande d'offre créée: {offer_request_response['data']['id']}")
            
            offer_request_id = offer_request_response['data']['id']
            
            # Récupérer les offres
            logger.info("Récupération des offres...")
            logger.info(f"Endpoint: offers (avec filtrage)")
            
            # Selon la collection Postman, l'endpoint est /offers avec des paramètres
            offers_response = self._make_request(
                'GET',
                'offers',
                params={
                    'offer_request_id': offer_request_id,
                    'limit': 50
                }
            )
            
            logger.info(f"Offres récupérées: {len(offers_response['data'])} offres")
            logger.info("=== FIN RECHERCHE DUFFEL ===")
            
            return {
                'offer_request': offer_request_response['data'],
                'offers': offers_response['data']
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de vols: {str(e)}")
            logger.error(f"Type d'erreur: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise DuffelAPIError(f"Erreur lors de la recherche: {str(e)}")
    
    def get_offer(self, offer_id):
        """
        Récupère les détails d'une offre spécifique
        
        Args:
            offer_id (str): ID de l'offre Duffel
        
        Returns:
            dict: Détails de l'offre
        """
        try:
            logger.info(f"Récupération de l'offre: {offer_id}")
            
            response = self._make_request('GET', f'offers/{offer_id}')
            return response['data']
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'offre {offer_id}: {str(e)}")
            raise DuffelAPIError(f"Erreur lors de la récupération de l'offre: {str(e)}")
    
    def create_booking(self, offer_id, passenger_data, payment_data):
        """
        Crée une réservation sur Duffel
        
        Args:
            offer_id (str): ID de l'offre Duffel
            passenger_data (list): Données des passagers avec IDs de l'offer_request
            payment_data (dict): Données de paiement
        
        Returns:
            dict: Données de la réservation créée
        """
        try:
            booking_data = {
                "data": {
                    "selected_offers": [offer_id],
                    "passengers": passenger_data,
                    "payments": [payment_data]
                }
            }
            
            logger.info(f"Création de réservation pour l'offre: {offer_id}")
            
            response = self._make_request('POST', 'orders', data=booking_data)
            return response['data']
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de réservation: {str(e)}")
            raise DuffelAPIError(f"Erreur lors de la création de réservation: {str(e)}")
    
    def confirm_booking(self, booking_id):
        """
        Confirme une réservation
        
        Args:
            booking_id (str): ID de la réservation Duffel
        
        Returns:
            dict: Données de la réservation confirmée
        """
        try:
            logger.info(f"Confirmation de réservation: {booking_id}")
            
            response = self._make_request(
                'POST', 
                f'orders/{booking_id}/actions/confirm'
            )
            return response['data']
            
        except Exception as e:
            logger.error(f"Erreur lors de la confirmation: {str(e)}")
            raise DuffelAPIError(f"Erreur lors de la confirmation: {str(e)}")
    
    def cancel_booking(self, booking_id):
        """
        Annule une réservation
        
        Args:
            booking_id (str): ID de la réservation Duffel
        
        Returns:
            dict: Données de l'annulation
        """
        try:
            logger.info(f"Annulation de réservation: {booking_id}")
            
            response = self._make_request(
                'POST', 
                f'orders/{booking_id}/actions/cancel'
            )
            return response['data']
            
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation: {str(e)}")
            raise DuffelAPIError(f"Erreur lors de l'annulation: {str(e)}")
    
    def get_booking_details(self, booking_id):
        """
        Récupère les détails d'une réservation
        
        Args:
            booking_id (str): ID de la réservation Duffel
        
        Returns:
            dict: Détails de la réservation
        """
        try:
            logger.info(f"Récupération des détails de réservation: {booking_id}")
            
            response = self._make_request('GET', f'orders/{booking_id}')
            return response['data']
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails: {str(e)}")
            raise DuffelAPIError(f"Erreur lors de la récupération: {str(e)}")
    
    def format_offer_for_frontend(self, offer):
        """
        Formate une offre de l'API Duffel pour l'affichage frontend.
        Exploite toutes les données riches disponibles dans l'API v2.
        """
        try:
            if not offer or 'id' not in offer:
                logger.warning("Offre invalide reçue")
                return None

            # Extraction des informations de base
            formatted_offer = {
                'id': offer.get('id'),
                'total_amount': offer.get('total_amount'),
                'total_currency': offer.get('total_currency'),
                'base_amount': offer.get('base_amount'),
                'tax_amount': offer.get('tax_amount'),
                'base_currency': offer.get('base_currency'),
                'tax_currency': offer.get('tax_currency'),
                'total_emissions_kg': offer.get('total_emissions_kg'),
                'owner': {
                    'name': offer.get('owner', {}).get('name', 'Compagnie inconnue'),
                    'iata_code': offer.get('owner', {}).get('iata_code', ''),
                    'logo_symbol_url': offer.get('owner', {}).get('logo_symbol_url', ''),
                    'logo_lockup_url': offer.get('owner', {}).get('logo_lockup_url', ''),
                    'id': offer.get('owner', {}).get('id', '')
                },
                'passenger_identity_documents_required': offer.get('passenger_identity_documents_required', False),
                'available_seats': 10,  # Valeur par défaut
                'live_mode': offer.get('live_mode', False),
                'created_at': offer.get('created_at'),
                'expires_at': offer.get('expires_at'),
                'partial': offer.get('partial', False)
            }

            # Traitement des slices (segments de vol)
            slices = offer.get('slices', [])
            if slices:
                formatted_offer['slices'] = []
                
                for slice_idx, slice_data in enumerate(slices):
                    segments = slice_data.get('segments', [])
                    
                    if segments:
                        # Premier segment du slice
                        first_segment = segments[0]
                        
                        # Informations de vol détaillées
                        slice_info = {
                            'id': slice_data.get('id'),
                            'fare_brand_name': slice_data.get('fare_brand_name'),
                            'origin': {
                                'iata_code': first_segment.get('origin', {}).get('iata_code', ''),
                                'name': first_segment.get('origin', {}).get('name', 'Aéroport inconnu'),
                                'city_name': first_segment.get('origin', {}).get('city_name', ''),
                                'terminal': first_segment.get('origin_terminal', ''),
                                'latitude': first_segment.get('origin', {}).get('latitude'),
                                'longitude': first_segment.get('origin', {}).get('longitude'),
                                'time_zone': first_segment.get('origin', {}).get('time_zone')
                            },
                            'destination': {
                                'iata_code': first_segment.get('destination', {}).get('iata_code', ''),
                                'name': first_segment.get('destination', {}).get('name', 'Aéroport inconnu'),
                                'city_name': first_segment.get('destination', {}).get('city_name', ''),
                                'terminal': first_segment.get('destination_terminal', ''),
                                'latitude': first_segment.get('destination', {}).get('latitude'),
                                'longitude': first_segment.get('destination', {}).get('longitude'),
                                'time_zone': first_segment.get('destination', {}).get('time_zone')
                            },
                            'segments': [],
                            'duration': slice_data.get('duration', ''),
                            'stops': len(segments) - 1,  # Nombre d'escales
                            'conditions': slice_data.get('conditions', {})
                        }
                        
                        # Traitement de tous les segments du slice
                        for segment in segments:
                            segment_info = {
                                'id': segment.get('id'),
                                'departing_at': segment.get('departing_at', ''),
                                'arriving_at': segment.get('arriving_at', ''),
                                'duration': segment.get('duration', ''),
                                'distance': segment.get('distance'),
                                'operating_carrier': {
                                    'name': segment.get('operating_carrier', {}).get('name', ''),
                                    'iata_code': segment.get('operating_carrier', {}).get('iata_code', ''),
                                    'flight_number': segment.get('operating_carrier_flight_number', ''),
                                    'logo_symbol_url': segment.get('operating_carrier', {}).get('logo_symbol_url', ''),
                                    'id': segment.get('operating_carrier', {}).get('id', '')
                                },
                                'marketing_carrier': {
                                    'name': segment.get('marketing_carrier', {}).get('name', ''),
                                    'iata_code': segment.get('marketing_carrier', {}).get('iata_code', ''),
                                    'flight_number': segment.get('marketing_carrier_flight_number', ''),
                                    'logo_symbol_url': segment.get('marketing_carrier', {}).get('logo_symbol_url', ''),
                                    'id': segment.get('marketing_carrier', {}).get('id', '')
                                },
                                'stops': segment.get('stops', []),
                                'origin_terminal': segment.get('origin_terminal'),
                                'destination_terminal': segment.get('destination_terminal'),
                                'aircraft': segment.get('aircraft'),
                                'passengers': segment.get('passengers', [])
                            }
                            
                            slice_info['segments'].append(segment_info)
                        
                        formatted_offer['slices'].append(slice_info)

            # Informations de paiement détaillées
            payment_reqs = offer.get('payment_requirements', {})
            if payment_reqs:
                formatted_offer['payment'] = {
                    'requires_instant_payment': payment_reqs.get('requires_instant_payment', False),
                    'price_guarantee_expires_at': payment_reqs.get('price_guarantee_expires_at', ''),
                    'payment_required_by': payment_reqs.get('payment_required_by', '')
                }

            # Conditions de l'offre détaillées
            conditions = offer.get('conditions', {})
            if conditions:
                formatted_offer['conditions'] = {
                    'refundable': conditions.get('refund_before_departure', {}).get('allowed', False) if conditions.get('refund_before_departure') else False,
                    'refund_penalty_amount': conditions.get('refund_before_departure', {}).get('penalty_amount') if conditions.get('refund_before_departure') else None,
                    'refund_penalty_currency': conditions.get('refund_before_departure', {}).get('penalty_currency') if conditions.get('refund_before_departure') else None,
                    'changeable': conditions.get('change_before_departure', {}).get('allowed', False) if conditions.get('change_before_departure') else False,
                    'change_penalty_amount': conditions.get('change_before_departure', {}).get('penalty_amount') if conditions.get('change_before_departure') else None,
                    'change_penalty_currency': conditions.get('change_before_departure', {}).get('penalty_currency') if conditions.get('change_before_departure') else None
                }
            else:
                formatted_offer['conditions'] = {
                    'refundable': False,
                    'refund_penalty_amount': None,
                    'refund_penalty_currency': None,
                    'changeable': False,
                    'change_penalty_amount': None,
                    'change_penalty_currency': None
                }

            # Conditions des slices (plus détaillées)
            if offer.get('slices'):
                for slice_data in offer['slices']:
                    slice_conditions = slice_data.get('conditions', {})
                    if slice_conditions:
                        # Ajouter les conditions spécifiques au slice
                        if 'change_before_departure' in slice_conditions:
                            change_info = slice_conditions['change_before_departure']
                            if change_info and change_info.get('allowed'):
                                formatted_offer['slice_conditions'] = {
                                    'change_before_departure': {
                                        'allowed': True,
                                        'penalty_amount': change_info.get('penalty_amount'),
                                        'penalty_currency': change_info.get('penalty_currency')
                                    }
                                }

            # Informations sur les passagers
            passengers = offer.get('passengers', [])
            if passengers:
                formatted_offer['passengers'] = []
                for passenger in passengers:
                    passenger_info = {
                        'id': passenger.get('id'),
                        'type': passenger.get('type'),
                        'age': passenger.get('age'),
                        'family_name': passenger.get('family_name'),
                        'given_name': passenger.get('given_name'),
                        'fare_type': passenger.get('fare_type'),
                        'loyalty_programme_accounts': passenger.get('loyalty_programme_accounts', [])
                    }
                    formatted_offer['passengers'].append(passenger_info)

            # Services supportés
            formatted_offer['supported_passenger_identity_document_types'] = offer.get('supported_passenger_identity_document_types', [])
            formatted_offer['supported_loyalty_programmes'] = offer.get('supported_loyalty_programmes', [])

            # Services disponibles
            formatted_offer['available_services'] = offer.get('available_services')

            logger.info(f"Offre formatée: {offer.get('id')} - {formatted_offer['owner']['name']} - {formatted_offer['total_amount']} {formatted_offer['total_currency']}")

            return formatted_offer

        except Exception as e:
            logger.error(f"Erreur lors du formatage de l'offre: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def get_offer_details(self, offer_id):
        """
        Récupère les détails complets d'une offre via l'endpoint /air/offers/{OFFER_ID}
        
        Args:
            offer_id (str): ID de l'offre (ex: off_0000AxePR1Bp3LJq0ToDYL)
        
        Returns:
            dict: Détails complets de l'offre
        """
        try:
            logger.info(f"Récupération des détails de l'offre: {offer_id}")
            
            response = self._make_request('GET', f'offers/{offer_id}')
            
            if response and 'data' in response:
                offer_details = response['data']
                logger.info(f"Détails de l'offre récupérés avec succès: {offer_id}")
                return offer_details
            else:
                logger.error(f"Réponse invalide pour l'offre {offer_id}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails de l'offre {offer_id}: {str(e)}")
            raise DuffelAPIError(f"Impossible de récupérer les détails de l'offre: {str(e)}")
    
    def _extract_baggage_info(self, offer):
        """Extrait les informations sur les bagages"""
        try:
            # Cette fonction devra être adaptée selon la structure réelle de l'API Duffel
            baggage_info = {
                'cabin': '1 bagage cabine (dimensions standard)',
                'checked': 'Selon la compagnie aérienne'
            }
            
            # Extraction des vraies données si disponibles
            services = offer.get('available_services', [])
            for service in services:
                if 'baggage' in service.get('type', '').lower():
                    baggage_info['checked'] = service.get('total_amount', 'Payant')
            
            return baggage_info
            
        except Exception:
            return {
                'cabin': '1 bagage cabine',
                'checked': 'Selon tarif'
            }
    
    def validate_passenger_data(self, passenger_data, for_booking=False):
        """
        Valide les données des passagers pour Duffel
        
        Args:
            passenger_data (list): Liste des données passagers
            for_booking (bool): Si True, valide pour création de réservation
        
        Returns:
            bool: True si valide
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        if not isinstance(passenger_data, list):
            raise ValidationError("Les données des passagers doivent être une liste")
        
        for i, passenger in enumerate(passenger_data):
            if not isinstance(passenger, dict):
                raise ValidationError(f"Passager {i+1}: données invalides")
            
            # Champs requis pour recherche
            required_fields = ['given_name', 'family_name', 'gender', 'born_on']
            
            # Champs supplémentaires requis pour réservation
            if for_booking:
                required_fields.extend(['id', 'title', 'email', 'phone_number'])
            
            for field in required_fields:
                if field not in passenger:
                    raise ValidationError(f"Passager {i+1}: champ '{field}' manquant")
            
            # Validation du format de date de naissance
            try:
                datetime.strptime(passenger['born_on'], '%Y-%m-%d')
            except ValueError:
                raise ValidationError(f"Passager {i+1}: format de date de naissance invalide")
            
            # Validation du genre
            if passenger['gender'] not in ['m', 'f']:
                raise ValidationError(f"Passager {i+1}: genre doit être 'm' ou 'f'")
            
            # Validation du titre pour réservation
            if for_booking and passenger.get('title') not in ['mr', 'mrs', 'ms']:
                raise ValidationError(f"Passager {i+1}: titre doit être 'mr', 'mrs' ou 'ms'")
        
        return True
    
    def format_passenger_for_booking(self, passenger_data, offer_request_passengers):
        """
        Formate les données passagers pour la création de réservation
        
        Args:
            passenger_data (list): Données passagers du frontend
            offer_request_passengers (list): IDs passagers de l'offer_request
        
        Returns:
            list: Données passagers formatées pour Duffel
        """
        formatted_passengers = []
        
        for i, passenger in enumerate(passenger_data):
            # Récupération de l'ID passager de l'offer_request
            if i < len(offer_request_passengers):
                passenger_id = offer_request_passengers[i]['id']
            else:
                raise ValidationError(f"Passager {i+1}: ID manquant dans l'offer_request")
            
            formatted_passenger = {
                'id': passenger_id,
                'given_name': passenger['given_name'],
                'family_name': passenger['family_name'],
                'title': passenger['title'],
                'gender': passenger['gender'],
                'born_on': passenger['born_on'],
                'email': passenger['email'],
                'phone_number': passenger['phone_number']
            }
            
            # Gestion des bébés avec passager responsable
            if 'infant_passenger_id' in passenger:
                formatted_passenger['infant_passenger_id'] = passenger['infant_passenger_id']
            
            formatted_passengers.append(formatted_passenger)
        
        return formatted_passengers
    
    def create_payment_data(self, amount, currency, payment_type='balance'):
        """
        Crée les données de paiement pour Duffel
        
        Args:
            amount (str): Montant du paiement
            currency (str): Devise du paiement
            payment_type (str): Type de paiement ('balance' ou 'arc_bsp_cash')
        
        Returns:
            dict: Données de paiement formatées
        """
        return {
            'type': payment_type,
            'currency': currency,
            'amount': str(amount)
        }

    def test_with_static_data(self, origin, destination, departure_date, return_date=None, 
                             passengers=1, cabin_class='economy'):
        """
        Méthode de test avec des données statiques pour vérifier le formatage
        """
        logger.info("=== TEST AVEC DONNÉES STATIQUES ===")
        
        # Données statiques basées sur votre exemple
        static_offers = [
            {
                "id": "off_static_001",
                "total_amount": "1597.65",
                "total_currency": "EUR",
                "owner": {
                    "name": "British Airways",
                    "iata_code": "BA"
                },
                "passenger_identity_documents_required": False,
                "live_mode": False,
                "slices": [
                    {
                        "segments": [
                            {
                                "origin": {
                                    "iata_code": origin,
                                    "name": f"Aéroport {origin}"
                                },
                                "destination": {
                                    "iata_code": destination,
                                    "name": f"Aéroport {destination}"
                                },
                                "departing_at": f"{departure_date.isoformat()}T15:29:00",
                                "arriving_at": f"{departure_date.isoformat()}T17:41:00",
                                "duration": "PT2H12M",
                                "operating_carrier": {
                                    "name": "British Airways",
                                    "flight_number": "0107"
                                },
                                "operating_carrier_flight_number": "0107"
                            }
                        ],
                        "duration": "PT2H12M",
                        "origin": {
                            "iata_code": origin,
                            "name": f"Aéroport {origin}"
                        },
                        "destination": {
                            "iata_code": destination,
                            "name": f"Aéroport {destination}"
                        }
                    }
                ]
            },
            {
                "id": "off_static_002",
                "total_amount": "1623.61",
                "total_currency": "EUR",
                "owner": {
                    "name": "American Airlines",
                    "iata_code": "AA"
                },
                "passenger_identity_documents_required": True,
                "live_mode": False,
                "slices": [
                    {
                        "segments": [
                            {
                                "origin": {
                                    "iata_code": origin,
                                    "name": f"Aéroport {origin}"
                                },
                                "destination": {
                                    "iata_code": destination,
                                    "name": f"Aéroport {destination}"
                                },
                                "departing_at": f"{departure_date.isoformat()}T14:00:00",
                                "arriving_at": f"{departure_date.isoformat()}T16:15:00",
                                "duration": "PT2H15M",
                                "operating_carrier": {
                                    "name": "American Airlines",
                                    "flight_number": "118"
                                },
                                "operating_carrier_flight_number": "118"
                            }
                        ],
                        "duration": "PT2H15M",
                        "origin": {
                            "iata_code": origin,
                            "name": f"Aéroport {origin}"
                        },
                        "destination": {
                            "iata_code": destination,
                            "name": f"Aéroport {destination}"
                        }
                    }
                ]
            }
        ]
        
        # Si c'est un aller-retour, ajouter le vol retour
        if return_date:
            for offer in static_offers:
                return_slice = {
                    "segments": [
                        {
                            "origin": {
                                "iata_code": destination,
                                "name": f"Aéroport {destination}"
                            },
                            "destination": {
                                "iata_code": origin,
                                "name": f"Aéroport {origin}"
                            },
                            "departing_at": f"{return_date.isoformat()}T15:29:00",
                            "arriving_at": f"{return_date.isoformat()}T17:44:00",
                            "duration": "PT2H15M",
                            "operating_carrier": {
                                "name": offer["owner"]["name"],
                                "flight_number": "0108"
                            },
                            "operating_carrier_flight_number": "0108"
                        }
                    ],
                    "duration": "PT2H15M",
                    "origin": {
                        "iata_code": destination,
                        "name": f"Aéroport {destination}"
                    },
                    "destination": {
                        "iata_code": origin,
                        "name": f"Aéroport {origin}"
                    }
                }
                offer["slices"].append(return_slice)
        
        logger.info(f"Données statiques générées: {len(static_offers)} offres")
        logger.info("=== FIN TEST STATIQUE ===")
        
        return {
            'offer_request': {
                'id': 'orq_static_test',
                'slices': [
                    {
                        'origin': origin,
                        'destination': destination,
                        'departure_date': departure_date.isoformat()
                    }
                ] + ([{
                    'origin': destination,
                    'destination': origin,
                    'departure_date': return_date.isoformat()
                }] if return_date else [])
            },
            'offers': static_offers
        }


# Instance globale du service
duffel_service = DuffelService()
