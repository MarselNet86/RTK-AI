from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

item_1 = KeyboardButton('📩Все новости')
item_2 = KeyboardButton('📬Мои новости')
item_3 = KeyboardButton('📲Пригласить друга')
item_4 = KeyboardButton('📔Отзывы')
item_5 = KeyboardButton('🐍О сервисе')
item_6 = KeyboardButton('📚Инструкции')
item_7 = KeyboardButton('☎️Поддержка')

markup = ReplyKeyboardMarkup(
    resize_keyboard=True, 
    input_field_placeholder="Выберите команду")

markup.row(item_1, item_2)
markup.row(item_3, item_4)
markup.row(item_5, item_6)
markup.add(item_7)


request_phone = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton('Отправить свой контакт ☎️', request_contact=True)
)


button_phone = KeyboardButton(text="Отправить номер телефона", request_contact=True)

reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
reply_keyboard.add(button_phone)

get_ref_link = KeyboardButton('🔗Получить ссылку')
statics = KeyboardButton('📊Статистика')

btn_ref = ReplyKeyboardMarkup(
    resize_keyboard=True, row_width=1
    )

btn_ref.add(get_ref_link, statics)

#Main
subscribe = InlineKeyboardButton('Подписаться', callback_data='set_subscribe')
back = InlineKeyboardButton('🔙Назад', callback_data='set_back')

btn_stock = InlineKeyboardMarkup(row_width=1)
btn_stock.add(subscribe, back)

subscribe = InlineKeyboardButton('📮Отписаться', callback_data='set_unsubscribe')
back = InlineKeyboardButton('🔙Назад', callback_data='set_back')

btn_subscribe = InlineKeyboardMarkup(row_width=1)
btn_subscribe.add(subscribe, back)

subscribe = InlineKeyboardButton('Подписаться', callback_data='set_subscribe')
back = InlineKeyboardButton('🔙Назад', callback_data='set_back')

btn_unsubscribe = InlineKeyboardMarkup(row_width=1)
btn_unsubscribe.add(subscribe, back)

#Twink

subscribe = InlineKeyboardButton('Подписаться', callback_data='fket_subscribe')
back = InlineKeyboardButton('🔙Назад', callback_data='fket_back')

my_btn_stock = InlineKeyboardMarkup(row_width=1)
my_btn_stock.add(subscribe, back)


subscribe = InlineKeyboardButton('📮Отписаться', callback_data='fket_unsubscribe')
back = InlineKeyboardButton('🔙Назад', callback_data='fket_back')

my_btn_subscribe = InlineKeyboardMarkup(row_width=1)
my_btn_subscribe.add(subscribe, back)


subscribe = InlineKeyboardButton('Подписаться', callback_data='fket_subscribe')
back = InlineKeyboardButton('🔙Назад', callback_data='fket_back')

my_btn_unsubscribe = InlineKeyboardMarkup(row_width=1)
my_btn_unsubscribe.add(subscribe, back)