from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

item_1 = KeyboardButton('Рассылка')
item_2 = KeyboardButton('Новости')
item_3 = KeyboardButton('Выгрузка')
item_4 = KeyboardButton('Статистика')
admin_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True, 
    input_field_placeholder="Выберите команду")

admin_keyboard.row(item_1, item_2)
admin_keyboard.row(item_3, item_4)

analogy = InlineKeyboardButton('🔄Перефразировать', callback_data='analogy')
confirm = InlineKeyboardButton('✅Подтвердить', callback_data='post_confirm')
cancel = InlineKeyboardButton('❌Отменить', callback_data='post_cancel')
back = InlineKeyboardButton('🔙Назад', callback_data='back')

btn_edit_text = InlineKeyboardMarkup()
btn_edit_text.add(analogy)
btn_edit_text.row(confirm, cancel)
btn_edit_text.add(back)


picture = InlineKeyboardButton('🌄Добавить картинку', callback_data='add_picture')
confirm = InlineKeyboardButton('✅Подтвердить', callback_data='mail_confirm')
cancel = InlineKeyboardButton('❌Отменить', callback_data='mail_cancel')

btn_mailing = InlineKeyboardMarkup()
btn_mailing.add(picture)
btn_mailing.row(confirm, cancel)

confirm = InlineKeyboardButton('✅Подтвердить', callback_data='photo_confirm')
cancel = InlineKeyboardButton('❌Отменить', callback_data='photo_cancel')

btn_photo_mailing = InlineKeyboardMarkup()
btn_photo_mailing.row(confirm, cancel)