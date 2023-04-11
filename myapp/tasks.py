from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.mail import send_mail
from myapp.models import FavoriteProduct
from myapp.views import RAKUTEN_APP_ID, YAHOO_APP_ID, search_products_on_rakuten, search_products_on_yahoo
import requests

def check_favorite_products_price():
    favorite_products = FavoriteProduct.objects.all()

    for favorite_product in favorite_products:
        if favorite_product.platform == 'rakuten':
            product = search_products_on_rakuten(item_code=favorite_product.product_id)
        elif favorite_product.platform == 'yahoo':
            product = search_products_on_yahoo(item_code=favorite_product.product_id)

        if product is not None:
            current_price = product['itemPrice']

            if current_price < favorite_product.price:
                # ここに通知を送る処理を実装してください
                favorite_product.price = current_price
                favorite_product.save()
        else:
            print(f"Product with id {favorite_product.product_id} not found.")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_favorite_products_price, 'interval', hours=1)
    scheduler.start()

start_scheduler()
