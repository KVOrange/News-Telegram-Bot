import configparser

CONFIG_FILE = 'config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

bot_token = config.get('TELEGRAM', 'BOT_TOKEN')
api_token = config.get('NEWSAPI', 'API_TOKEN')

reg_message = """"Привет! Я бот, который поможет тебе всегда оставаться в курсе важных событий!
Здесь ты можешь подписываться на новостные каналы и искать новости по ключевым словам.
Как я могу к тебе обращаться?"""