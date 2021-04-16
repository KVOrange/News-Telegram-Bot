from newsapi import NewsApiClient
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from config import bot_token, api_token, reg_message
from data_base import User, DbConnector, Category, Keyword

bot = TeleBot(bot_token)
news_api = NewsApiClient(api_key=api_token)


@bot.message_handler(commands=['home'])
def home_command(message):
    db = DbConnector()
    user_tg_id = message.from_user.id
    user = db.session.query(User).filter_by(telegram_id=user_tg_id).first()
    home_handler(message, user)


@bot.message_handler(commands=['start'])
def welcome(message):
    db = DbConnector()
    user_tg_id = message.from_user.id
    user = db.session.query(User).filter_by(telegram_id=user_tg_id).first()
    if not user:
        bot.send_message(message.from_user.id, reg_message)
        bot.register_next_step_handler(message, create_user)
    else:
        bot.send_message(message.from_user.id, 'Здравствуй, ' + user.name)
        home_handler(message, user)


def create_user(message):
    username = message.text
    user = User(message.from_user.id, username)
    data_base = DbConnector()
    data_base.session.add(user)
    data_base.session.commit()
    bot.send_message(message.from_user.id, 'Здравствуй, ' + username)
    home_handler(message, user)


def home_handler(message, user: User):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    subs_news = KeyboardButton(text='Показать новости по подписке')
    keyword_news = KeyboardButton(text='Показать новости по ключевым словам')
    categories = KeyboardButton(text='Подписки')
    keywords = KeyboardButton(text='Ключевые слова')
    markup.row(subs_news, keyword_news)
    markup.row(categories, keywords)
    bot.send_message(user.telegram_id, 'Домашняя страница', reply_markup=markup)
    bot.register_next_step_handler(message, home_keyboard_handler, user)


def home_keyboard_handler(message, user: User):
    if message.text == 'Показать новости по подписке':
        subs_news_handler(message, user)
    elif message.text == 'Показать новости по ключевым словам':
        keywords_news_handler(message, user)
    elif message.text == 'Подписки':
        subscriptions_handler(message, user)
    elif message.text == 'Ключевые слова':
        keywords_handler(message, user)
    else:
        home_handler(message, user)


def subs_news_handler(message, user):
    db = DbConnector()
    user_cats = db.session.query(Category).filter_by(user=user)
    user_cats_id = ''
    for cat in user_cats:
        user_cats_id += cat.news_api_id + ','
    if not user_cats_id:
        bot.send_message(user.telegram_id, 'Вы ещё не подписались ни на один канал!')
        home_handler(message, user)
        return None
    user_cats_id = user_cats_id[:-1]
    news_list = news_api.get_top_headlines(sources=user_cats_id)['articles'][:10]
    if not news_list:
        bot.send_message(user.telegram_id, 'Сейчас новостей нет. Попробуйте чуть позже')
        home_handler(message, user)
        return None
    for news in news_list:
        news_text = '{0}\n{1}\n{2}'.format(news['title'], news['description'], news['url'])
        bot.send_message(user.telegram_id, news_text)
    home_handler(message, user)


def keywords_news_handler(message, user):
    db = DbConnector()
    user_keywords = db.session.query(Keyword).filter_by(user=user)
    user_keywords_names = ''
    for keyword in user_keywords:
        user_keywords_names += keyword.name + ' OR '
    if not user_keywords_names:
        bot.send_message(user.telegram_id, 'У вас ещё нет ключевых слов!')
        home_handler(message, user)
        return None
    user_keywords_names = user_keywords_names[:-4]
    news_list = news_api.get_top_headlines(q=user_keywords_names)['articles'][:10]
    if not news_list:
        bot.send_message(user.telegram_id, 'Сейчас новостей нет. Попробуйте чуть позже')
        home_handler(message, user)
        return None
    for news in news_list:
        news_text = '{0}\n{1}\n{2}'.format(news['title'], news['description'], news['url'])
        bot.send_message(user.telegram_id, news_text)
    home_handler(message, user)


def subscriptions_handler(message, user: User):
    markup_inline = ReplyKeyboardMarkup(resize_keyboard=True)
    info = KeyboardButton(text='Мои подписки')
    add_cat = KeyboardButton(text='Добавить подписку')
    back = KeyboardButton(text='Назад')
    markup_inline.add(info, add_cat, back)
    bot.send_message(user.telegram_id, 'Подписки', reply_markup=markup_inline)
    bot.register_next_step_handler(message, subscriptions_keyboard_handler, user)


def subscriptions_keyboard_handler(message, user: User):
    if message.text == 'Мои подписки':
        db = DbConnector()
        categories = db.session.query(Category).filter_by(user=user)
        bot.send_message(user.telegram_id, 'Ваши подписки:')
        for cat in categories:
            markup = InlineKeyboardMarkup()
            button = InlineKeyboardButton(text='Удалить',
                                          callback_data='del_subs$@{0}'.format(cat.id))
            markup.add(button)
            bot.send_message(user.telegram_id, cat.name, reply_markup=markup)
        subscriptions_handler(message, user)
    elif message.text == 'Добавить подписку':
        add_category_list(message, user)
    elif message.text == 'Назад':
        home_handler(message, user)
    else:
        subscriptions_handler(message, user)


