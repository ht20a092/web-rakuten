from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.mail import send_mail
from myapp.models import FavoriteItem
from myapp.views import RAKUTEN_APP_ID, LINE_NOTIFY_TOKEN
import requests

def check_favorite_items_price():
    favorite_items = FavoriteItem.objects.all()

    for favorite_item in favorite_items:
        url = f'https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706?format=json&itemCode={favorite_item.item_id}&applicationId={RAKUTEN_APP_ID}'
        response = requests.get(url)
        data = response.json()
        current_price = data['Items'][0]['Item']['itemPrice']

        if current_price < favorite_item.last_checked_price:
            notify = LineNotify(LINE_NOTIFY_TOKEN)
            message = f'【Price Drop】\n{favorite_item.item_name}\nOld Price: {favorite_item.last_checked_price}円\nNew Price: {current_price}円'
            notify.send_message(message)
            favorite_item.last_checked_price = current_price
            favorite_item.save()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_favorite_items_price, 'interval', hours=1)
    scheduler.start()

start_scheduler()