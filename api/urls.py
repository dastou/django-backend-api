from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemViewSet, read_items, write_item

router = DefaultRouter()
router.register(r'items', ItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Ajout des endpoints spécifiques
    path('read/', read_items, name='read_items'),
    path('write/', write_item, name='write_item'),
]