def add_category_list(message, user: User):
    db = DbConnector()
    user_cats = db.session.query(Category).filter_by(user=user)
    user_cat_names = []
    for cat in user_cats:
        user_cat_names.append(cat.name)
    subscriptions = news_api.get_sources()['sources']
    for subscript in subscriptions:
        if subscript['name'] in user_cat_names or subscript['language'] != 'en':
            continue
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text='Подписаться',
                                      callback_data='subs$@{0}$@{1}'.format(subscript['name'], subscript['id']))
        markup.add(button)
        info = 'Название подписки: {0}\nОписание: {1}'.format(subscript['name'], subscript['description'])
        bot.send_message(user.telegram_id, info, reply_markup=markup)
    subscriptions_handler(message, user)


def keywords_handler(message, user: User):
    markup_inline = ReplyKeyboardMarkup(resize_keyboard=True)
    info = KeyboardButton(text='Мои ключевые слова')
    keyword = KeyboardButton(text='Добавить ключевое слово')
    back = KeyboardButton(text='Назад')
    markup_inline.add(info, keyword, back)
    bot.send_message(user.telegram_id, 'Ключевые слова', reply_markup=markup_inline)
    bot.register_next_step_handler(message, keywords_keyboard_handler, user)


def keywords_keyboard_handler(message, user: User):
    if message.text == 'Мои ключевые слова':
        db = DbConnector()
        keywords = db.session.query(Keyword).filter_by(user=user)
        bot.send_message(user.telegram_id, 'Ваши ключевые слова:')
        for keyword in keywords:
            markup = InlineKeyboardMarkup()
            button = InlineKeyboardButton(text='Удалить', callback_data='del_keyw$@{0}'.format(keyword.id))
            markup.add(button)
            bot.send_message(user.telegram_id, keyword.name, reply_markup=markup)
        keywords_handler(message, user)
    elif message.text == 'Добавить ключевое слово':
        bot.send_message(user.telegram_id, 'Введите ключевое слово')
        bot.register_next_step_handler(message, add_keyword, user)
    elif message.text == 'Назад':
        home_handler(message, user)
    else:
        keywords_handler(message, user)


def add_keyword(message, user: User):
    keyword_name = message.text
    keyword = Keyword(keyword_name, user)
    db = DbConnector()
    users_keyword = db.session.query(Keyword).filter_by(user=user)
    users_keyword_names = []
    for word in users_keyword:
        users_keyword_names.append(word.name)
    if keyword_name in users_keyword_names:
        bot.send_message(user.telegram_id, 'У вас уже есть такое ключевое слово')
        keywords_handler(message, user)
    db.session.add(keyword)
    db.session.commit()
    bot.send_message(user.telegram_id, 'Ключевое слово ' + keyword_name + ' успешно добавлено!')
    home_handler(message, user)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    db = DbConnector()
    user = db.session.query(User).filter_by(telegram_id=call.message.chat.id).first()
    if call.data.split('$@')[0] == 'subs':
        cat_data = call.data.split('$@')
        user_cats = db.session.query(Category).filter_by(user=user)
        user_cat_names = []
        for cat in user_cats:
            user_cat_names.append(cat.name)
        if cat_data[1] in user_cat_names:
            bot.send_message(user.telegram_id, 'Вы уже подписаны на этот канал!')
            return None
        new_cat = Category(cat_data[1], cat_data[2], user)
        db.session.add(new_cat)
        db.session.commit()
        bot.send_message(user.telegram_id, 'Подписка на канал ' + cat_data[1] + ' успешно оформлена!')
    if call.data.split('$@')[0] == 'del_subs':
        cat_id = call.data.split('$@')[1]
        cat = db.session.query(Category).filter_by(user=user, id=cat_id).first()
        if not cat:
            bot.send_message(user.telegram_id, 'Что то пошло не так...')
            return None
        cat_name = cat.name
        db.session.delete(cat)
        db.session.commit()
        bot.send_message(user.telegram_id, 'Вы успешно отписались от ' + cat_name)
    if call.data.split('$@')[0] == 'del_keyw':
        keyword_id = call.data.split('$@')[1]
        keyword = db.session.query(Keyword).filter_by(user=user, id=keyword_id).first()
        if not keyword:
            bot.send_message(user.telegram_id, 'Что то пошло не так...')
            return None
        keyword_name = keyword.name
        db.session.delete(keyword)
        db.session.commit()
        bot.send_message(user.telegram_id, 'Вы удалили ключевое слово ' + keyword_name)


bot.polling(none_stop=True, interval=0)
