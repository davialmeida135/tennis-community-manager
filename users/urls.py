# filepath: d:\Github\tennis_community_manager\users\urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
# Remove: from . import views # No longer needed for login/logout

router = DefaultRouter()
# Register users endpoint for CRUD operations (create, list, retrieve, update, delete)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Keep custom actions if needed, e.g., communities, matches
    path('users/communities/', UserViewSet.as_view({'get': 'communities'}), name='user-communities'),
    path('users/matches/', UserViewSet.as_view({'get': 'matches'}), name='user-matches'),
    # REMOVE login and logout paths
    # path('users/login/', views.UserViewSet.as_view({'post': 'login'}), name='login'),
    # path('users/logout/', views.UserViewSet.as_view({'post': 'logout'}), name='logout'),
]