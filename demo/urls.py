from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("items/<int:item_id>/delete/", views.delete_item, name="delete_item"),
]
