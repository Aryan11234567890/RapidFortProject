from django.urls import path
from . import views

urlpatterns = [
    path('', views.homePage, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('upload/', views.upload, name='upload'),
    path('convert/<int:file_id>/', views.cvt, name='convert'),
    path('convert/<int:file_id>/<str:password>/', views.cvt, name='convert'),
    path('download/<int:file_id>/', views.download, name='download'),
    path('history/', views.history, name='history'),
]