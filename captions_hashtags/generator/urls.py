from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('input/', views.input, name='input'),
    path('generate/', views.generate_captions, name='generate'),
    path('download/<str:filetype>/', views.download_export, name='download_export'),
]
