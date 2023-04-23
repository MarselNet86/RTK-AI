import psycopg2
from sniper_bot import get_wall_posts, get_group_info, translate_to_english, \
    get_extract, translate_to_russia, get_title
import requests
from config import token, admin_id
from openpyxl import Workbook
from config import token
import os


class Database:
    def __init__(self, host, user, password, database, port):
        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        self.connection.autocommit = True
    
    def get_version(self):
        """Получить версию СУБД PostgreSQL"""
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            print(f'Server version: {cursor.fetchone()[0]}')

    def get_groups(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT group_link FROM providers"
            )
            groups = cursor.fetchall()
        return groups


    def standart_mailing(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users")
            user_ids = cursor.fetchall()
    
            cursor.execute("SELECT COUNT(user_id) FROM users")
            user_count = cursor.fetchone()[0]
        return user_ids, user_count
    
    
    def provider_mailing(self, post_id):
        """Рассылка по сгенирированному посту ИИ"""
        with self.connection.cursor() as cursor:
            # Получаем id провайдера по номеру поста
            cursor.execute("SELECT providers.id FROM providers JOIN news ON providers.group_link = news.group_screen_name WHERE news.post_id = %s", [post_id])
            provider_id = cursor.fetchone()[0]
    
            # Получаем user_id и подписки на провайдеров
            cursor.execute("SELECT users.user_id, subscribed_providers.subscriptions FROM users JOIN subscribed_providers ON users.id = subscribed_providers.fk_id WHERE %s = ANY(subscribed_providers.subscriptions)", [provider_id])
            user_ids = cursor.fetchall()
    
            cursor.execute("SELECT COUNT(*) FROM users JOIN subscribed_providers ON users.id = subscribed_providers.fk_id WHERE %s = ANY(subscribed_providers.subscriptions)", [provider_id])
            subscription_count = cursor.fetchone()[0]
    
        return user_ids, subscription_count
    
    def export_to_excel(self, user_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users"
            )
    
            # Создание нового Excel-файла и листа в нем
            workbook = Workbook()
            worksheet = workbook.active
    
            # Запись заголовков столбцов в первую строку Excel-файла
            worksheet.append(["id", "user_id", "referrer_id", "user_name", "user_phone", "registration_date"])
    
            # Запись данных из запроса в Excel-файл
            for row in cursor.fetchall():
                worksheet.append(row)
    
            # Сохраняем Excel документ в файл
            workbook.save("users.xlsx")
    
            # Отправка файла пользователю через Telegram бота
            with open("users.xlsx", "rb") as file:
                 file_data = file.read()
    
                 text = '🔖Данные из таблицы users'
    
                 form_data = {
                    'document': ('users.xlsx', file_data)
                 }
                 url = f'https://api.telegram.org/bot{token}/sendDocument?caption={text}'
                 requests.post(url, data={'chat_id': user_id}, files=form_data)
    
            # Удаление Excel-файла
            os.remove("users.xlsx")
    
    def get_provider_statistics(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT providers.name, COUNT(subscribed_providers.subscriptions) AS subscription_count FROM providers LEFT JOIN subscribed_providers ON providers.id = ANY(subscribed_providers.subscriptions) GROUP BY providers.id ORDER BY providers.name")
            result = cursor.fetchall()
        return result
        
    
    def get_bot_statistics(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(id) FROM users")
            result = cursor.fetchone()[0]
        return result
        
    
    async def sniper_bot(self, group):
        post = get_wall_posts(group)
    
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT id FROM news WHERE post_id = %s)", [post[0]]
            )
            result = cursor.fetchone()[0]
        
        if result is False:
            group_info = get_group_info(group)
            
            post[2].replace("\n", "")
            english_text = translate_to_english(post)
            edit_text = get_extract(english_text)
    
            russian_text = translate_to_russia(edit_text)
            title = get_title(russian_text)
    
            with self.connection.cursor() as cursor:
                cursor.execute("INSERT INTO news (group_id, group_name, group_screen_name, title, post_id, stock_post, ai_post, media, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                    (group_info[0], group_info[1], group_info[2], title, post[0], post[2], russian_text, post[1], post[3]))
            
            text = f'Обнаружен новый пост: {post[0]}'
            for admin in admin_id:
                requests.post(
                    f'https://api.telegram.org/bot{token}/sendMessage?chat_id={admin}&parse_mode=html&text={text}')
                
    
    def get_analogy(self, post_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT stock_post FROM news WHERE post_id = %s", [post_id])
            stock_post = cursor.fetchone()[0]
    
            english_text = translate_to_english(stock_post)
            edit_text = get_extract(english_text)
    
            russian_text = translate_to_russia(edit_text)
            title = get_title(russian_text)
    
            cursor.execute("UPDATE news SET title = %s, ai_post = %s WHERE post_id = %s", [title, russian_text, post_id])
    
            cursor.execute("SELECT title, ai_post FROM news WHERE post_id = %s", [post_id])
            edited_post = cursor.fetchall()
            return edited_post
    
    
    def get_post_id(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT post_id FROM news WHERE status = 'waiting'"
            )
    
            news = cursor.fetchall()
            return news
        
    def edit_status_post(self, status, post_id):
        with self.connection.cursor() as cursor:
            if status == 'post_confirm':
                cursor.execute("UPDATE news SET status = 'confirmed' WHERE post_id = %s", [post_id])
            else:
                cursor.execute("UPDATE news SET status = 'cancelled' WHERE post_id = %s", [post_id])
    
    def get_post(self, post_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT group_id, group_name, title, post_id, ai_post, date FROM news WHERE post_id = %s", [post_id]
            )
    
            post = cursor.fetchall()[0]
        return post
    
    
    def get_news(self, user_id):
        """Получаем все новости, а также новости на которые подписан юзер"""
        with self.connection.cursor() as cursor:
        
            cursor.execute(
                "SELECT id FROM users WHERE user_id = %s", [user_id]
            )
            fk_id = cursor.fetchone()[0]
    
            cursor.execute(
                "SELECT subscriptions FROM subscribed_providers WHERE fk_id = %s", [fk_id]
            )
            subscribed_news = cursor.fetchall()[0]
    
            cursor.execute(
                "SELECT id, name FROM providers"
            )
    
            providers = cursor.fetchall()
    
            return providers, subscribed_news
        
    def get_sub_news(self, user_id):
        """Получаем новости на которые подписан юзер"""
        with self.connection.cursor() as cursor:
        
            cursor.execute(
                    "SELECT id FROM users WHERE user_id = %s", [user_id]
                )
            fk_id = cursor.fetchone()[0]
            
            cursor.execute(
                "SELECT subscriptions FROM subscribed_providers WHERE fk_id = %s", [fk_id]
            )
    
            subscriptions = cursor.fetchall()[0]
    
            if subscriptions[0]:
            
                query = "SELECT id, name FROM providers WHERE id IN %s;"
                cursor.execute(query, (tuple(subscriptions[0]),))
                subscriptions = cursor.fetchall()
                return subscriptions
        
            else:
                return None
    
        
    def get_provider_name(self, provider_id, user_id):
        """Получаем имя провайдера по id"""
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, name FROM providers WHERE id = %s", [provider_id]
            )
    
            provider_name = cursor.fetchall()[0]
    
            cursor.execute(
                    "SELECT id FROM users WHERE user_id = %s", [user_id]
                )
            fk_id = cursor.fetchone()[0]
    
            cursor.execute(
                "SELECT subscriptions FROM subscribed_providers WHERE fk_id = %s", [fk_id]
            )
            subscribed_news = cursor.fetchall()[0]
            return provider_name, subscribed_news
    
    def check_registration(self, user_id):
        """Проверка на наличие регистрации пользователя"""
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id FROM users WHERE user_id = %s", [user_id]
            )
    
            reg_status = cursor.fetchone()
            return reg_status
    
    def register_user(self, user_id, user_name, user_phone, referrer_id=None):
        """Регестрируем и заносим данные пользователя в БД"""
        with self.connection.cursor() as cursor:
            if referrer_id:
                if referrer_id != user_id:
                    cursor.execute(
                        "INSERT INTO users (user_id, user_name, user_phone, referrer_id) VALUES (%s, %s, %s, %s)", 
                        (user_id,  user_name, user_phone, referrer_id[0])
                    )
            else:
                cursor.execute(
                    "INSERT INTO users (user_id, user_name, user_phone) VALUES (%s, %s, %s)", 
                    (user_id, user_name, user_phone))
               
    
    
            cursor.execute(
                "SELECT id FROM users WHERE user_id = %s", [user_id]
            )
    
            fk_id = cursor.fetchone()[0]
    
            cursor.execute(
                "INSERT INTO subscribed_providers (fk_id) VALUES (%s)", 
                [fk_id]
            )
    
    def user_exists(self, user_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(id) FROM users WHERE referrer_id = %s", [user_id])
            result = cursor.fetchone()[0]
        return result
    
    def add_sub(self, call_data, user_id, provider_name):
        """Добавляем провайдеров в бд на которые хочет подписаться юзер"""
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM providers WHERE name = %s", [provider_name]
            )
            provider_id = cursor.fetchone()[0]
            cursor.execute(
                "SELECT id FROM users WHERE user_id = %s", [user_id]
            )
            fk_id = cursor.fetchone()[0]
            cursor.execute(
                "SELECT subscriptions FROM subscribed_providers WHERE fk_id = %s", [fk_id]
            )
        
            subscriptions = cursor.fetchall()[0]
    
            if subscriptions is None:
                subscriptions = []
    
            # Пользователь нажал на кнопку "Все новости"
            if 'subscribe' in call_data:
                # Проверяем, есть ли уже провайдер в столбце all_news
                if not provider_id in subscriptions:
                    # Добавляем провайдер в столбец all_news
                    cursor.execute("UPDATE subscribed_providers SET subscriptions = array_append(subscriptions, %s) WHERE fk_id = %s", [provider_id, fk_id])
    
            if 'unsubscribe' in call_data:
                if provider_id in subscriptions[0]:
                    cursor.execute("UPDATE subscribed_providers SET subscriptions = array_remove(subscriptions, %s) WHERE fk_id = %s", [provider_id, fk_id])
    
