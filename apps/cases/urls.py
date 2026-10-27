from django.urls import path
from . import views

app_name = 'cases'

urlpatterns = [
    # Case List & Detail
    path('', views.case_list, name='case_list'),
    path('<int:pk>/', views.case_detail, name='case_detail'),
    
    # Workflow Actions
    path('<int:pk>/assess/', views.submit_assessment, name='submit_assessment'),
    path('<int:pk>/approve/', views.approve_case, name='approve_case'),
    path('<int:pk>/submit/', views.record_submission, name='record_submission'),
]