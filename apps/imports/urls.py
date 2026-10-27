from django.urls import path
from . import views

app_name = 'imports'

urlpatterns = [
    path('upload/', views.upload_csv, name='upload_csv'),
    path('summary/<uuid:pk>/', views.import_summary, name='import_summary'),
]