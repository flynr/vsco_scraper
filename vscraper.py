from requests import get
from requests.exceptions import RequestException
from contextlib import closing 
from bs4 import BeautifulSoup
import json
import shutil
import requests

# TODO:
# Make the get request into a dedicated function with try/catch/error handling
# Keep this func as logic for saving the image to directory
def fetch_image(url, postId):
	rep = get(url, stream=True)
	save_image(rep.raw, postId)


def save_image(raw, postId):
	with open('images/img_'+postId+'.jpg', 'wb') as f:
		shutil.copyfileobj(raw, f)


# Right now this is just grabbing the initial profile page source
def get_html(url):
	# Try to get the content at the URL w/ http get request.
	# If HTML/XML, return content, otherwise None
	try: 
		with closing(get(url)) as resp:
			if good_html(resp):
				return resp.content
			else:
				return None
	except RequestException as e:
		log_error('Error during requests to {0} " {1}'.format(url, str(e)))
		return None


def good_html(resp):
	# Return True if HTML, False otherwise
	content_type = resp.headers['Content-Type']
	return (resp.status_code == 200 
		and content_type is not None 
		and content_type.lower().find('html') > -1)


def log_error(e):
	print(e)


if __name__ == '__main__':

	targetUser = 'ryflyn'
	vsco_page = 'https://vsco.co/' + targetUser
	print('==SCRAPING==')
	raw_html = get_html(vsco_page)
	html = BeautifulSoup(raw_html, 'html.parser')

	page_script = html.find('script', text=lambda t: t.startswith('window.__PRELOADED_STATE__'))
	page_script_text = page_script.text.split(' = ', 1)[1].rstrip(';')
	page_json = json.loads(page_script_text)

	# XHR request for json object to load next page of images
	# Essentially going to just use this request to ask for all images as if 
	# it were all onto one page. 
	queryUrlBase = 'https://vsco.co/api/2.0/medias?'

	authToken = page_json['users']['currentUser']['tkn']
	print("Bearer Token: " + authToken)

	# TODO: if the number of images returned == size, redo request with size*2
	page = 1
	size = 10000 #arbitrarily large
	site_id = page_json['sites']['siteByUsername'][targetUser]['site']['id']

	queryVars = 'site_id={}&page={}&size={}'.format(site_id, page, size)
	queryUrl = queryUrlBase + queryVars
	print('Retrieving from: ' + queryUrl)

	# TODO: Randomize User-Agents?
	headers = {
		'Authorization': 'Bearer ' + authToken, 
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}
	resp = get(queryUrl, headers=headers)
	postObjects = json.loads(resp.content)

	for post in postObjects['media']:
		print('Fetching image ' + str(post['_id']))
		fetch_image('https://' + post['responsive_url'], str(post['_id']))