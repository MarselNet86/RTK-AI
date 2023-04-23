import asyncio
from main import bot, dp, connection
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from keyboards.admin import admin_keyboard, btn_edit_text, btn_mailing, btn_photo_mailing
from config import host, user, password, db_name, port
from keyboards.user import markup, btn_stock, \
      btn_subscribe, btn_unsubscribe, request_phone, \
     my_btn_subscribe, my_btn_unsubscribe, btn_ref
from aiogram.utils.exceptions import MessageNotModified
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from contextlib import suppress
from config import admin_id, bot_nickname
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import BotBlocked
import re


class Post(StatesGroup):
    waiting_contact = State()
    waiting_text = State()
    waiting_photo = State()

@dp.message_handler(commands=['admin'])
async def admin_panel(message: Message):
    if message.chat.id in admin_id:
        await message.answer('Открыта админ панель.', reply_markup=admin_keyboard)
        connection.get_version()

@dp.message_handler(lambda message: message.text in ['Рассылка', 'Новости', 'Выгрузка', 'Статистика'])
async def process_news_command(message: Message, state: FSMContext):
    if message.chat.id in admin_id:
        if message.text == 'Новости':   
            global post_news
            post_news = InlineKeyboardMarkup()
            rows = connection.get_post_id()
            for row in rows:
                button = InlineKeyboardButton(text='📬 #' + str(row[0]), callback_data="message_" + str(row[0]))
                post_news.add(button)

            await message.answer('Новости доступные для публикации: ', reply_markup=post_news)
        
        elif message.text == 'Рассылка':
            await state.finish()
            await Post.waiting_text.set()
            await message.answer('Введите текст сообщения для рассылки 👇')

        elif message.text == 'Выгрузка':
            connection.export_to_excel(message.from_user.id)


        elif message.text == 'Статистика':
            provider_statics = connection.get_provider_statistics()
            bot_statics = connection.get_bot_statistics()

            # Создаем строку для отправки в бота
            statics_str = '\n'.join([f'{provider[0]} - {provider[1]}' for provider in provider_statics])

            await message.answer(f'Статистика подписок по провайдерам: \n\n{statics_str}'
                                 f'\n\nОбщее кол-во пользователей в боте: {bot_statics}')

@dp.message_handler(state=Post.waiting_text)
async def get_text_for_post(message: Message, state: FSMContext):
    async with state.proxy() as data: # Устанавливаем состояние ожидания
    
        data['waiting_text'] = message.text
        await message.answer(f"Ваш пост:\n\n{data['waiting_text']}", reply_markup=btn_mailing)
        await state.reset_state(with_data=False)

