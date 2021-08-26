import configparser
import datetime
import json
import os
import random
import requests
from aiohttp import web
from PIL import Image, ImageDraw, ImageFont

conf = configparser.ConfigParser()
conf.read('config.ini')

HOSTNAME = conf['SERVER_SETTINGS']['hostname']
SERVERPORT = conf['SERVER_SETTINGS']['serverport']

BOT_TOKEN = conf['BOT_SETTINGS']['bot_token']
BOT_REQUEST_URL = 'https://api.telegram.org/bot' + BOT_TOKEN + '/'

TABLE_COLOR = conf['GAME_SETTINGS']['table_color']
INGAME_TEXT_COLOR = conf['GAME_SETTINGS']['ingame_text_color']
ENDGAME_TEXT_COLOR = conf['GAME_SETTINGS']['endgame_text_color']
GAME_FONT = conf['GAME_SETTINGS']['game_font']

help_text =  '/start - Start a new game;\n'
help_text += '/help - Command list.'

etc_text = 'This bot is support only default commands /start and /help.'

list_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
list_suit = ['C', 'D', 'H', 'S']

def card_list_to_string(card_list):
	card_string = ''
	for j in card_list:
		if (len(card_string) != 0):
			card_string += ','
		card_string += j
	return(card_string)

def new_card():
	c = random.randint(0, len(list_cards)-1)
	s = random.randint(0, len(list_suit)-1)
	return(list_cards[c]+list_suit[s])
	
def score_update(card_list):
	score = 0
	aces = 0
	for card in card_list:
		if (card[0:-1] == 'A'):
			score += 11
			aces += 1
		elif ((card[0:-1] == 'J') or (card[0:-1] == 'Q') or (card[0:-1] == 'K')):
			score += 10
		else:
			score += int(card[0:-1])
	for i in range(aces):
		if (score > 21):
			score -= 10
	return(score)

def end_game_result(dealer_round_score, player_round_score, dealer_game_score, player_game_score):
	if ((player_round_score > 21) or ((dealer_round_score <= 21) and (dealer_round_score > player_round_score))):
		return('Dealer Win.', dealer_game_score+1, player_game_score)
	elif (player_round_score == dealer_round_score):
		return('Push.', dealer_game_score, player_game_score)
	else:
		return('Player Win.', dealer_game_score, player_game_score+1)
	
def draw_game(dealer_cards, player_cards, dealer_round_score, player_round_score, dealer_game_score, player_game_score, end_game=''):
	table = Image.new('RGB', (500, 640), color = TABLE_COLOR)
	i = 0
	for card_name in dealer_cards:
		card = Image.open('PNG/'+card_name+'.png')
		table.paste(card, (160+i*35,10), card)
		i += 1
	i = 0
	for card_name in player_cards:
		card = Image.open('PNG/'+card_name+'.png')
		table.paste(card, (160+i*35,330), card)
		i += 1
	img_draw = ImageDraw.Draw(table)
	font_title = ImageFont.truetype(GAME_FONT, 45)
	font_score = ImageFont.truetype(GAME_FONT, 55)
	img_draw.text((10, 10), 'Dealer', fill=INGAME_TEXT_COLOR, font=font_title, stroke_width=1, stroke_fill='black')
	img_draw.text((20, 50), str(dealer_round_score), fill=INGAME_TEXT_COLOR, font=font_score, stroke_width=1, stroke_fill='black')
	img_draw.text((10, 110), 'Wins:', fill=INGAME_TEXT_COLOR, font=font_title, stroke_width=1, stroke_fill='black')
	img_draw.text((20, 150), str(dealer_game_score), fill=INGAME_TEXT_COLOR, font=font_score, stroke_width=1, stroke_fill='black')
	img_draw.text((10, 330), 'Player', fill=INGAME_TEXT_COLOR, font=font_title, stroke_width=1, stroke_fill='black')
	img_draw.text((20, 370), str(player_round_score), fill=INGAME_TEXT_COLOR, font=font_score, stroke_width=1, stroke_fill='black')
	img_draw.text((10, 430), 'Wins:', fill=INGAME_TEXT_COLOR, font=font_title, stroke_width=1, stroke_fill='black')
	img_draw.text((20, 470), str(player_game_score), fill=INGAME_TEXT_COLOR, font=font_score, stroke_width=1, stroke_fill='black')
	font_end_game = ImageFont.truetype(GAME_FONT, 80)
	if (len(end_game) > 0):
		img_draw.text((50, 280), end_game, fill=ENDGAME_TEXT_COLOR, font=font_end_game, stroke_width=3, stroke_fill='black')
	return(table)

