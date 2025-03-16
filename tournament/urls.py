from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TournamentMatchViewSet, TournamentPlayerViewSet, TournamentViewSet
from . import views
router = DefaultRouter()
router.register(r'tournament', TournamentViewSet)
router.register(r'tournament_player', TournamentPlayerViewSet)
router.register(r'tournament_match', TournamentMatchViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('generate-bracket', views.TournamentViewSet.generate_bracket, name='generate-bracket'),
]
