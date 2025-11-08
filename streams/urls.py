from django.urls import path
from . import views

app_name = "streams"

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('create-stream/', views.create_stream, name='create_stream'),
    path('add-player/', views.add_player, name='add_player'),
    path('delete-stream/<str:play_key>/', views.delete_stream, name='delete_stream'),
    path('delete-player/<str:play_key>/', views.delete_player, name='delete_player'),
]