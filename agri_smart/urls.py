from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from agri_app import views
from django.contrib.auth import views as auth_views

from agri_smart import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='agri_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('post-news/', views.post_news_view, name='post_news'),

    path('dashboard/ai-prediction/', views.ai_prediction_view, name='ai_prediction'),
    path('dashboard/rental/', views.rental_view, name='rental_service'),
    path('dashboard/sell-product/', views.sell_product_view, name='sell_product'),

    path('post-news/', views.post_news_view, name='post_news'),

    path('dashboard/', views.farmer_dashboard, name='dashboard'),

    path('market/', views.market_list_view, name='market_list'),
    path('market/review/<int:product_id>/', views.add_review_view, name='add_review'),
    path('market/', views.market_list_view, name='market_list'),
    path('market/sell/', views.sell_product_view, name='sell_product'),
    path('market/buy/<int:product_id>/', views.buy_product_view, name='buy_product'),
    path('market/delete/<int:product_id>/', views.delete_product_view, name='delete_product'),

    path('rental/', views.rental_view, name='rental_list'),
    path('rental/toggle/<int:equipment_id>/', views.toggle_equipment_status, name='toggle_equipment'),
    path('rental/delete/<int:equipment_id>/', views.delete_equipment, name='delete_equipment'),

    path('rental/add/', views.add_equipment_view, name='add_equipment'),
    path('rental/rent/<int:equipment_id>/', views.rent_equipment_view, name='rent_equipment'),
    path('rental/review/<int:equipment_id>/', views.add_equipment_review_view, name='add_equipment_review'),
    path('dashboard/notifications/', views.notifications_view, name='notifications'),

    path('buyer-dashboard/', views.buyer_dashboard, name='buyer_dashboard'),

    path('news/', views.news_list_view, name='news_list'),
    path('news/edit/<int:news_id>/', views.edit_news_view, name='edit_news'),
    path('news/delete/<int:news_id>/', views.delete_news_view, name='delete_news'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='agri_app/password_reset.html'),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='agri_app/password_reset_done.html'),
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='agri_app/password_reset_confirm.html'),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='agri_app/password_reset_complete.html'),
         name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

