import requests
from django.conf import settings
from django.core.mail import send_mail
from apscheduler.schedulers.background import BackgroundScheduler
from myapp.models import Product, UserProfile

def check_price():
    users = UserProfile.objects.all()
    for user in users:
        favorite_products = user.favorite_products.all()
        for product in favorite_products:
            if product.platform == "rakuten":
                item = search_products_on_rakuten(item_code=product.product_id)
            else:
                item = search_products_on_yahoo(item_code=product.product_id)

            if item and item["itemPrice"] < product.price:
                message = f"{product.name}の価格が下がりました！\n新しい価格: {item['itemPrice']}円\n詳細ページ: {product.url}"
                send_line_notify(message)
                print(message)
                product.price = item["itemPrice"]
                product.save()

scheduler = BackgroundScheduler()
scheduler.add_job(check_price, "interval", hours=1)
scheduler.start()
