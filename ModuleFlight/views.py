from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import datetime, date
from decimal import Decimal
import json
import logging

from .models import TravelAgency, MerchantAgency, FlightBooking, FlightUserManager, Passenger, FlightBookingDetail
from .duffel_service import duffel_service, DuffelAPIError
from ModuleProfils.models import ClientProfile, MerchantProfile

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class FlightView(View):
    """Vue principale pour le module Flight avec gestion par paramètres"""
    
    def get(self, request, param=None, **kwargs):
        """Gestion des requêtes GET selon le paramètre"""
        
        if param == "search":
            return self.search_flights(request)
        elif param == "results":
            return self.flight_results(request)
        elif param == "detail" or param == "flight_detail":
            offer_id = kwargs.get('offer_id')
            return self.flight_detail(request, offer_id)
        elif param == "Flight":  # Garde la compatibilité existante
            return self.search_flights(request)
        else:
            return self.search_flights(request)  # Par défaut
    
    def post(self, request, param=None, **kwargs):
        """Gestion des requêtes POST selon le paramètre"""
        
        # Vérifier si c'est une requête AJAX avec opération
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            op = request.POST.get('op', '')
            
            if op == 'search_flights':
                return self.ajax_search_flights(request)
            elif op == 'get_agencies':
                return self.ajax_get_agencies(request)
            elif op == 'create_booking':
                return self.ajax_create_booking(request)
            elif op == 'pay_booking':
                booking_id = kwargs.get('booking_id')
                return self.ajax_pay_booking(request, booking_id)
            elif op == 'cancel_booking':
                return self.ajax_cancel_booking(request)
            elif op == 'get_booking_details':
                return self.ajax_get_booking_details(request)
        
        # Logique POST standard (non-AJAX)
        if param == "book":
            return self.ajax_create_booking(request)
        elif param == "pay":
            booking_id = kwargs.get('booking_id')
            return self.pay_flight(request, booking_id)
        elif param == "cancel":
            return self.cancel_booking(request)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Action non reconnue'
            }, status=400)
    
    def search_flights(self, request):
        """Affiche le formulaire de recherche de vols"""
        try:
            # Récupérer les agences actives pour le sélecteur
            agencies = TravelAgency.get_active_agencies()
            
            # Vérifier si l'utilisateur est un marchand
            is_merchant = FlightUserManager.user_is_merchant(request.user)
            merchant_agencies = []
            
            if is_merchant:
                merchant_agencies = MerchantAgency.get_agencies_for_merchant(request.user)
            
            context = {
                'title': 'Recherche de vols',
                'agencies': agencies,
                'merchant_agencies': merchant_agencies,
                'is_merchant': is_merchant,
                'today': date.today().isoformat(),
            }
            
            return render(request, "ModuleFlight/affiche.html", context)
            
        except Exception as e:
            logger.error(f"Erreur dans search_flights: {str(e)}")
            context = {
                'title': 'Recherche de vols',
                'error': 'Erreur lors du chargement de la page'
            }
            return render(request, "ModuleFlight/affiche.html", context)
    
    def flight_results(self, request):
        """Affiche les résultats de recherche de vols"""
        try:
            # Récupération des paramètres de recherche
            origin = request.GET.get('origin', '').upper()
            destination = request.GET.get('destination', '').upper()
            departure_date = request.GET.get('departure_date')
            return_date = request.GET.get('return_date')
            passengers = int(request.GET.get('passengers', 1))
            cabin_class = request.GET.get('cabin_class', 'economy')
            
            # Validation des paramètres
            if not all([origin, destination, departure_date]):
                context = {
                    'title': 'Résultats de recherche',
                    'error': 'Paramètres de recherche manquants'
                }
                return render(request, "ModuleFlight/flight-list.html", context)
            
            # Conversion des dates
            try:
                # Gestion du format "27+Nov+2025" (Flatpickr)
                if '+' in departure_date:
                    # Format: "27+Nov+2025" -> "27 Nov 2025"
                    departure_date = departure_date.replace('+', ' ')
                
                # Essayer différents formats de date
                departure_date_obj = None
                date_formats = ['%Y-%m-%d', '%d %b %Y', '%d %B %Y', '%d/%m/%Y', '%d-%m-%Y']
                
                for date_format in date_formats:
                    try:
                        departure_date_obj = datetime.strptime(departure_date, date_format).date()
                        break
                    except ValueError:
                        continue
                
                if not departure_date_obj:
                    raise ValueError(f"Impossible de parser la date: {departure_date}")
                
                return_date_obj = None
                if return_date and return_date.strip():  # Vérifier que return_date n'est pas vide
                    if '+' in return_date:
                        return_date = return_date.replace('+', ' ')
                    
                    for date_format in date_formats:
                        try:
                            return_date_obj = datetime.strptime(return_date, date_format).date()
                            break
                        except ValueError:
                            continue
                    
                    if not return_date_obj:
                        raise ValueError(f"Impossible de parser la date de retour: {return_date}")
                        
            except ValueError as e:
                context = {
                    'title': 'Résultats de recherche',
                    'error': f'Format de date invalide: {str(e)}',
                    'error_type': 'date_format'
                }
                return render(request, "ModuleFlight/flight-list.html", context)
            
            # Recherche via l'API Duffel
            try:
                # Réactivation de l'API Duffel réelle
                logger.info("Tentative de connexion à l'API Duffel réelle")
                search_results = duffel_service.search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date_obj,
                    return_date=return_date_obj,
                    passengers=passengers,
                    cabin_class=cabin_class
                )
                
                # Formatage des offres pour l'affichage
                formatted_offers = []
                for offer in search_results.get('offers', []):
                    formatted_offer = duffel_service.format_offer_for_frontend(offer)
                    if formatted_offer:
                        formatted_offers.append(formatted_offer)
                
                context = {
                    'title': 'Résultats de recherche',
                    'offers': formatted_offers,
                    'search_params': {
                        'origin': origin,
                        'destination': destination,
                        'departure_date': departure_date,
                        'return_date': return_date,
                        'passengers': passengers,
                        'cabin_class': cabin_class
                    },
                    'total_offers': len(formatted_offers)
                }
                
                return render(request, "ModuleFlight/flight-list.html", context)
                
                # CODE STATIQUE COMMENTÉ POUR LE MOMENT
                # logger.info("Utilisation des données statiques pour le test")
                # search_results = duffel_service.test_with_static_data(
                #     origin=origin,
                #     destination=destination,
                #     departure_date=departure_date_obj,
                #     return_date=return_date_obj,
                #     passengers=passengers,
                #     cabin_class=cabin_class
                # )
                # 
                # # Formatage des offres pour l'affichage
                # formatted_offers = []
                # for offer in search_results.get('offers', []):
                #     formatted_offer = duffel_service.format_offer_for_frontend(offer)
                #     if formatted_offer:
                #         formatted_offer.append(formatted_offer)
                # 
                # context = {
                #     'title': 'Résultats de recherche (Test)',
                #     'offers': formatted_offers,
                #     'search_params': {
                #         'origin': origin,
                #         'destination': destination,
                #         'departure_date': departure_date,
                #         'return_date': return_date,
                #         'passengers': passengers,
                #         'cabin_class': cabin_class
                #     },
                #     'total_offers': len(formatted_offers),
                #     'test_mode': True
                # }
                # 
                # return render(request, "ModuleFlight/flight-list.html", context)
                
            except DuffelAPIError as e:
                logger.error(f"Erreur API Duffel: {str(e)}")
                
                context = {
                    'title': 'Erreur de recherche',
                    'error': f'Erreur API Duffel: {str(e)}',
                    'error_type': 'duffel_api'
                }
                return render(request, "ModuleFlight/flight-list.html", context)
                
        except Exception as e:
            logger.error(f"Erreur dans flight_results: {str(e)}")
            context = {
                'title': 'Résultats de recherche',
                'error': f'Erreur interne lors de la recherche: {str(e)}',
                'error_type': 'internal_error'
            }
            return render(request, "ModuleFlight/flight-list.html", context)
    
    def flight_detail(self, request, offer_id):
        """
        Affiche les détails complets d'une offre de vol
        """
        try:
            # Récupérer les détails complets de l'offre via l'API Duffel
            offer_details = duffel_service.get_offer_details(offer_id)
            
            if not offer_details:
                context = {
                    'title': 'Offre non trouvée',
                    'error': 'Impossible de récupérer les détails de cette offre'
                }
                return render(request, "ModuleFlight/flight-detail.html", context)
            
            # Formater l'offre pour l'affichage frontend
            formatted_offer = duffel_service.format_offer_for_frontend(offer_details)
            
            if not formatted_offer:
                context = {
                    'title': 'Erreur de formatage',
                    'error': 'Impossible de formater les données de cette offre'
                }
                return render(request, "ModuleFlight/flight-detail.html", context)
            
            context = {
                'title': f'Détail du vol - {formatted_offer["owner"]["name"]}',
                'offer': formatted_offer,
                'offer_raw': offer_details  # Données brutes pour debug si nécessaire
            }
            
            return render(request, "ModuleFlight/flight-detail.html", context)
            
        except DuffelAPIError as e:
            logger.error(f"Erreur API Duffel lors de la récupération des détails: {str(e)}")
            context = {
                'title': 'Erreur API',
                'error': f'Erreur API Duffel: {str(e)}'
            }
            return render(request, "ModuleFlight/flight-detail.html", context)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails: {str(e)}")
            context = {
                'title': 'Erreur interne',
                'error': f'Erreur interne: {str(e)}'
            }
            return render(request, "ModuleFlight/flight-detail.html", context)
    
    @csrf_exempt
    def book_flight(self, request):
        """Créer une réservation de vol - MÉTHODE DÉPRÉCIÉE"""
        # Cette méthode est dépréciée, utiliser ajax_create_booking à la place
        return JsonResponse({
            'success': False,
            'message': 'Méthode dépréciée. Utiliser la nouvelle API de réservation.'
        }, status=400)
    
    @csrf_exempt
    def pay_flight(self, request, booking_id):
        """Simuler le paiement d'une réservation"""
        try:
            if request.method != 'POST':
                return JsonResponse({
                    'success': False,
                    'message': 'Méthode non autorisée'
                }, status=405)
            
            # Récupération de la réservation
            booking = FlightBooking.get_booking_by_uuid_for_user(booking_id, request.user)
            if not booking:
                return JsonResponse({
                    'success': False,
                    'message': 'Réservation introuvable'
                }, status=404)
            
            # Vérification du statut
            if booking.payment_status == 'PAID':
                return JsonResponse({
                    'success': False,
                    'message': 'Cette réservation est déjà payée'
                }, status=400)
            
            if booking.status == FlightBooking.STATUS_CANCELLED:
                return JsonResponse({
                    'success': False,
                    'message': 'Impossible de payer une réservation annulée'
                }, status=400)
            
            # Simulation du paiement (toujours réussi)
            with transaction.atomic():
                booking.mark_paid(updated_by=request.user)
                
                logger.info(f"Paiement simulé pour la réservation: {booking.booking_reference}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Paiement effectué avec succès',
                    'data': {
                        'booking_reference': booking.booking_reference,
                        'status': booking.status,
                        'payment_status': booking.payment_status,
                        'total_paid': float(booking.get_total_with_commission())
                    }
                })
                
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Erreur dans pay_flight: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Erreur interne lors du paiement'
            }, status=500)
    
    @csrf_exempt
    def cancel_booking(self, request):
        """Annuler une réservation"""
        try:
            if request.method != 'POST':
                return JsonResponse({
                    'success': False,
                    'message': 'Méthode non autorisée'
                }, status=405)
            
            # Récupération des données
            try:
                data = json.loads(request.body)
                booking_id = data.get('booking_id')
            except (json.JSONDecodeError, KeyError):
                return JsonResponse({
                    'success': False,
                    'message': 'Données invalides'
                }, status=400)
            
            if not booking_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de réservation manquant'
                }, status=400)
            
            # Récupération de la réservation
            booking = FlightBooking.get_booking_by_uuid_for_user(booking_id, request.user)
            if not booking:
                return JsonResponse({
                    'success': False,
                    'message': 'Réservation introuvable'
                }, status=404)
            
            # Vérification si l'annulation est possible
            if not booking.is_cancellable():
                return JsonResponse({
                    'success': False,
                    'message': 'Cette réservation ne peut pas être annulée'
                }, status=400)
            
            # Annulation
            with transaction.atomic():
                booking.cancel_booking(updated_by=request.user)
                
                logger.info(f"Réservation annulée: {booking.booking_reference}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Réservation annulée avec succès',
                    'data': {
                        'booking_reference': booking.booking_reference,
                        'status': booking.status
                    }
                })
                
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Erreur dans cancel_booking: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Erreur interne lors de l\'annulation'
            }, status=500)
    
    # ===== MÉTHODES AJAX AVEC OPÉRATIONS =====
    
    def ajax_search_flights(self, request):
        """Recherche de vols via AJAX"""
        try:
            # Récupération des paramètres de recherche
            search_params = {
                'origin': request.POST.get('origin', '').upper(),
                'destination': request.POST.get('destination', '').upper(),
                'departure_date': request.POST.get('departure_date'),
                'return_date': request.POST.get('return_date'),
                'passengers': request.POST.get('passengers', '1'),
                'cabin_class': request.POST.get('cabin_class', 'economy')
            }
            
            # Validation côté serveur
            if not search_params['origin'] or not search_params['destination'] or not search_params['departure_date']:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Veuillez remplir tous les champs obligatoires'
                })
            
            # Construction de l'URL de redirection
            from urllib.parse import urlencode
            query_params = {k: v for k, v in search_params.items() if v}
            redirect_url = f"/flights/results/?{urlencode(query_params)}"
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Recherche en cours...',
                'redirect_url': redirect_url
            })
            
        except Exception as e:
            logger.error(f"Erreur dans ajax_search_flights: {str(e)}")
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Erreur lors de la recherche'
            })
    
    def ajax_get_agencies(self, request):
        """Récupère la liste des agences disponibles"""
        try:
            agencies = TravelAgency.get_agencies_for_user(request.user)
            agencies_data = []
            
            for agency in agencies:
                agencies_data.append({
                    'uuid': str(agency.uuid),
                    'id': agency.id,  # Pour rétrocompatibilité
                    'name': agency.name,
                    'city': agency.city,
                    'country': agency.country
                })
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Agences chargées',
                'agencies': agencies_data
            })
            
        except Exception as e:
            logger.error(f"Erreur dans ajax_get_agencies: {str(e)}")
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Erreur lors du chargement des agences'
            })
    
    def ajax_create_booking(self, request):
        """
        Création d'une réservation via AJAX
        """
        try:
            if request.method != 'POST':
                return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

            # Récupération des données JSON
            data = json.loads(request.body)
            offer_id = data.get('offer_id')
            passengers = data.get('passengers', [])
            total_amount = data.get('total_amount')
            total_currency = data.get('total_currency')

            if not offer_id or not passengers:
                return JsonResponse({'error': 'Données manquantes'}, status=400)

            # Validation des données des passagers
            for passenger in passengers:
                required_fields = ['type', 'title', 'given_name', 'family_name', 'gender', 'date_of_birth', 'nationality']
                for field in required_fields:
                    if not passenger.get(field):
                        return JsonResponse({'error': f'Champ manquant: {field}'}, status=400)

            # Création de la réservation
            try:
                with transaction.atomic():
                    # Récupération de l'agence par défaut
                    agency = TravelAgency.get_default_agency()
                    if not agency:
                        return JsonResponse({'error': 'Aucune agence de voyage disponible'}, status=500)
                    
                    # Récupération du profil client
                    try:
                        client_profile = ClientProfile.objects.get(user=request.user)
                    except ClientProfile.DoesNotExist:
                        return JsonResponse({'error': 'Profil client non trouvé'}, status=400)
                    
                    # Récupération du marchand par défaut
                    from ModuleProfils.models import MerchantProfile
                    try:
                        default_merchant = MerchantProfile.objects.filter(is_active=True).first()
                        if not default_merchant:
                            return JsonResponse({'error': 'Aucun marchand disponible'}, status=400)
                    except Exception as e:
                        logger.error(f"Erreur lors de la récupération du marchand par défaut: {e}")
                        return JsonResponse({'error': 'Erreur lors de la récupération du marchand'}, status=400)
                    
                    # Création du FlightBooking
                    # Extraction des informations de vol depuis les données Duffel
                    origin = "N/A"  # Valeur par défaut
                    destination = "N/A"  # Valeur par défaut
                    departure_date = datetime.now()  # Valeur par défaut
                    
                    # Si nous avons des données Duffel, essayons d'extraire les vraies informations
                    if 'duffel_data' in locals() and data:
                        # Essayer d'extraire depuis les données Duffel
                        try:
                            # Les données peuvent être dans différents formats selon l'API
                            if 'slices' in data and data['slices']:
                                first_slice = data['slices'][0]
                                if 'segments' in first_slice and first_slice['segments']:
                                    first_segment = first_slice['segments'][0]
                                    origin = first_segment.get('origin', {}).get('iata_code', 'N/A')
                                    destination = first_segment.get('destination', {}).get('iata_code', 'N/A')
                                    if 'departing_at' in first_segment:
                                        departure_date = datetime.fromisoformat(first_segment['departing_at'].replace('Z', '+00:00'))
                        except Exception as e:
                            logger.warning(f"Impossible d'extraire les données de vol depuis Duffel: {e}")
                    
                    booking = FlightBooking.objects.create(
                        client=client_profile,
                        agency=agency,
                        merchant=default_merchant,
                        duffel_offer_id=offer_id,
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date,
                        passenger_count=len(passengers),
                        status=FlightBooking.STATUS_PENDING,
                        payment_status=FlightBooking.PAYMENT_UNPAID,
                        price=Decimal(total_amount) if total_amount else Decimal('0.00'),
                        currency=total_currency or 'EUR',
                        create_by=request.user,
                        update_by=request.user
                    )

                    # Création des passagers
                    for passenger_data in passengers:
                        Passenger.objects.create(
                            booking=booking,
                            type=passenger_data['type'],
                            title=passenger_data['title'],
                            given_name=passenger_data['given_name'],
                            family_name=passenger_data['family_name'],
                            gender=passenger_data['gender'],
                            date_of_birth=datetime.strptime(passenger_data['date_of_birth'], '%Y-%m-%d').date(),
                            nationality=passenger_data['nationality'],
                            country_code=passenger_data.get('country_code'),
                            create_by=request.user,
                            update_by=request.user
                        )

                    # Création des détails de réservation
                    FlightBookingDetail.objects.create(
                        booking=booking,
                        duffel_data=data,
                        create_by=request.user,
                        update_by=request.user
                    )

                logger.info(f"Réservation créée avec succès: {booking.uuid}")
                
                return JsonResponse({
                    'resultat': 'SUCCESS',
                    'message': 'Réservation créée avec succès',
                    'redirect_url': f'/flights/pay/{booking.uuid}/'
                })

            except Exception as e:
                logger.error(f"Erreur lors de la création de la réservation: {str(e)}")
                return JsonResponse({'error': f'Erreur lors de la création: {str(e)}'}, status=500)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Données JSON invalides'}, status=400)
        except Exception as e:
            logger.error(f"Erreur dans ajax_create_booking: {str(e)}")
            return JsonResponse({'error': 'Erreur interne'}, status=500)

    def ajax_book(self, request):
        """
        Méthode de réservation principale (alias pour ajax_create_booking)
        """
        return self.ajax_create_booking(request)

    def ajax_pay_booking(self, request, booking_id):
        """Paiement d'une réservation via AJAX"""
        try:
            booking = FlightBooking.get_booking_by_uuid_for_user(booking_id, request.user)
            if not booking:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Réservation introuvable'
                })
            
            # Vérifications
            if booking.payment_status == FlightBooking.PAYMENT_PAID:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Cette réservation est déjà payée'
                })
            
            if booking.status == FlightBooking.STATUS_CANCELLED:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Impossible de payer une réservation annulée'
                })
            
            # Traitement du paiement (fictif)
            booking.mark_paid(updated_by=request.user)
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Paiement traité avec succès',
                'data': {
                    'booking_reference': booking.booking_reference,
                    'status': booking.get_status_display(),
                    'total_paid': str(booking.get_total_with_commission()),
                    'currency': booking.currency
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur dans ajax_pay_booking: {str(e)}")
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Erreur lors du traitement du paiement'
            })
    
    def ajax_cancel_booking(self, request):
        """Annulation d'une réservation via AJAX"""
        try:
            booking_id = request.POST.get('booking_id')
            if not booking_id:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'ID de réservation manquant'
                })
            
            booking = FlightBooking.get_booking_by_uuid_for_user(booking_id, request.user)
            if not booking:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Réservation introuvable'
                })
            
            # Vérification si l'annulation est possible
            if not booking.is_cancellable():
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Cette réservation ne peut pas être annulée'
                })
            
            # Annulation de la réservation
            booking.cancel_booking(updated_by=request.user)
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Réservation annulée avec succès',
                'data': {
                    'booking_reference': booking.booking_reference,
                    'status': booking.get_status_display()
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur dans ajax_cancel_booking: {str(e)}")
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Erreur lors de l\'annulation'
            })
    
    def ajax_get_booking_details(self, request):
        """Récupère les détails d'une réservation via AJAX"""
        try:
            booking_id = request.POST.get('booking_id')
            if not booking_id:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'ID de réservation manquant'
                })
            
            booking = FlightBooking.get_booking_by_uuid_for_user(booking_id, request.user)
            if not booking:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Réservation introuvable'
                })
            
            booking_data = {
                'booking_reference': booking.booking_reference,
                'status': booking.get_status_display(),
                'payment_status': booking.get_payment_status_display(),
                'origin': booking.origin,
                'destination': booking.destination,
                'departure_date': booking.departure_date.isoformat() if booking.departure_date else None,
                'passenger_data': booking.passenger_data,
                'price': str(booking.price),
                'currency': booking.currency,
                'commission_amount': str(booking.calculate_commission()),
                'total_with_commission': str(booking.get_total_with_commission())
            }
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Détails récupérés',
                'booking': booking_data
            })
            
        except Exception as e:
            logger.error(f"Erreur dans ajax_get_booking_details: {str(e)}")
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Erreur lors de la récupération des détails'
            })