@dp.callback_query_handler(lambda call: call.data in ['add_picture', 'mail_confirm', 'mail_cancel'])
async def standart_mailing_settings(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with state.proxy() as data: 
        message_text = data['waiting_text']

        with suppress(MessageNotModified):
            if call.data == 'add_picture':
                await call.message.edit_text('📲Прекрепите картинку')
                await Post.waiting_photo.set()

            if call.data == 'mail_confirm':
                await bot.answer_callback_query(call.id)
                await call.message.delete()

                user_ids, count_before = connection.standart_mailing()
                count_after = 0
                for user_id in user_ids:
                    try:
                        await bot.send_message(user_id[0], message_text) 
                        count_after += 1
                    except BotBlocked:
                        pass

                    await asyncio.sleep(5)
                
                await call.message.answer(f'Сообщение было успешно отправлено: {str(count_after)} из {str(count_before)} пользователей')
                

            elif call.data == 'mail_cancel':
                await call.message.edit_text('Рассылка отменена!')


@dp.message_handler(state=Post.waiting_photo, content_types=types.ContentType.PHOTO) # Принимаем состояние
async def set_mailing_photo(message: Message, state: FSMContext):
    async with state.proxy() as data: # Устанавливаем состояние ожидания
        data['waiting_photo'] = message.photo[-1].file_id
        await bot.send_photo(message.chat.id, photo=data['waiting_photo'], caption=data['waiting_text'], reply_markup=btn_photo_mailing)
        await state.reset_state(with_data=False)


@dp.callback_query_handler(lambda call: call.data in ['photo_confirm', 'photo_cancel'])
async def send_mailing_photo(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        message_text = data['waiting_text']
        message_photo = data['waiting_photo']
        with suppress(MessageNotModified):
            user_ids, count_before = connection.standart_mailing()
            count_after = 0
            if call.data == 'photo_confirm':
                await call.message.delete()
                for user_id in user_ids:
                    try:
                        if not user_id[0] in admin_id:
                            await bot.send_photo(user_id[0], photo=message_photo, caption=message_text)
                        count_after += 1
                    except BotBlocked:
                        pass

                    await asyncio.sleep(5)
                
                await call.message.answer(f'Сообщение было успешно отправлено: {str(count_after)} из {str(count_before)} пользователей')

            elif call.data == 'photo_cancel':
                await call.message.delete()
                await call.message.answer('Рассылка отменена!')

            await state.finish()

@dp.callback_query_handler(lambda call: 'message' in call.data)
async def news_of_providers(call: CallbackQuery):

    global post_id, group_id, values

    post_id = call.data.split('_')[1]
    values = connection.get_post(post_id)
    group_id = values[0]

    await call.message.edit_text('➖➖➖➖➖➖➖➖➖➖➖➖'
                                 f'\n📋Новый пост: #{values[3]}'
                                 f'\n💼Провайдер: {values[1]}'
                                 f'\n⏰Дата публикации: {values[5]}'
                                 '\n➖➖➖➖➖➖➖➖➖➖➖➖'
                                 f'\n\n📮{values[2]}'
                                 f'\n\n👉{values[4]}'
                                 f'\n\n🔗Ссылка на новость: https://vk.com/wall-{str(group_id)}_{str(post_id)}', reply_markup=btn_edit_text)
    

@dp.callback_query_handler(lambda call: call.data in ['analogy', 'post_confirm', 'post_cancel', 'back'])
async def news_settings(call: CallbackQuery):
    user_id = call.from_user.id
    with suppress(MessageNotModified):
        if call.data == 'analogy':
            await bot.answer_callback_query(call.id)
            await call.message.edit_text('➖➖➖➖➖➖➖➖➖➖➖➖'
                                 f'\n📋Пост id: #{values[3]}'
                                 f'\n💼Провайдер: {values[1]}'
                                 f'\n⏰Дата публикации: {values[5]}'
                                 '\n➖➖➖➖➖➖➖➖➖➖➖➖'
                                 f'\n\n⏳Ожидайте, мы составляем новый пост...')
            
            edited_post = connection.get_analogy(post_id)
            await call.message.edit_text('➖➖➖➖➖➖➖➖➖➖➖➖'
                                 f'\n📋Пост id: #{values[3]}'
                                 f'\n💼Провайдер: {values[1]}'
                                 f'\n⏰Дата публикации: {values[5]}'
                                 '\n➖➖➖➖➖➖➖➖➖➖➖➖'
                                 f'\n\n📮{edited_post[0][0]}'
                                 f'\n\n👉{edited_post[0][1]}'
                                 f'\n\n🔗Ссылка на новость: https://vk.com/wall-{str(group_id)}_{str(post_id)}', reply_markup=btn_edit_text)
            
        elif call.data == 'post_confirm':
            await bot.answer_callback_query(call.id)
            await call.message.edit_text('➖➖➖➖➖➖➖➖➖➖➖➖'
                                 f'\n📋Пост id: #{values[3]}'
                                 f'\n💼Провайдер: {values[1]}'
                                 f'\n⏰Дата публикации: {values[5]}'
                                 '\n➖➖➖➖➖➖➖➖➖➖➖➖'
                                 f'\n\n⏳Начинаем рассылку...')

            status_post = call.data
            connection.edit_status_post(status_post, post_id)
            user_ids, subscription_count = connection.provider_mailing(post_id)
            success_mailing = 0
            for user_id in user_ids:
                try:
                    if not user_id[0] in admin_id:
                        await bot.send_message(user_id[0], f'\n\n📮{values[2]}'
                                    f'\n\n👉{values[4]}'
                                    f'\n\n🔗Ссылка на новость: https://vk.com/wall-{str(group_id)}_{str(post_id)}') 
                    success_mailing += 1
                except BotBlocked:
                    pass
                await asyncio.sleep(5)

            await call.message.edit_text('➖➖➖➖➖➖➖➖➖➖➖➖'
                     f'\n📋Пост id: #{values[3]}'
                     f'\n💼Провайдер: {values[1]}'
                     f'\n⏰Дата публикации: {values[5]}'
                     '\n➖➖➖➖➖➖➖➖➖➖➖➖'
                     f'\n\n✅Сообщение было успешно отправлено: {str(success_mailing)} из {str(subscription_count)} пользователей')

        elif call.data == 'post_cancel':
            status_post = call.data
            connection.edit_status_post(status_post, values[3])
            await call.message.edit_text('Пост удален с рекомендации')

        elif call.data == 'back':
            await call.message.edit_text('Новости доступные для публикации: ', reply_markup=post_news)

@dp.message_handler(commands=['start', 'user'])
async def start(message: Message, state: FSMContext):
    async with state.proxy() as data: # Устанавливаем состояние ожидания
        data['user_contact'] = message.text
        user_id = message.chat.id
        is_reg = connection.check_registration(user_id)

        if is_reg is None:
            await message.answer('Привет, перед началом мне потребуется твой номер', reply_markup=request_phone)
            await Post.waiting_contact.set()

        else:
            await message.answer('👋 <b>Приветствую,</b> Вас в нашем агрегаторе провайдеров! Мы рады, что вы присоединились к нам :)', parse_mode='html', reply_markup=markup)
        

@dp.message_handler(state=Post.waiting_contact, content_types=['contact'])
async def handle_contact(message: Message, state: FSMContext):
    async with state.proxy() as data: # Устанавливаем состояние ожидания
        user_id = message.chat.id
        user_name = message.from_user.username
        phone_number = message.contact.phone_number

        await message.answer(f"Спасибо! Я получил твой номер телефона: {phone_number}. Теперь тебе доступен полный функционал бота 😋", reply_markup=markup)

        referrer_id = re.findall('\d+', data['user_contact'])
        await state.finish()
        if referrer_id:
            if referrer_id != user_id:
                try:
                    await bot.send_message(referrer_id[0], 'По вашей ссылке перешел новый пользователь!')
                except BotBlocked:
                    pass

        connection.register_user(user_id, user_name, phone_number, referrer_id)



@dp.message_handler(content_types=['text'])
async def user_buttons(message: Message):

    if message.text == '📩Все новости':
        await message.answer('Здесь отображаются все новостные порталы провайдеров')

        keyboard = InlineKeyboardMarkup()
        rows = connection.get_news(message.chat.id)

        subscribed_news = rows[1]

        for row in rows[0]:
            if rows[1][0] is not None and row[0] in subscribed_news[0]:
                button = InlineKeyboardButton(text='✅' + row[1] + ' (Отслеживается)', callback_data="provider_" + str(row[0]))
                keyboard.add(button)
            else:
                button = InlineKeyboardButton(text=row[1], callback_data="provider_" + str(row[0]))
                keyboard.add(button)
    
        await message.answer('Следим за: ', reply_markup=keyboard)


    elif message.text == '📬Мои новости':
        await message.answer('Здесь отображаются новости на которые Вы подписаны')

        my_news = InlineKeyboardMarkup()
        rows = connection.get_sub_news(message.chat.id)

        try:
            for row in rows:
                button = InlineKeyboardButton(text=row[1], callback_data="fkrovider_" + str(row[0]))
                my_news.add(button)
        except TypeError:
            pass
    
        await message.answer('Следим за: ', reply_markup=my_news)

    elif message.text == '📲Пригласить друга':
        await message.answer('Выберите действие 👇', reply_markup=btn_ref)
    
    elif message.text == '🔗Получить ссылку':
        await message.answer(f'Ваша реферальная ссылка: https://t.me/{bot_nickname}?start={message.from_user.id}'
                             f'\n\nИспользуйте её, чтобы приглашать пользователей.', reply_markup=markup)
        
    elif message.text == '📊Статистика':      
        await message.answer(f'Кол-во ваших рефералов: {connection.user_exists(message.chat.id)}', reply_markup=markup)

    elif message.text == '📔Отзывы':
        await message.answer('💌Отзывы RTK | AI  - @example123'
                             '\n\nПолучите обратно 500 рублей на вашу карту, оставив отзыв о подключении услуг провайдера RTK!')

    elif message.text == '🐍О сервисе':
        await message.answer('🤖RTK | AI - лучший новостной агрегатор провайдеров связи'
                             '\n\n@exp_mars - другие наши проекты от создателя бота'
                             '\n\nСобираем последние новости от провайдеров связи и делится ими с нашими пользователями'
                             '\n\n> Получайте информацию без необходимости посещать различные медиа ресурсы провайдеров'
                             '\n\n> Подписываетесь на новости и получайте персональные скидки на услуги связи')

    elif message.text == '📚Инструкции':
        await message.answer('Функция в режиме апробации')

    elif message.text == '☎️Поддержка':
        await message.answer('Функция в режиме апробации')

@dp.callback_query_handler(lambda call: 'provider' in call.data)
async def news_of_providers(call: CallbackQuery):
    with suppress(MessageNotModified):
        provider_id = call.data.split('_')[1]
        provider = connection.get_provider_name(provider_id, call.message.chat.id)

        try:
            if provider[0][0] in provider[1][0]:
                await call.message.edit_text(f'Выбран: {provider[0][1]}', reply_markup=btn_subscribe)

            else:
                await call.message.edit_text(f'Выбран: {provider[0][1]}', reply_markup=btn_stock)

        except TypeError:
            await call.message.edit_text(f'Выбран: {provider[0][1]}', reply_markup=btn_stock)

@dp.callback_query_handler(lambda call: 'fkrovider' in call.data)
async def news_of_providers(call: CallbackQuery):
    with suppress(MessageNotModified): 

        provider_id = call.data.split('_')[1]
        rows = connection.get_provider_name(provider_id, call.message.chat.id)

        if rows[0][0] in rows[1][0]:
            await call.message.edit_text(f'Выбран: {rows[0][1]}', reply_markup=my_btn_subscribe)


@dp.callback_query_handler(lambda call: 'set' in call.data)
async def news_settings(call: CallbackQuery):
    user_id = call.from_user.id
    with suppress(MessageNotModified):

        if call.data == 'set_subscribe':
            await bot.answer_callback_query(call.id)
            await call.message.edit_reply_markup(reply_markup=btn_subscribe)

            provider_name = call.message.text.split(':')[1].strip()
            connection.add_sub(call.data, user_id, provider_name)

        elif call.data == 'set_unsubscribe':
            await bot.answer_callback_query(call.id)
            await call.message.edit_reply_markup(reply_markup=btn_unsubscribe)

            provider_name = call.message.text.split(':')[1].strip()
            connection.add_sub(call.data, user_id, provider_name)

        elif call.data == 'set_back':
            
            keyboard = InlineKeyboardMarkup()
            rows = connection.get_news(call.message.chat.id)
            subscribed_news = rows[1]
            try:
                for row in rows[0]:
                    if row[0] in subscribed_news[0]:
                        button = InlineKeyboardButton(text='✅' + row[1] + ' (Отслеживается)', callback_data="provider_" + str(row[0]))
                        keyboard.add(button)
                    else:
                        button = InlineKeyboardButton(text=row[1], callback_data="provider_" + str(row[0]))
                        keyboard.add(button)
            except TypeError:
                button = InlineKeyboardButton(text=row[1], callback_data="provider_" + str(row[0]))
                keyboard.add(button)

            await call.message.edit_text('Следим за: ', reply_markup=keyboard)

@dp.callback_query_handler(lambda call: 'fket' in call.data)
async def news_settings(call: CallbackQuery):
    user_id = call.from_user.id
    with suppress(MessageNotModified):
        if call.data == 'fket_subscribe':
            await bot.answer_callback_query(call.id)
            await call.message.edit_reply_markup(reply_markup=my_btn_subscribe)

        elif call.data == 'fket_unsubscribe':
            await bot.answer_callback_query(call.id)
            await call.message.edit_reply_markup(reply_markup=my_btn_unsubscribe)

            provider_name = call.message.text.split(':')[1].strip()
            connection.add_sub(call.data, user_id, provider_name)

        elif call.data == 'fket_back':
            my_news = InlineKeyboardMarkup()
            rows = connection.get_sub_news(call.message.chat.id)

            try:
                for row in rows:
                    button = InlineKeyboardButton(text=row[1], callback_data="fkrovider_" + str(row[0]))
                    my_news.add(button)
            except TypeError:
                pass

            await call.message.edit_text('Следим за: ', reply_markup=my_news)