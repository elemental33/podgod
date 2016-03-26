#!/usr/bin/python
#encoding: utf-8

#/*
# *      Copyright (C) 2015-2016 gerikss, modded with permission by podgod
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# *  ===================
# *
# *  Sbnation API in this plugin belongs to sbnation.com and being used 
# *  only to find NBA/NHL/NFL/MLB games and scores (the same way as on sbnation.com/scoreboard website)
# *  
# *  All Reddit resources used in this plugin belong to their owners and reddit.com
# *  
# *  All logos used in this plugin belong to their owners
# *  
# *  All video streams used in this plugin belong to their owners
# *  
# *  
# */



import urllib, urllib2, sys, cookielib, base64, re
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
from datetime import datetime, timedelta
import json
import calendar, time
import CommonFunctions
import praw
import urlparse
common = CommonFunctions

__addon__ = xbmcaddon.Addon('plugin.video.xrxs')
__addonname__ = __addon__.getAddonInfo('name')
path = __addon__.getAddonInfo('path')
display_score = __addon__.getSetting('score')
display_status = __addon__.getSetting('status')
display_start_time = __addon__.getSetting('start_time')
show_sd = __addon__.getSetting('showsd')
show_xrxs  = __addon__.getSetting('showxrxs')
display_pattern = __addon__.getSetting('pattern')

logos ={'nba':'http://bethub.org/wp-content/uploads/2015/09/NBA_Logo_.png',
'nhl':'https://upload.wikimedia.org/wikipedia/de/thumb/1/19/Logo-NHL.svg/2000px-Logo-NHL.svg.png',
'nfl':'http://www.shermanreport.com/wp-content/uploads/2012/06/NFL-Logo1.gif',
'mlb':'http://content.sportslogos.net/logos/4/490/full/1986.gif',
'soccer':'http://images.clipartpanda.com/soccer-ball-clipart-soccer-ball-clip-art-4.png'}

def utc_to_local(utc_dt):
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)

def GetURL(url, referer=None):
    url = url.replace('///','//')
    request = urllib2.Request(url)
    request.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    if referer:
    	request.add_header('Referer', referer)
    try:
    	response = urllib2.urlopen(request, timeout=5)
    	html = response.read()
    	return html
    except:
    	if 'reddit' in url:
    		xbmcgui.Dialog().ok(__addonname__, 'Looks like '+url+' is down... Please try later...')
    	return None

def GetJSON(url, referer=None):
    request = urllib2.Request(url)
    request.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    if referer:
    	request.add_header('Referer', referer)
    try:
    	response = urllib2.urlopen(request, timeout=5)
    	f = response.read()
    	jsonDict = json.loads(f)
    	return jsonDict
    except:
    	xbmcgui.Dialog().ok(__addonname__, 'Looks like '+url+' is down... Please try later...')
    	return None

def GameStatus(status):
	statuses = {'pre-event':'Not started', 'mid-event':'[COLOR green]In progress[/COLOR]', 'post-event':'Completed', 'postponed':'Postponed'}
	if status in statuses:
		return statuses[status]
	else: return ''	

def Main():
	addDir("[COLOR=FF00FF00][ NHL GAMES ][/COLOR]", '', iconImg='https://upload.wikimedia.org/wikipedia/de/thumb/1/19/Logo-NHL.svg/2000px-Logo-NHL.svg.png', mode="nhl")
	addDir("[COLOR=blue][ MY SUBREDDITS ][/COLOR]", '', iconImg='http://scitechconnect.elsevier.com/wp-content/uploads/2014/07/1reddit-logo2.png', mode="myreddit")
	addDir("[COLOR=FFFFFF00][ Archive ][/COLOR]", '', iconImg='special://home/addons/plugin.video.prosport/icon.png', mode="archive")
	xbmcplugin.endOfDirectory(h)

def Arch():
	addDir("[COLOR=FFFFFF00][ NHL Archive ][/COLOR]", '', iconImg='https://upload.wikimedia.org/wikipedia/de/thumb/1/19/Logo-NHL.svg/2000px-Logo-NHL.svg.png', mode="nhlarch")
	#addDir("[COLOR=FFFFFF00][ MLB Archive ][/COLOR]", '', iconImg='http://content.sportslogos.net/logos/4/490/full/1986.gif', mode="mlbarch")
	xbmcplugin.endOfDirectory(h)
	