def data_string_parser(incoming_data_string):
	data_list = incoming_data_string.split(';')
	if (len(data_list) == 5):
		return(data_list[1].split(','), data_list[2].split(','), int(data_list[3]), int(data_list[4]))
	else:
		return([], [], 0, 0)

def new_game(incoming_data_string, chat_id):
	dealer_cards = []
	player_cards = []
	if (incoming_data_string == 'newgame'):
		dealer_game_score = 0
		player_game_score = 0
	else:
		dealer_game_score = int(incoming_data_string.split(';')[1])
		player_game_score = int(incoming_data_string.split(';')[2])
	player_cards.append(new_card())
	dealer_cards.append(new_card())
	player_cards.append(new_card())
	player_round_score = score_update(player_cards)
	dealer_round_score = score_update(dealer_cards)
	if (player_round_score < 21):
		game_table = draw_game(dealer_cards, player_cards, dealer_round_score, player_round_score, dealer_game_score, player_game_score)
		data_string = ';'+card_list_to_string(dealer_cards)+';'+card_list_to_string(player_cards)+';'+str(dealer_game_score)+';'+str(player_game_score)
		buttons_json = json.dumps({'inline_keyboard': [[{'text': 'Stand', 'callback_data': 'S'+data_string},{'text': 'Hit', 'callback_data': 'H'+data_string}]]})
	else:
		if ((player_round_score == 21) and ((dealer_round_score == 10) or (dealer_round_score == 11))):
			dealer_cards.append(new_card())
			dealer_round_score = score_update(dealer_cards)
		end_game,dealer_game_score,player_game_score = end_game_result(dealer_round_score, player_round_score, dealer_game_score, player_game_score)
		if ((player_round_score == 21) and (end_game != 'Push.')):
			end_game = 'Blackjack!'
		game_table = draw_game(dealer_cards, player_cards, dealer_round_score, player_round_score, dealer_game_score, player_game_score, end_game)
		buttons_json = json.dumps({'inline_keyboard': [[{'text': 'Next Round', 'callback_data': 'Next'+';'+str(dealer_game_score)+';'+str(player_game_score)}]]})
	png_file_name = 'table_'+str(chat_id)+'_'+str(datetime.datetime.now()).replace(' ','')+'.png'
	game_table.save('PNG/'+png_file_name, format='PNG')
	return(buttons_json, png_file_name)
		
