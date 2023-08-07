from django.urls import path
from . import views

app_name = "myapp"

urlpatterns = [
    path("", views.search_rakuten, name="search_rakuten"),
    path("search/rakuten/", views.search_rakuten, name="search_rakuten"),
    path("search/yahoo/", views.search_yahoo, name="search_yahoo"),
    path("favorites/", views.favorites, name="favorites"),
    path('add_favorite/<str:platform>/<str:product_id>/<path:product_name>/', views.add_favorite, name='add_favorite'),
    path("search/both/", views.search_both, name="search_both"),
    path('remove_favorite/<str:platform>/<str:product_id>/', views.remove_favorite, name='remove_favorite'),
    path('test_email/<str:platform>/<str:product_id>/<path:product_name>/', views.test_email, name='test_email'),
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path('logout/', views.logout_view, name='logout'),
]