def Games(mode):
	today = datetime.utcnow() - timedelta(hours=8)
	today_from = str(today.strftime('%Y-%m-%d'))+'T00:00:00.000-05:00'
	today_to = str(today.strftime('%Y-%m-%d'))+'T23:59:00.000-05:00'
	js = GetJSON('http://www.sbnation.com/sbn_scoreboard/ajax_leagues_and_events?ranges['+mode+'][from]='+today_from+'&ranges['+mode+'][until]='+today_to)
	js = js['leagues'][mode]
	if js:	
		if mode == 'nfl':
			addDir('[COLOR=FF00FF00][B]NFL Redzone[/B][/COLOR]', GAMEURL, iconImg=logos[mode], home='redzone', away='redzone', mode="STREAMS")
		for game in js:
			home = game['away_team']['name']
			away = game['home_team']['name']
			if 'mlb' in mode:
				try:
					hs = str(game['score']['home'][game['score']['cols'].index('R')])
					if not hs:
						hs = '0'
				except:
					hs = '0'
				try:
					avs = str(game['score']['away'][game['score']['cols'].index('R')])
					if not avs:
						avs = '0'
				except:
					avs = '0'
			else:
				hs = str(game['score']['home'][game['score']['cols'].index('Total')])
				if not hs:
					hs = '0'
				avs = str(game['score']['away'][game['score']['cols'].index('Total')])
				if not avs:
					avs = '0'
			score = ' - '+avs+':'+hs
			start_time = game['start_time']
			try:
				plus = False
				st = start_time.replace('T', ' ')
				if '+' in st:
					plus = True
					str_new = st.split('+')[-1]
					st = st.replace('+'+str_new,'')
				else:
					str_new = st.split('-')[-1]
					st = st.replace('-'+str_new,'')
				str_new = str_new.split(':')[0]
				if plus:
					st_time_utc = datetime(*(time.strptime(st, '%Y-%m-%d %H:%M:%S')[0:6]))-timedelta(hours=int(str_new))
				else:
					st_time_utc = datetime(*(time.strptime(st, '%Y-%m-%d %H:%M:%S')[0:6]))+timedelta(hours=int(str_new))
				local_game_time = utc_to_local(st_time_utc)
				local_time_str = ' - '+local_game_time.strftime(xbmc.getRegion('dateshort')+' '+xbmc.getRegion('time').replace('%H%H','%H').replace(':%S',''))
			except:
				local_time_str = ''
			status = GameStatus(game['status'])
			status = ' - '+status
			title = '[COLOR=FF00FF00][B]'+game['title'].replace(game['title'].split()[-1],'')+'[/B][/COLOR]'
			if display_start_time=='true':
				title = title+'[COLOR=FFFFFF00]'+local_time_str+'[/COLOR]'
			if display_status=='true':
				title = title+'[COLOR=FFFF0000]'+status+'[/COLOR]'
			if display_score=='true':
				title = title+'[COLOR=FF00FFFF]'+score+'[/COLOR]'
			addDir(title, mode, iconImg=logos[mode], home=home, away=away, mode="PROSTREAMS")
	else:
		addDir("[COLOR=FFFF0000]Could not fetch today's "+mode.upper()+" games... Probably no games today?[/COLOR]", '', iconImg="", mode="")
	xbmcplugin.endOfDirectory(h, cacheToDisc=True)

def ParseLink(el, orig_title):
	el = 'http'+el.split('http')[-1]
	if 'caststreams' in el:
		url = Caststreams(orig_title)
		return url
	elif 'stream24k.com' in el or 'baltak.com' in el or 'watchnba.tv' in el or 'feedredsoccer.at.ua' in el or 'jugandoes.com' in el or 'wiz1.net' in el or 'bosscast.net' in el or 'watchsportstv.boards.net' in el or 'tv-link.in' in el or 'giostreams.eu' in el or 'klivetv.co' in el or 'videosport.me' in el or 'livesoccerg.com' in el or 'zunox.hk' in el or 'serbiaplus.club' in el or 'zona4vip.com' in el or 'ciscoweb.ml' in el or 'streamendous.com' in el:
		url = Universal(el)
		return url
	elif 'blabseal.com' in el:
		url = Blabseal(el)
		return url
	elif '1apps.com' in el:
		url = Oneapp(el)
		return url
	elif 'youtu' in el and 'list' not in el:
		url = Universal(el)
		return url
	elif 'freecast.in' in el:
		url = Freecastin(el)
		return url
	elif 'streamsus.com' in el:
		url = Streamsus(el)
		return url
	elif 'streamboat.tv' in el:
		url = Streambot(el)
		return url
	elif 'nbastream.net' in el:
		url = Universal(el)
		return url
	elif 'nhlstream.net' in el:
		url = Universal(el)
		return url
	elif 'livenflstream.net' in el:
		url = Universal(el)
		return url
	elif 'fs.anvato.net' in el:
		url = Getanvato(el)
		return url
	elif 'mlblive-akc' in el:
		url = Getmlb(el)
		return url
	elif 'streamsarena.eu' in el:
		url = Streamarena(el)
		return url
	elif 'streamup.com' in el and 'm3u8' not in el:
		url = GetStreamup(el.split('/')[3])
		return url
	elif 'torula' in el:
		url = Torula(el)
		return url
	elif 'gstreams.tv' in el:
		url = Gstreams(el)
		return url
	elif 'nfl-watch.com/live/watch' in el or 'nfl-watch.com/live/-watch' in el or 'nfl-watch.com/live/nfl-network' in el:
		url = Nflwatch(el)
		return url
	elif 'ducking.xyz' in el:
		url = Ducking(el)
		return url
	elif 'streamandme' in el:
		url = Universal(el)
		return url
	elif 'henno.info' in el:
		url = Henno(el)
		return url
	elif 'stream2hd.net' in el:
		url = Stream2hd(el)
		return url
	elif 'serbiaplus.club/cbcsport.html' in el:
		url = CbcSportAz(el)
		return url
	elif 'mursol.moonfruit.com' in el:
		url = Moonfruit(el)
		return url
	elif 'castalba.tv' in el:
		url = Castalba(el)
		return url
	elif 'room' in el and 'm3u8' in el:
		url = Getroom(el)
		return url
	elif '101livesportsvideos.com' in el:
		url = Universal(el)
		return url
	elif '.m3u8' in el and 'room' not in el and 'anvato' not in el and 'mlblive-akc' not in el:
		return el
				