async def post_handler(request):
	request_data = await request.text()
	request_json = {}
	try:
		request_json = json.loads(request_data)
	except error:
		print(error)
		return web.Response()
	if ('message' in request_json):
		message = {	'chat_id': request_json['message']['chat']['id'],
					'text': ''
				}
		if ('text' in request_json['message']):
			command_found_in_text = False
			msg_txt = request_json['message']['text'].lower()
			if (msg_txt.find('/start') + 1):
				message['text'] = 'For start new game press button below.'
				button_list = [[{'text': 'New Game', 'callback_data': 'newgame'}]]
				message['reply_markup'] = json.dumps({'inline_keyboard': button_list})
				command_found_in_text = True
			elif (msg_txt.find('/help') + 1):
				message['text'] = help_text
				command_found_in_text = True
			if (not command_found_in_text):
				message['text'] = etc_text
		else:
			message['text'] = etc_text
		if (len(message['text'])>0):
			response = requests.post(BOT_REQUEST_URL + 'sendMessage', data=message)
	elif ('callback_query' in request_json):
		params = {	'chat_id': request_json['callback_query']['message']['chat']['id'],
					'message_id': request_json['callback_query']['message']['message_id']
				}
		if (request_json['callback_query']['data'] == 'newgame'):
			buttons_list,table_file_name = new_game(request_json['callback_query']['data'],request_json['callback_query']['message']['chat']['id'])
			params['reply_markup'] = buttons_list
			files = {'photo': open('PNG/'+table_file_name, 'rb')}
			response = requests.post(BOT_REQUEST_URL + 'sendPhoto', files=files, data=params)
			os.remove('PNG/'+table_file_name)
		elif (request_json['callback_query']['data'].split(';')[0] == 'S'):
			dealer_cards,player_cards,dealer_game_score,player_game_score = data_string_parser(request_json['callback_query']['data'])
			dealer_round_score = score_update(dealer_cards)
			while (dealer_round_score < 17):
				dealer_cards.append(new_card())
				dealer_round_score = score_update(dealer_cards)
			player_round_score = score_update(player_cards)
			dealer_round_score = score_update(dealer_cards)
			end_game,dealer_game_score,player_game_score = end_game_result(dealer_round_score, player_round_score, dealer_game_score, player_game_score)
			game_table = draw_game(dealer_cards, player_cards, dealer_round_score, player_round_score, dealer_game_score, player_game_score, end_game)
			png_file_name = 'table_'+str(params['chat_id'])+'_'+str(datetime.datetime.now()).replace(' ','')+'.png'
			game_table.save('PNG/'+png_file_name, format='PNG')
			params['reply_markup'] = json.dumps({'inline_keyboard': [[{'text': 'Next Round', 'callback_data': 'Next'+';'+str(dealer_game_score)+';'+str(player_game_score)}]]})
			params['media'] = json.dumps({'type': 'photo', 'media': 'attach://media'})
			files = {'media': open('PNG/'+png_file_name, 'rb')}
			response = requests.post(BOT_REQUEST_URL + 'editMessageMedia', files=files, data=params)
			os.remove('PNG/'+png_file_name)
		elif (request_json['callback_query']['data'].split(';')[0] == 'H'):
			dealer_cards,player_cards,dealer_game_score,player_game_score = data_string_parser(request_json['callback_query']['data'])
			player_cards.append(new_card())
			player_round_score = score_update(player_cards)
			dealer_round_score = score_update(dealer_cards)
			if (player_round_score < 21):
				game_table = draw_game(dealer_cards, player_cards, dealer_round_score, player_round_score, dealer_game_score, player_game_score)
				data_string = ';'+card_list_to_string(dealer_cards)+';'+card_list_to_string(player_cards)+';'+str(dealer_game_score)+';'+str(player_game_score)
				params['reply_markup'] = json.dumps({'inline_keyboard': [[{'text': 'Stand', 'callback_data': 'S'+data_string}, {'text': 'Hit', 'callback_data': 'H'+data_string}]]})
			else:
				end_game,dealer_game_score,player_game_score = end_game_result(dealer_round_score, player_round_score, dealer_game_score, player_game_score)
				game_table = draw_game(dealer_cards, player_cards, dealer_round_score, player_round_score, dealer_game_score, player_game_score, end_game)
				params['reply_markup'] = json.dumps({'inline_keyboard': [[{'text': 'Next Round', 'callback_data': 'Next'+';'+str(dealer_game_score)+';'+str(player_game_score)}]]})
			png_file_name = 'table_'+str(params['chat_id'])+'_'+str(datetime.datetime.now()).replace(' ','')+'.png'
			game_table.save('PNG/'+png_file_name, format='PNG')
			params['media'] = json.dumps({'type': 'photo', 'media': 'attach://media'})
			files = {'media': open('PNG/'+png_file_name, 'rb')}
			response = requests.post(BOT_REQUEST_URL + 'editMessageMedia', files=files, data=params)
			os.remove('PNG/'+png_file_name)
		elif (request_json['callback_query']['data'].split(';')[0] == 'Next'):
			buttons_list,table_file_name = new_game(request_json['callback_query']['data'],request_json['callback_query']['message']['chat']['id'])
			params['reply_markup'] = buttons_list
			params['media'] = json.dumps({'type': 'photo', 'media': 'attach://media'})
			files = {'media': open('PNG/'+table_file_name, 'rb')}
			response = requests.post(BOT_REQUEST_URL + 'editMessageMedia', files=files, data=params)
			os.remove('PNG/'+table_file_name)
		response = requests.post(BOT_REQUEST_URL + 'answerCallbackQuery', data={'callback_query_id': request_json['callback_query']['id']})
	return web.Response()

app = web.Application()
app.add_routes([web.post('/', post_handler)])

if __name__ == "__main__":
	web.run_app(app, host=HOSTNAME, port=SERVERPORT)