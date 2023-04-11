from django.urls import path
from . import views

app_name = "myapp"

urlpatterns = [
    path("", views.search, name="index"),
    path("search/", views.search, name="search"),
    path("favorites/", views.favorites, name="favorites"),
    path("add_favorite/<str:product_id>/", views.add_favorite, name="add_favorite"),
    path('remove_favorite/<str:product_id>/', views.remove_favorite, name='remove_favorite'),
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path('logout/', views.logout_view, name='logout'),
]