def strip_non_ascii(string):
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)

def Archive(page, mode):
	if mode == 'mlbarch':
		url = 'http://www.life2sport.com/category/basketbol/nba/page/'+str(page)
	if mode == 'nbaarch':
		url = 'http://www.life2sport.com/category/basketbol/nba/page/'+str(page)
	elif mode == 'nflarch':
		url = 'http://www.life2sport.com/category/american-football/page/'+str(page)
	html = GetURL(url)
	links = common.parseDOM(html, "a", attrs={"rel": "bookmark"}, ret="href")
	titles = common.parseDOM(html, "a", attrs={"rel": "bookmark"}, ret="title")
	del links[1::2]
	for i, el in enumerate(links):
		if '-nba-' in el or '-nfl-' in el:
			title = common.parseDOM(html, "a", attrs={"href": el}, ret="title")[0]
			title = title.split('/')[-1]+' - '+title.split('/')[len(title.split('/'))-2]
			title = strip_non_ascii(title)
			title = title.replace('&#8211;','').strip()
			addDir(title, el, iconImg="", mode="playarchive")
	uri = sys.argv[0] + '?mode=%s&page=%s' % (mode, str(int(page)+1))
	item = xbmcgui.ListItem("next page...", iconImage='', thumbnailImage='')
	xbmcplugin.addDirectoryItem(h, uri, item, True)
	xbmcplugin.endOfDirectory(h, cacheToDisc=True)
	
def Nhlarchive(page, mode):
	url = 'http://rutube.ru/api/video/person/979571/?page='+str(page)+'&format=json'
	json = GetJSON(url)
	json = json['results']
	for el in json:
		title = el['title']
		id = el['id']
		img = el['thumbnail_url']
		addLink(title, title, id, iconImg=img, mode="playnhlarchive")
	uri = sys.argv[0] + '?mode=%s&page=%s' % (mode, str(int(page)+1))
	item = xbmcgui.ListItem("next page...", iconImage='', thumbnailImage='')
	xbmcplugin.addDirectoryItem(h, uri, item, True)
	xbmcplugin.endOfDirectory(h, cacheToDisc=True)

def Playnhlarchive(url):
	orig_title = xbmc.getInfoLabel('ListItem.Title')
	url = 'http://rutube.ru/api/play/options/'+url+'?format=json'
	json = GetJSON(url)
	link = json['video_balancer']['m3u8']
	Play(link, orig_title)
	
def PlayArchive(url):
	orig_title = xbmc.getInfoLabel('ListItem.Title')
	html = GetURL(url)
	html = html.split('>english<')[-1]
	link = common.parseDOM(html, "iframe", ret="src")[0]
	link = link.replace('https://videoapi.my.mail.ru/videos/embed/mail/','http://videoapi.my.mail.ru/videos/mail/')
	link = link.replace('html','json')
	cookieJar = cookielib.CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar), urllib2.HTTPHandler())
	conn = urllib2.Request(link)
	connection = opener.open(conn)
	f = connection.read()
	connection.close()
	js = json.loads(f)
	for cookie in cookieJar:
		token = cookie.value
	js = js['videos']
	for el in js:
		addLink(el['key'], orig_title, el['url']+'|Cookie=video_key='+token, mode="PLAY")
	xbmcplugin.endOfDirectory(h, cacheToDisc=True)

def GetStreamup(channel):
	try:
		chan = GetJSON('https://api.streamup.com/v1/channels/'+channel)
		if chan['channel']['live']:
			videoId = chan['channel']['capitalized_slug'].lower()
			domain = GetURL('https://lancer.streamup.com/api/redirect/'+videoId)
			return 'https://'+domain+'/app/'+videoId+'_aac/playlist.m3u8'
	except:
		return None	

