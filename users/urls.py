from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from . import views
router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('users/login/', views.UserViewSet.as_view({'post': 'login'}), name='login'),
    path('users/logout/', views.UserViewSet.as_view({'post': 'logout'}), name='logout'),
    path('users/communities/', views.UserViewSet.as_view({'get': 'communities'}), name='communities'),
]
