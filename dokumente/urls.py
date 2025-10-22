from django.urls import path
from . import views

urlpatterns = [
    path('', views.standard_list, name='standard_list'),
    path('<str:nummer>/', views.standard_detail, name='standard_detail'),
    path('<str:nummer>/history/<str:check_date>/', views.standard_detail),
    path('<str:nummer>/history/', views.standard_detail, {"check_date":"today"}, name='standard_history'),
    path('<str:nummer>/checkliste/', views.standard_checkliste, name='standard_checkliste')
]