def GetYoutube(url):
	try:
		if ('channel' in url or 'user' in url) and 'live' in url:
			html = GetURL(url)
			videoId = html.split("https://www.youtube.com/watch?v=")[-1].split('">')[0]
			link = 'plugin://plugin.video.youtube/?action=play_video&videoid=' + videoId
			return link
		regex = (r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
		youtube_regex_match = re.match(regex, url)
		videoId = youtube_regex_match.group(6)
		link = 'plugin://plugin.video.youtube/?action=play_video&videoid=' + videoId
		return link
	except:
		return None
		
def Xrxs(home, away):
	try:
		today = datetime.utcnow() - timedelta(hours=8)
		today = str(today.strftime('%Y-%m-%d'))
		html = GetURL("http://xrxs.net/nhl/?date="+today)
		html = html.split('<br/><hr/>')
		for el in html:
			if home.lower() in el.lower() and away.lower() in el.lower():
				links = common.parseDOM(el, "a", ret="href")
				for link in links:
					if '5000' in link:
						if 'HOME' in link:
							addDirectLink('HOME', {'Title': away+' @ '+home}, link)
						elif 'VISIT' in link:
							addDirectLink('VISIT', {'Title': away+' @ '+home}, link)
						elif 'FRENCH' in link:
							addDirectLink('FRENCH', {'Title': away+' @ '+home}, link)
						elif 'NATIONAL' in link:
							addDirectLink('NATIONAL', {'Title': away+' @ '+home}, link)
	except:
		pass	


def Caststreams(orig_title):
	try:
		orig_title = orig_title.replace('[COLOR=FF00FF00][B]','').replace('[/B][/COLOR]','')
		home = orig_title.split('at')[0].split()[0]
		away = orig_title.split('at')[-1].split()[0]
		url = 'https://caststreams.com:2053/login'
		data = urllib.urlencode({"email":"prosport@testmail.com","password":"prosport","ipaddress":"desktop","androidId":"","deviceId":"","isGoogleLogin":0})
		request = urllib2.Request(url, data)
		response = urllib2.urlopen(request, timeout=5)
		resp = response.read()
		jsonDict = json.loads(resp)
		token = jsonDict['token']
		url = 'https://caststreams.com:2053/feeds'
		request = urllib2.Request(url)
		request.add_header('Authorization', token)
		response = urllib2.urlopen(request, timeout=5)
		resp = response.read()
		jsonDict = json.loads(resp)
		feeds = jsonDict['feeds']
		for feed in feeds:
			title = feed['nam'].lower().replace('ny', 'new')
			if home.lower() in title.lower() and away.lower() in title.lower() and 'testing' not in title.lower():
				channel = feed['url'][0]
				link = 'https://caststreams.com:2053/getGame?rUrl='+channel
				return link	
			else:
				continue
	except:
		return None		
		
def Oneapp(url):
	try:
		html = GetURL(url)
		block_content = common.parseDOM(html, "iframe", ret="src")[0]
		link = GetYoutube(block_content)
		return link
	except:
		return None
		
def Torula(url):
	try:
		html = GetURL(url)
		block_content = common.parseDOM(html, "input", attrs={"id": "vlc"}, ret="value")[0]
		link = block_content
		return link
	except:
		return None

def Freecastin(url):
	try:
		html = GetURL(url)
		block_content = common.parseDOM(html, "iframe", attrs={"width": "100%"}, ret="src")[0]
		link = GetYoutube(block_content)
		return link
	except:
		return None
		
def Streamsus(url):
	try:
		html = GetURL(url)
		block_content = common.parseDOM(html, "iframe", ret="src")[0]
		link = GetYoutube(block_content)
		return link
	except:
		return None

def CbcSportAz(url):
	try:
		html = GetURL('http://serbiaplus.club/embedhls/cbcsport.html')
		regex = re.compile(r'([-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,4}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?)',re.IGNORECASE)
		links = re.findall(regex, html)
		for link in links:
			if 'http' in link[0] and 'm3u8' in link[0]:
				return link[0]
	except:
		return None
			
def Streambot(url):
	try:
		cookieJar = cookielib.CookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar), urllib2.HTTPHandler())
		conn = urllib2.Request('https://streamboat.tv/signin')
		connection = opener.open(conn, timeout=5)
		for cookie in cookieJar:
			token = cookie.value
		headers = {
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3",
            "Content-Type" : "application/x-www-form-urlencoded",
            "Cookie":"_gat=1; csrftoken="+token+"; _ga=GA1.2.943051497.1450922237",
            "Origin":"https://streamboat.tv",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8,bg;q=0.6,it;q=0.4,ru;q=0.2,uk;q=0.2",
            "Accept-Encoding" : "windows-1251,utf-8;q=0.7,*;q=0.7",
            "Referer": "https://streamboat.tv/signin"
		}
		reqData = {'csrfmiddlewaretoken':token,'username' : 'test_user', 'password' : 'password'}
		conn = urllib2.Request('https://streamboat.tv/signin', urllib.urlencode(reqData), headers)
		connection = opener.open(conn, timeout=5)
		conn = urllib2.Request(url)
		connection = opener.open(conn, timeout=5)
		html = connection.read()
		connection.close()
		link1 = 'http://' + html.split("cdn_host: '")[-1].split("',")[0]
		link2 = html.split("playlist_url: '")[-1].split("',")[0]
		link = link1+link2
		return link
	except:
		return None

def Nbanhlstreams(url):
	try:
		if 'nba' in url:
			URL = 'http://www.nbastream.net/'
		elif 'nhl' in url:
			URL = 'http://www.nhlstream.net/'
		elif 'nfl' in url:
			URL = 'http://www.livenflstream.net/'
		html = GetURL(url)
		link = common.parseDOM(html, "iframe",  ret="src")[0]
		html  = GetURL(URL+link)
		link = common.parseDOM(html, "iframe",  ret="src")[0]
		if 'streamup' in link:
			channel = link.split('/')[3]
			link = GetStreamup(channel)
			return link
	except:
		return None
		
def Streamandme(url):
	try:
		html = GetURL(url)
		link = common.parseDOM(html, "iframe",  ret="src")[0]
		channel = link.split('/')[3]
		link = GetStreamup(channel)
		return link
	except:
		return None

