from django.urls import path
from . import views

urlpatterns = [
    path('', views.standard_list, name='standard_list'),
    path('unvollstaendig/', views.incomplete_vorgaben, name='incomplete_vorgaben'),
    path('meine-kommentare/', views.user_comments, name='user_comments'),
    path('<str:nummer>/', views.standard_detail, name='standard_detail'),
    path('<str:nummer>/history/<str:check_date>/', views.standard_detail),
    path('<str:nummer>/history/', views.standard_detail, {"check_date":"today"}, name='standard_history'),
    path('<str:nummer>/checkliste/', views.standard_checkliste, name='standard_checkliste'),
    path('<str:nummer>/json/', views.standard_json, name='standard_json'),
    path('comments/<int:vorgabe_id>/', views.get_vorgabe_comments, name='get_vorgabe_comments'),
    path('comments/<int:vorgabe_id>/add/', views.add_vorgabe_comment, name='add_vorgabe_comment'),
    path('comments/delete/<int:comment_id>/', views.delete_vorgabe_comment, name='delete_vorgabe_comment'),
]

