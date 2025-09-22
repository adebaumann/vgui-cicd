from django.urls import path
from . import views

urlpatterns = [
    path('', views.stichwort_list, name='stichworte_list'),
    path('<str:stichwort>/',views.stichwort_detail, name="stichwort_detail")
]
