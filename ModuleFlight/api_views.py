"""
API ViewSets DRF pour le module Flight
Expose les fonctionnalités via une API REST
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import datetime
import logging

from .models import TravelAgency, MerchantAgency, FlightBooking, FlightUserManager
from .serializers import (
    TravelAgencySerializer, 
    MerchantAgencySerializer, 
    FlightBookingSerializer,
    FlightBookingCreateSerializer,
    FlightSearchSerializer,
    FlightOfferSerializer
)
from .duffel_service import duffel_service, DuffelAPIError
from ModuleProfils.models import ClientProfile, MerchantProfile

logger = logging.getLogger(__name__)


class TravelAgencyViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des agences de voyage"""
    
    serializer_class = TravelAgencySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'
    
    def get_queryset(self):
        """Retourne les agences selon les permissions de l'utilisateur"""
        return TravelAgency.get_agencies_for_user(self.request.user)
    
    @action(detail=True, methods=['post'])
    def assign_merchant(self, request, pk=None):
        """Assigner un marchand à une agence"""
        try:
            agency = self.get_object()
            merchant_id = request.data.get('merchant_id')
            role = request.data.get('role', 'AGENT')
            is_responsible = request.data.get('is_responsible', False)
            
            if not merchant_id:
                return Response({
                    'success': False,
                    'message': 'ID du marchand requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            merchant = MerchantProfile.get_merchant_by_id(merchant_id)
            if not merchant:
                return Response({
                    'success': False,
                    'message': 'Marchand introuvable'
                }, status=status.HTTP_404_NOT_FOUND)
            
            assignment = MerchantAgency.assign_merchant_to_agency(
                merchant=merchant,
                agency=agency,
                role=role,
                is_responsible=is_responsible,
                created_by=request.user
            )
            
            serializer = MerchantAgencySerializer(assignment)
            return Response({
                'success': True,
                'message': 'Marchand assigné avec succès',
                'data': serializer.data
            })
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de l'assignation: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None):
        """Récupérer les réservations d'une agence"""
        try:
            agency = self.get_object()
            bookings = FlightBooking.get_bookings_by_agency(agency)
            
            # Pagination
            page = self.paginate_queryset(bookings)
            if page is not None:
                serializer = FlightBookingSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = FlightBookingSerializer(bookings, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des réservations: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération des réservations'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MerchantAgencyViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des affectations marchand-agence"""
    
    serializer_class = MerchantAgencySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'
    
    def get_queryset(self):
        """Retourne les affectations selon les permissions"""
        if FlightUserManager.user_is_merchant(self.request.user):
            # Un marchand ne voit que ses propres affectations
            return MerchantAgency.get_agencies_for_merchant(self.request.user)
        else:
            # Un admin peut voir toutes les affectations
            return MerchantAgency.get_all_active_assignments()
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Désactiver une affectation"""
        try:
            assignment = self.get_object()
            assignment.remove_assignment(updated_by=request.user)
            
            return Response({
                'success': True,
                'message': 'Affectation désactivée avec succès'
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la désactivation: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la désactivation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FlightBookingViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des réservations de vol"""
    
    serializer_class = FlightBookingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'
    
    def get_queryset(self):
        """Retourne les réservations selon l'utilisateur"""
        if FlightUserManager.user_is_client(self.request.user):
            # Un client ne voit que ses propres réservations
            return FlightBooking.get_bookings_by_client(self.request.user.clientprofile_profile)
        elif FlightUserManager.user_is_merchant(self.request.user):
            # Un marchand voit les réservations de ses agences
            return FlightBooking.get_bookings_by_merchant(self.request.user.merchantprofile_profile)
        else:
            # Admin voit tout
            return FlightBooking.get_all_bookings_ordered()
    
    def get_serializer_class(self):
        """Sélectionne le serializer selon l'action"""
        if self.action == 'create':
            return FlightBookingCreateSerializer
        return FlightBookingSerializer
    
    def create(self, request, *args, **kwargs):
        """Créer une nouvelle réservation via API"""
        try:
            # Vérifier que l'utilisateur est un client
            if not FlightUserManager.user_is_client(request.user):
                return Response({
                    'success': False,
                    'message': 'Seuls les clients peuvent créer des réservations'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Récupération des données validées
            duffel_offer_id = serializer.validated_data['duffel_offer_id']
            agency_uuid = serializer.validated_data['agency_uuid']
            passenger_data = serializer.validated_data['passenger_data']
            
            client = request.user.clientprofile
            
            # Récupération de l'agence
            agency = TravelAgency.get_agency_by_uuid(agency_uuid)
            if not agency:
                return Response({
                    'success': False,
                    'message': 'Agence introuvable'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Récupération du marchand responsable
            responsible_merchants = agency.get_responsible_merchants()
            if not responsible_merchants.exists():
                return Response({
                    'success': False,
                    'message': 'Aucun marchand responsable pour cette agence'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            merchant = responsible_merchants.first()
            
            # Récupération des détails de l'offre
            try:
                offer_details = duffel_service.get_offer(duffel_offer_id)
                formatted_offer = duffel_service.format_offer_for_frontend(offer_details)
                
                if not formatted_offer:
                    return Response({
                        'success': False,
                        'message': 'Offre invalide ou expirée'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except DuffelAPIError as e:
                return Response({
                    'success': False,
                    'message': f'Erreur API Duffel: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Création de la réservation
            flight_details = {
                'origin': formatted_offer['origin'],
                'destination': formatted_offer['destination'],
                'departure_date': datetime.fromisoformat(formatted_offer['departure_time'].replace('Z', '+00:00')),
                'return_date': None,
                'passenger_count': len(passenger_data) if isinstance(passenger_data, list) else 1,
                'price': formatted_offer['price'],
                'currency': formatted_offer['currency'],
            }
            
            with transaction.atomic():
                booking = FlightBooking.create_booking(
                    client=client,
                    agency=agency,
                    merchant=merchant,
                    duffel_offer_id=duffel_offer_id,
                    flight_details=flight_details,
                    passenger_data=passenger_data,
                    created_by=request.user
                )
                
                # Retourner les détails de la réservation
                response_serializer = FlightBookingSerializer(booking)
                return Response({
                    'success': True,
                    'message': 'Réservation créée avec succès',
                    'data': response_serializer.data
                }, status=status.HTTP_201_CREATED)
                
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de la création de réservation: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """Marquer une réservation comme payée"""
        try:
            booking = self.get_object()
            
            # Vérifier que l'utilisateur est le propriétaire
            if FlightUserManager.user_is_client(request.user):
                if booking.client != request.user.clientprofile_profile:
                    return Response({
                        'success': False,
                        'message': 'Non autorisé'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            with transaction.atomic():
                booking.mark_paid(updated_by=request.user)
                
                serializer = FlightBookingSerializer(booking)
                return Response({
                    'success': True,
                    'message': 'Paiement effectué avec succès',
                    'data': serializer.data
                })
                
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors du paiement: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Annuler une réservation"""
        try:
            booking = self.get_object()
            
            # Vérifier que l'utilisateur est le propriétaire
            if FlightUserManager.user_is_client(request.user):
                if booking.client != request.user.clientprofile_profile:
                    return Response({
                        'success': False,
                        'message': 'Non autorisé'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            if not booking.is_cancellable():
                return Response({
                    'success': False,
                    'message': 'Cette réservation ne peut pas être annulée'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                booking.cancel_booking(updated_by=request.user)
                
                serializer = FlightBookingSerializer(booking)
                return Response({
                    'success': True,
                    'message': 'Réservation annulée avec succès',
                    'data': serializer.data
                })
                
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """Récupérer les réservations de l'utilisateur connecté"""
        try:
            if FlightUserManager.user_is_client(request.user):
                bookings = FlightBooking.get_bookings_by_client(request.user.clientprofile_profile)
            elif FlightUserManager.user_is_merchant(request.user):
                bookings = FlightBooking.get_bookings_by_merchant(request.user.merchantprofile_profile)
            else:
                return Response({
                    'success': False,
                    'message': 'Type d\'utilisateur non pris en charge'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Pagination
            page = self.paginate_queryset(bookings)
            if page is not None:
                serializer = FlightBookingSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = FlightBookingSerializer(bookings, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des réservations: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FlightSearchAPIView(APIView):
    """API pour la recherche de vols"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Rechercher des vols via l'API Duffel"""
        try:
            serializer = FlightSearchSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Récupération des paramètres validés
            origin = serializer.validated_data['origin']
            destination = serializer.validated_data['destination']
            departure_date = serializer.validated_data['departure_date']
            return_date = serializer.validated_data.get('return_date')
            passengers = serializer.validated_data['passengers']
            cabin_class = serializer.validated_data['cabin_class']
            
            # Recherche via Duffel
            try:
                search_results = duffel_service.search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    passengers=passengers,
                    cabin_class=cabin_class
                )
                
                # Formatage des offres
                formatted_offers = []
                for offer in search_results.get('offers', []):
                    formatted_offer = duffel_service.format_offer_for_frontend(offer)
                    if formatted_offer:
                        formatted_offers.append(formatted_offer)
                
                return Response({
                    'success': True,
                    'data': {
                        'offers': formatted_offers,
                        'search_params': {
                            'origin': origin,
                            'destination': destination,
                            'departure_date': departure_date.isoformat(),
                            'return_date': return_date.isoformat() if return_date else None,
                            'passengers': passengers,
                            'cabin_class': cabin_class
                        },
                        'total_offers': len(formatted_offers)
                    }
                })
                
            except DuffelAPIError as e:
                logger.error(f"Erreur API Duffel: {str(e)}")
                return Response({
                    'success': False,
                    'message': f'Erreur lors de la recherche: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Erreur dans FlightSearchAPIView: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne lors de la recherche'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """Récupérer les détails d'une offre spécifique"""
        try:
            offer_id = request.query_params.get('offer_id')
            
            if not offer_id:
                return Response({
                    'success': False,
                    'message': 'ID d\'offre requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                offer_details = duffel_service.get_offer(offer_id)
                formatted_offer = duffel_service.format_offer_for_frontend(offer_details)
                
                if not formatted_offer:
                    return Response({
                        'success': False,
                        'message': 'Offre introuvable ou invalide'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                return Response({
                    'success': True,
                    'data': formatted_offer
                })
                
            except DuffelAPIError as e:
                return Response({
                    'success': False,
                    'message': f'Erreur lors de la récupération: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération d'offre: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