def Henno(url):
	try:
		url = 'http://henno.info/stream?stream=Streamup&source=&template=any&ticket=&user='
		html = GetURL(url)
		link = common.parseDOM(html, "iframe",  ret="src")[0]
		channel = link.split('/')[3]
		link = GetStreamup(channel)
		return link
	except:
		return None
		
def Stream2hd(url):
	try:
		html = GetURL(url)
		link = common.parseDOM(html, "iframe",  ret="src")[0]
		if 'streamup' in link:
			channel = link.split('/')[3]
			link = GetStreamup(channel)
			return link
	except:
		return None

def Gstreams(url):
	try:
		html = GetURL(url)
		link = common.parseDOM(html, "iframe",  ret="src")[0]
		if 'gstreams.tv' in link:
			html  = GetURL(link)
			link = html.split('https://')[1]
			link = link.split('",')[0]
			link = 'https://' + link 
			return link
		elif 'streamup.com' in link and 'm3u8' not in link:
			channel = link.split('/')[3]
			link = GetStreamup(channel)
			return link
		elif 'youtu' in link:
			link = GetYoutube(link)
			return link
		elif 'm3u8' in link:
			return link
	except:
		return None
		
def Moonfruit(url):
	try:
		cookieJar = cookielib.CookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar), urllib2.HTTPHandler())
		conn = urllib2.Request(url+'/htown3')
		connection = opener.open(conn, timeout=5)
		for cookie in cookieJar:
			token = cookie.value
		headers = {
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3",
            "Content-Type" : "application/x-www-form-urlencoded",
            "Cookie":"markc="+token,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8,bg;q=0.6,it;q=0.4,ru;q=0.2,uk;q=0.2",
		}
		html = connection.read()
		link = common.parseDOM(html, "iframe",  ret="src")
		link = url+link[-1]
		conn = urllib2.Request(link, headers=headers)
		connection = opener.open(conn, timeout=5)
		html = connection.read()
		link = common.parseDOM(html, "iframe",  ret="src")[0]
		if 'streamup.com' in link:
			channel = link.split('/')[4]
			link = GetStreamup(channel)
			return link
	except:
		return None

def Nflwatch(url):
	try:
		html = GetURL(url)
		links = common.parseDOM(html, "iframe",  ret="src")
		for link in links:
			if 'streamup' in link:
				channel = link.split('/')[3]
				link = GetStreamup(channel)
				return link
			else:
				continue
		if 'p2pcast' in html:
			id = html.split("'text/javascript'>id='")[-1]
			id = id.split("';")[0]
			link = p2pcast(id)
			return link
	except:
		return None

def Ducking(url):
	try:
		request = urllib2.Request('http://www.ducking.xyz/kvaak/stream/basu.php')
		request.add_header('Referer', 'www.ducking.xyz/kvaak/')
		request.add_header('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36')
		response = urllib2.urlopen(request, timeout=5)
		html = response.read()
		link = common.parseDOM(html, "iframe", ret="src")[0]
		channel = link.split('/')[3]
		link = GetStreamup(channel)
		return link
	except:
		return None
		
def Streamarena(url):
	try:
		html = GetURL(url)
		link = common.parseDOM(html, "iframe",  ret="src")[0]
		link = link.replace('..','http://www.streamsarena.eu/')
		html  = GetURL(link)
		if 'streamup' in html:
			link = common.parseDOM(html, "iframe",  ret="src")[0]
			channel = link.split('/')[3]
			link = GetStreamup(channel)
			return link
		elif 'p2pcast' in html:
			id = html.split("'text/javascript'>id='")[-1]
			id = id.split("';")[0]
			link = p2pcast(id)
			return link
	except:
		return None
		
def Livesports101(url):
	try:
		html = GetURL(url)
		try:
			block_content = common.parseDOM(html, "meta", attrs={"property": "og:description"}, ret="content")
			for el in block_content:
				if 'youtube.com' in el:
					link = GetYoutube(block_content)
					return link
				elif 'streamboat.tv' in el:
					link = el
					link = link.split('http://')[1]
					link = link.split("'")[0]
					link = 'http://' + link 
					return link
				elif 'streamup' in el:
					link = el
					link = link.split('https://')[1]
					link = link.split("'")[0]
					link = 'https://' + link 
					return link
		except:
			pass
		try:	
			block_content = common.parseDOM(html, "embed", attrs={"id": "vlcp"}, ret="target")[0]
			if 'streamboat' in block_content or 'streamup' in block_content:
				link = block_content
				return link
		except:
			pass
		try:
			block_content = common.parseDOM(html, "iframe", ret="src")[0]
			if 'streamup' in block_content:
				channel = block_content.split('/')[3]
				link = GetStreamup(channel)
				return link
			elif 'youtube.com' in block_content:
					link = GetYoutube(block_content)
					return link
			elif 'wiz1' in block_content:
				this = GetURL(block_content, referer=block_content)
				link = re.compile('src="(.+?)"').findall(str(this))[0]
				if 'sawlive' in link:
					link = sawresolve(link)
					return link
		except:
			pass
	except:
		return None

