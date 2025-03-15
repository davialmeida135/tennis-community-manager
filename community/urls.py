from .views import CommunityViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()
router.register(r'communities', CommunityViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('add_user', views.CommunityViewSet.add_user, name='add_user'),
    ]

