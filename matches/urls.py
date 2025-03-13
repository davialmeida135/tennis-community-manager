from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MatchViewSet, MatchMomentViewSet, MatchSetViewSet

router = DefaultRouter()
router.register(r'matches', MatchViewSet)
router.register(r'match-moments', MatchMomentViewSet)
router.register(r'match-sets', MatchSetViewSet)

urlpatterns = [
    path('', include(router.urls)),

]
# Debug URL patterns
#print(f"Match URLs: {router.urls}")