def Castalba(url):
	try:
		try:
			cid  = urlparse.parse_qs(urlparse.urlparse(url).query)['cid'][0] 
		except:
			cid = re.compile('channel/(.+?)(?:/|$)').findall(url)[0]
		try:
			referer = urlparse.parse_qs(urlparse.urlparse(url).query)['referer'][0]
		except:
			referer='http://castalba.tv'        
		url = 'http://castalba.tv/embed.php?cid=%s&wh=600&ht=380&r=%s'%(cid,urlparse.urlparse(referer).netloc)
		pageUrl=url
		request = urllib2.Request(url)
		request.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		request.add_header('Referer', referer)
		response = urllib2.urlopen(request, timeout=5)
		result = response.read()
		result=urllib.unquote(result)
		if 'm3u8' in result:
			link = re.compile('filez\s*=\s*(?:unescape\()\'(.+?)\'').findall(result)[0]
			link = 'http://' + url + '.m3u8'
			link += '|%s' % urllib.urlencode({'User-Agent': client.agent(), 'Referer': referer})          
		else:
			try:
				filePath = re.compile("'file'\s*:\s*(?:unescape\()?'(.+?)'").findall(result)[0]  
			except:
				file = re.findall('var file\s*=\s*(?:unescape\()?(?:\'|\")(.+?)(?:\'|\")',result)[0]
				try:
					file2 = re.findall("'file':\s*unescape\(file\)\s*\+\s*unescape\('(.+?)'\)",result)[0]
					filePath = file+file2
				except:
					filePath = file
			swf = re.compile("'flashplayer'\s*:\s*\"(.+?)\"").findall(result)[0]
			try:
				streamer=re.findall('streamer\(\)\s*\{\s*return \'(.+?)\';\s*\}',result)[0]
				if 'rtmp' not in streamer:
					streamer = 'rtmp://' + streamer
			except:
				try:
					streamer = re.compile("var sts\s*=\s*'(.+?)'").findall(result)[0]
				except:
					streamer=re.findall('streamer\(\)\s*\{\s*return \'(.+?)\';\s*\}',result)[0]    
			link = streamer.replace('///','//') + ' playpath=' + filePath +' swfUrl=' + swf + ' flashver=WIN\\2020,0,0,228 live=true timeout=15 swfVfy=true pageUrl=' + pageUrl
		return link
	except:
		return None


def Universal(url):
	if 'zona4vip.com/live' in url:
		url = url.replace('/live','')
	if 'serbiaplus.club/wlive' in url:
		url = 'http://serbiaplus.club/whd/'+url.split('/w')[-1]
	if 'wiz1' in url or 'live9.net' in url:
		this = GetURL(url, referer=url)
		link = re.compile('src="(.+?)"').findall(str(this))[0]
		if 'sawlive' in link:
			lnk = sawresolve(link)
			return lnk
	if 'streamup' in url:
		if 'm3u8' in url:
			return url
		channel = url.split('/')[3]
		link = GetStreamup(channel)
		return link
	if 'youtu' in url:
		link = GetYoutube(url)
		return link
	if 'lshstream' in url:
		link = lshstream(url)
		return link
	html = GetURL(url, referer=url)
	if html and 'weplayer.pw' in html:
		id = html.split("'text/javascript'>id='")[-1]
		id = id.split("';")[0]
		link = weplayer(id)
		return link
	elif html and 'p2pcast' in html:
		id = html.split("'text/javascript'>id='")[-1]
		id = id.split("';")[0]
		link = p2pcast(id)
		return link
	elif html and 'castup' in html:
		id = html.split('fid="')[-1].split('";')[0]
		link = castup(id)
		return link
	elif html and 'streamking.cc' in html:
		id = re.findall('(http://streamking.+?")',html)[0]
		id = id.replace('"','')
		link = streamking(id)
		return link
	elif html and 'hdcast.org' in html:
		id = html.split('fid="')[-1]
		id = id.split('";')[0]
		link = hdcast(id)
		return link
	elif html and 'm3u8' in html:
		link = re.findall('(http://.+?\.m3u8)',html)[0]
		return link
	elif html and 'rtmp' in html and 'jwplayer' in html:
		link = re.findall('(rtmp://.+?")',html)[0]
		link = link.replace('"','')
		return link
	else:
		domain = urlparse.urlparse(url).netloc
		scheme = urlparse.urlparse(url).scheme
		urls = common.parseDOM(html, 'iframe', ret='src')
		if urls:
			for url in urls:
				if 'http://' not in url and 'https://' not in url:
					if not url.startswith('/'):
						url = '/'+url
					if scheme:
						url = scheme+'://'+domain+url
					else:
						url = 'http://'+domain+url
				ss = Universal(url)
				if ss:
					return ss
				else:
					Universal(url)


