from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TournamentMatchViewSet, TournamentViewSet
router = DefaultRouter()
router.register(r'tournament', TournamentViewSet)
router.register(r'tournament_match', TournamentMatchViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
