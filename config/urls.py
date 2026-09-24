from django.contrib import admin
from django.urls import path
from floor_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_direct'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('validation/', views.process_validation_view, name='process_validation_default'),
    path('validation/<str:process_code>/', views.process_validation_view, name='process_validation'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/export-excel/', views.export_excel_view, name='export_excel'),
    path('settings/', views.settings_view, name='settings'),
    path('users/', views.users_view, name='users'),
    path('admin-control/set-stage/', views.admin_set_stage_view, name='admin_set_stage'),
    
    # API Endpoints
    path('api/demo-scenario/', views.api_get_demo_scenario, name='api_demo_scenario'),
    path('api/submit-process/', views.api_submit_process_result, name='api_submit_process'),
    path('api/generate-barcode/', views.api_generate_barcode, name='api_generate_barcode'),
    path('api/switch-operator/', views.api_switch_operator, name='api_switch_operator'),
    path('api/switch-user/', views.api_switch_user, name='api_switch_user'),
    path('api/admin-request-action/', views.api_admin_request_action, name='api_admin_request_action'),
]