def sawresolve(url):
	try:
		page = re.compile('//(.+?)/(?:embed|v)/([0-9a-zA-Z-_]+)').findall(url)[0]
		page = 'http://%s/embed/%s' % (page[0], page[1])
		try: 
			referer = urlparse.parse_qs(urlparse.urlparse(url).query)['referer'][0]
		except: 
			referer = url
		ch = url.split("/")[-1]
		request = urllib2.Request(url)
		request.add_header('Referer', referer)
		request.add_header('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36')
		response = urllib2.urlopen(request, timeout=5)
		result = response.read()
		url = common.parseDOM(result, 'iframe', ret='src')[-1]
		url = url.replace(' ', '').split("'")[0]
		sw = re.compile("sw='(.+?)'").findall(str(result))
		if not sw:
			sw = re.compile("ch='(.+?)'").findall(str(result))
		url = url+'/'+ch+'/'+sw[0]
		try:
			url = url.replace('watch//', 'watch/')
		except:
			pass
		request = urllib2.Request(url)
		request.add_header('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36')
		response = urllib2.urlopen(request, timeout=5)
		result = response.read()
		file = re.compile("'file'.+?'(.+?)'").findall(result)
		if file:
			file = file[0]
		else:
			file = result.split("'file', ")[-1].split(");")[0].replace("'","").replace('unescape(','')
		if 'http' in file:
			if 'm3u8' in file:
				return file
			request = urllib2.Request(file)
			request.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
			request.add_header('Referer', file)
			response = urllib2.urlopen(request, timeout=5)
			url = response.geturl()
			url += '|%s' % urllib.urlencode({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36', 'Referer': file})
			return url
		else:
			file = urllib.unquote(file)
			strm = re.compile("'streamer'.+?'(.+?)'").findall(result)
			if strm:
				strm = strm[0]
				if 'skin' in strm:
					strm = re.findall('(rtmp://.+?sh)',result)[0]
			else:
				strm = result.split("'streamer', ")[-1].split(");")[0].replace("'","").replace('unescape(','')
			strm = urllib.unquote(strm)
			swf = re.compile("SWFObject\('(.+?)'").findall(result)[0]
			if '+' in file:
				flile = result.split("flile = '")[-1].split("';")[0].replace("'","").replace('unescape(','')
				flile = urllib.unquote(flile)
				tkta = result.split("tkta = '")[-1].split("';")[0].replace("'","").replace('unescape(','')
				tkta = urllib.unquote(tkta)
				file = flile+'?'+tkta
			url = '%s playpath=%s swfUrl=%s pageUrl=%s live=1 timeout=40' % (strm, file, swf, url)
			return url
	except:
		return None


def castup(id):
	try:
		url = 'http://www.castup.tv/embed_2.php?channel='+id
		pageUrl = url
		try: referer = urlparse.parse_qs(urlparse.urlparse(url).query)['referer'][0]
		except: referer = url
		result = GetURL(url, referer)
		json_url = re.compile('\$.getJSON\("(.+?)", function\(json\){').findall(result)[0]
		token = re.compile("\('token', '(.+?)'\);").findall(result)[0]
		data = GetJSON(json_url, referer)
		file = data['streamname']
		rtmp = data['rtmp']
		swf ='http://www.castup.tv' + re.compile('.*?SWFObject\([\'"]([^\'"]+)[\'"].*').findall(result)[0]
		url = rtmp + ' playpath=' + file + ' swfUrl=' + swf + ' live=1 timeout=15 token=' + token + ' swfVfy=1 pageUrl=' + pageUrl
		return url
	except:
		return None

def p2pcast(id):
	try:
		agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'
		url = 'http://p2pcast.tech/stream.php?id='+id+'&live=0&p2p=0&stretching=uniform'
		request = urllib2.Request(url)
		request.add_header('User-Agent', agent)
		request.add_header('Referer', url)
		response = urllib2.urlopen(request, timeout=5)
		html = response.read()
		token = html.split('murl = "')[1].split('";')[0]
		link = base64.b64decode(token)
		request = urllib2.Request('http://p2pcast.tech/getTok.php')
		request.add_header('User-Agent', agent)
		request.add_header('Referer', url)
		request.add_header('X-Requested-With', 'XMLHttpRequest')
		response = urllib2.urlopen(request, timeout=5)
		html = response.read()
		js = json.loads(html)
		tkn = js['token']
		link = link+tkn
		link = link + '|User-Agent='+agent+'&Referer='+url
		return link
	except:
		return None

def weplayer(id):
	try:
		url = 'http://weplayer.pw/stream.php?id='+id
		request = urllib2.Request(url)
		request.add_header('Host', urlparse.urlparse(url).netloc)
		request.add_header('Referer', 'http://wizhdsports.com')
		request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36')
		response = urllib2.urlopen(request, timeout=5)
		result = response.read()
		id = result.split("'text/javascript'>id='")[-1]
		id = id.split("';")[0]
		url2 = 'http://deltatv.xyz/stream.php?id='+id
		request = urllib2.Request(url2)
		request.add_header('Referer', url)
		request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36')
		response = urllib2.urlopen(request, timeout=5)
		result = response.read()
		streamer = result.split("streamer=")[-1].split("&amp;")[0]
		file = result.split("file=")[-1].split("&amp;")[0]
		url = streamer+' playpath='+file+' swfUrl=http://cdn.deltatv.xyz/players.swf token=Fo5_n0w?U.rA6l3-70w47ch pageUrl='+url2+' live=1'
		return url
	except:
		return None

def streamking(url):
	try:
		html = GetURL(url, referer=url)
		link = re.findall('(http://.+?\.m3u8)',html)[0]
		link += '|User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36&Referer='+url
		return link
	except:
		return None	


def hdcast(id):
	try:
		page = 'http://www.hdcast.org/embedlive2.php?u=%s&vw=640&vh=400&domain=www.nhlstream.net' % id
		request = urllib2.Request(url)
		request.add_header('Referer', 'http://www.nhlstream.net')
		response = urllib2.urlopen(request, timeout=5)
		result = response.read()
		#result = GetURL(page, referer='http://www.nhlstream.net/')
		streamer = re.compile('file\s*:\s*\'(.+?)\'').findall(result)[0]
		token = 'SECURET0KEN#yw%.?()@W!'
		url = '%s swfUrl=http://player.hdcast.org/jws/jwplayer.flash.swf pageUrl=%s token=%s swfVfy=1 live=1 timeout=15' % (streamer, page, token)
		return url
	except:
		return None


def lshstream(url):
	try:
		url = 'http://'+url.split('http://')[-1]
		id = urlparse.parse_qs(urlparse.urlparse(url).query)['u'][0]
		result = GetURL(url, referer=url)
		streamer = result.replace('//file', '')
		streamer = re.compile("file *: *'(.+?)'").findall(streamer)[-1]
		url=streamer + ' swfUrl=http://www.lshstream.com/jw/jwplayer.flash.swf flashver=WIN/2019,0,0,185 live=1 token=SECURET0KEN#yw%.?()@W! timeout=14 swfVfy=1 pageUrl=http://cdn.lshstream.com/embed.php?u=' + id
		return url
	except:
		return None


def Play(url, orig_title):
    url = ParseLink(url, orig_title)
    if not url:
    	dialog = xbmcgui.Dialog()
    	dialog.notification('Pro Sport', 'Stream not found', xbmcgui.NOTIFICATION_INFO, 3000)
    else:
    	item = xbmcgui.ListItem(path=url)
    	item.setInfo('video', { 'Title': orig_title })
    	xbmcplugin.setResolvedUrl(h, True, item)

    	
def addDir(title, url, iconImg="DefaultVideo.png", home="", away="", mode=""):
    sys_url = sys.argv[0] + '?url=' + urllib.quote_plus(url) + '&home=' + urllib.quote_plus(str(home)) +'&away=' + urllib.quote_plus(str(away)) +'&mode=' + urllib.quote_plus(str(mode))
    item = xbmcgui.ListItem(title, iconImage=iconImg, thumbnailImage=iconImg)
    item.setInfo(type='Video', infoLabels={'Title': title})
    xbmcplugin.addDirectoryItem(handle=h, url=sys_url, listitem=item, isFolder=True)

def addDir2(title, url, next_url, iconImg="DefaultVideo.png", popup=None, mode=""):
    sys_url = sys.argv[0] + '?url=' + urllib.quote_plus(url)+'&next_url=' + urllib.quote_plus(next_url) +'&mode=' + urllib.quote_plus(str(mode))
    item = xbmcgui.ListItem(title, iconImage=iconImg, thumbnailImage=iconImg)
    item.setInfo(type='Video', infoLabels={'Title': title})
    if popup:
    	item.addContextMenuItems(popup, True)
    xbmcplugin.addDirectoryItem(handle=h, url=sys_url, listitem=item, isFolder=True)

def addLink(title, orig_title, url, iconImg="DefaultVideo.png", mode=""):
    sys_url = sys.argv[0] + '?url=' + urllib.quote_plus(url) + '&mode=' + urllib.quote_plus(str(mode))+ '&orig=' + urllib.quote_plus(str(orig_title))
    item = xbmcgui.ListItem(title, iconImage=iconImg, thumbnailImage=iconImg)
    item.setLabel(title)
    item.setInfo(type='Video', infoLabels={'Title': title})
    item.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=h, url=sys_url, listitem=item)
    
def addDirectLink(title, infoLabels, url, iconImg="DefaultVideo.png"):
    item = xbmcgui.ListItem(title, iconImage=iconImg, thumbnailImage=iconImg)
    item.setInfo(type='Video', infoLabels=infoLabels)
    xbmcplugin.addDirectoryItem(handle=h, url=url, listitem=item)
       
def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]

    return param

h = int(sys.argv[1])
params = get_params()

mode = None
url = None

try: mode = urllib.unquote_plus(params['mode'])
except: pass

try: url = urllib.unquote_plus(params['url'])
except: pass

try: home = urllib.unquote_plus(params['home'])
except: pass

try: away = urllib.unquote_plus(params['away'])
except: pass

try: orig_title = urllib.unquote_plus(params['orig'])
except: pass

try: page = params['page'] if 'page' in params else 1
except: pass

if mode == None: Main()
elif mode == 'nhl': Games(mode)
elif mode == 'nhlarch': Nhlarchive(page, mode)
elif mode == 'archive': Arch()
elif mode == 'playarchive': PlayArchive(url)
elif mode == 'playnhlarchive': Playnhlarchive(url)
elif mode == 'XRXSSTREAMS': Xrxs(home, away)
elif mode == 'MYSTREAMS': getMyStreams(url, home)
elif mode == 'PLAY': Play(url, orig_title)
elif mode == 'topics': Topics(url)
elif mode == 'addnew': Addnew()
elif mode == 'remove': Remove(url)
elif mode == 'edit': Edit(url)

xbmcplugin.endOfDirectory(h)