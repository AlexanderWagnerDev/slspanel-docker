from django.urls import path
from . import views

app_name = "streams"

urlpatterns = [
    path('', views.index, name='index'),
    path('sls-stats/<str:player_key>/', views.sls_stats, name='sls_stats'),
    path('api/streams-status/', views.streams_status_json, name='streams_status_json'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('create-stream/', views.create_stream, name='create_stream'),
    path('add-player/', views.add_player, name='add_player'),
    path('delete-stream/<str:publisher_key>/', views.delete_stream, name='delete_stream'),
    path('delete-player/<str:player_key>/', views.delete_player, name='delete_player'),
    path('stats/<str:player_key>/', views.sls_stats, name='sls_stats'),
]