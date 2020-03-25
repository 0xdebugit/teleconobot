import requests
import json
import datetime
import time
import os

from bs4 import BeautifulSoup

import sqlite3

import random

import sys

from api import telegram
from secret import tokens

url = {
	'covid_world_stats' : 'https://coronavirus-tracker-api.herokuapp.com/all',
	'mohfw' : 'http://www.mohfw.gov.in/',
	'indiatoday' : 'https://www.indiatoday.in/coronavirus-covid-19-outbreak',
	'who_safety' : 'https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public',
	'who_myth' : 'https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public/myth-busters',
	'mumbailive' : 'https://www.mumbailive.com',
	'khabar' : 'https://khabar.ndtv.com/topic/corona-virus',
	'abplive_marathi' : 'https://marathi.abplive.com/news/maharashtra/live-blog-22nd-march-2020-todays-breaking-news-marathi-news-latest-updates-janata-curfew-753187',
	'tamil_news18' : 'https://tamil.news18.com/news/national/coronavirus-covid19-outbreak-india-reports-more-cases-san-270231.html',
	'toptamilnews' : 'https://www.toptamilnews.com/coronavirus'
}

dbPath = 'covid.db'
tbl_covid_stats = 'india_covid'
tbl_covid_news = 'news_covid'

class covidStats(object):

	countries = ['China','Italy','Iran','Japan','Singapore'];

	"""Main class for telegram bot functionalities"""
	def __init__(self):
		super(covidStats, self).__init__()
		# self.arg = arg

	def dbcon(self):
		con = sqlite3.connect(dbPath)
		self.initDB(con)
		return con

	def initDB(self,con):
		c = con.cursor()
		covid_stats = 'CREATE TABLE IF NOT EXISTS {} (logged TEXT NOT NULL,state TEXT NOT NULL,total_cases_nat TEXT NOT NULL,total_cases_inter TEXT NOT NULL, cured TEXT NOT NULL,death TEXT NOT NULL)'.format(tbl_covid_stats)
		c.execute(covid_stats)
		covid_news = 'CREATE TABLE IF NOT EXISTS {} (headline TEXT NOT NULL,para TEXT NOT NULL)'.format(tbl_covid_news)
		c.execute(covid_news)
		con.commit()
		return

	def worldStat(self):
		msg = ''
		apiUrl = url['covid_world_stats']
		msg = "\n\n🦠 <b>World Covid-19 Stats</b> 🦠\n\n"
		res = requests.get(apiUrl)
		if(res.status_code == 200):
			data = res.content.decode('utf-8')
			data = json.loads(data)
			confirmed = data['confirmed']
			deaths = data['deaths']
			latest = data['latest']
			recovered = data['recovered']

			msg += "<i>Recent Counts</i> : \n"
			msg += "Confirmed - <code>"+str(latest['confirmed'])+'</code>\n'
			msg += "Deaths - <code>"+str(latest['deaths'])+'</code>\n'
			msg += "Recovered - <code>"+str(latest['recovered'])+'</code>\n\n'

			msg += "<i>Top Countries Affected</i> : \n"

			for country in self.countries:
				count = 0
				for temp in confirmed['locations']:
					if country == temp['country']:
						count += temp['latest']
				msg += '<strong>'+country+'</strong> - <code>'+str(count)+'</code>\n'
			return msg
		else:
			print('Cant fetch Data')

	def indiaStat(self,con,grp_type):
		c = con.cursor()
		msg = ''
		summary_post = {}
		sql_data = []
		urli = url['mohfw']
		res = requests.get(urli)
		
		if(res.status_code == 200):
			soup = BeautifulSoup(res.content,'lxml')
			div = soup.find("div",{"class" : "content newtab"})
			clean_data = div.find('table')
			rows = clean_data.find_all('tr')
			# print(rows)
			# exit()
			summary = rows[-1].find_all('td')
			summary_post['registered'] = sum([int(summary[1].text),int(summary[2].text)])
			summary_post['recovered'] = summary[3].text.replace('\n','')
			summary_post['death'] = summary[4].text.replace('\n','')
			print(summary_post)
			msg_date = time.strftime('%d/%m')
			msg += '🦠 <b>INDIA Covid-19 Stats</b> 🦠 - {}\n'.format(msg_date)
			msg += 'source : Ministry of Health & Family Welfare\n\n'
			msg += 'Registered - '+str(summary_post['registered'])+'\n'
			msg += 'Recovered - '+str(summary_post['recovered'])+'\n'
			msg += 'Death - '+str(summary_post['death'])+'\n\n'
			# msg += '<b>State-wise Count</b>\n\n'
			msg += '<pre>State-Cases-Death</pre>\n'
			# exit()
			# rows.pop(0)
			# rows.pop(-1)
			# print(rows)

			reporting_date = datetime.date.today()

			if_data_exist = 'SELECT logged from {} where logged = "{}" '.format(tbl_covid_stats,reporting_date)
			if_data_exist = c.execute(if_data_exist)
			existQ = if_data_exist.fetchone()

			for r in rows[1:len(rows) - 1]:
				count = 0
				data = r.find_all('td')
				count = sum([int(data[2].text),int(data[3].text)])
				# print(data)

				msg += data[1].text+'-'+str(count)+'-'+data[5].text+'\n'

				if(existQ is None or len(existQ) != 1):
					sql_data = [reporting_date,data[1].text,data[2].text,data[3].text,data[4].text,data[5].text]
					cmdInsertData = 'INSERT INTO {} VALUES (?,?,?,?,?,?)'.format(tbl_covid_stats)
					c.execute(cmdInsertData,sql_data)
					con.commit()

			print(msg)
			world_update = self.worldStat()
			msg += world_update
			telegram.pushMessage(msg,'Html',grp_type)
		else:
			print('Invalid Response')

	def mhStat(self,grp_type):
		msg = ''
		msg += 'Covid-19 | @covid_india |'+time.strftime('%d/%m')+'\n\n'
		msg += 'Covid-19 Cases in Maharashtra\n'
		urli = url['mumbailive']
		res = requests.get(urli)

		if(res.status_code == 200):
			soup = BeautifulSoup(res.content,'lxml')
			# title = soup.find("div",{'class':'container push-half--bottom'})
			title = soup.find("div",{'class':'container push-half--bottom'})
			print(title.text)

			cases = title.findAll('small')
			for i in cases:
				msg += i.text+'\n'

			telegram.pushMessage(msg,'Html',grp_type)
		else:
			print('Invalid Response')


	def eng_news(self,con,grp_type):
		c = con.cursor()
		msg = ''
		urli = url['indiatoday']
		res = requests.get(urli)
		
		if(res.status_code == 200):
			soup = BeautifulSoup(res.content,'lxml')
			clean_data = soup.find("div",{'class' : 'catagory-listing'})
			# print(clean_data)
			img = clean_data.find('img')['src']
			text_data = soup.find("div",{'class' : 'detail'}) 
			para = clean_data.find('p')
			headline = clean_data.find('a')
			print(headline.text)

			if_news_exist = 'SELECT headline from {} where headline = "{}" '.format(tbl_covid_news,headline.text)
			existQ = c.execute(if_news_exist)
			existQ = existQ.fetchone()
			if(existQ is None or len(existQ) != 1):
				msg_date = time.strftime('%d/%m')
				msg += 'Covid-19 | Latest News | {}\n\n'.format(msg_date)
				msg += '<b>{}</b>\n\n'.format(headline.text)
				msg += '<i>{}</i>'.format(para.text)

				telegram.pushMessage(msg,'Html',grp_type)

				cmdInsertData = 'INSERT INTO {} VALUES (?,?)'.format(tbl_covid_news)
				c.execute(cmdInsertData,[headline.text,para.text])
				con.commit()
		else:
			print('Invalid Response')

	def hindi_news(self,grp_type):
		msg = ''
		msg += '<b>Covid-19 | Hindi | @covid_india</b>\n\n'
		# url = 'https://www.mumbailive.com/hi/liveupdates/coronavirus-covid-19-live-updates'
		urli = url['khabar']
		res = requests.get(urli)

		if(res.status_code == 200):
			soup = BeautifulSoup(res.content,'lxml')
			title = soup.findAll("p",{'class':'header fbld'})
			para = soup.find("p",{'class':'intro'})

			# print(clean_data[0].text)
			msg += title[0].text+'\n\n'
			msg += para.text.lstrip()

			telegram.pushMessage(msg,"Html",grp_type)
		else:
			print('Invalid Response')

	def marathi_news(self,grp_type):
		urli = url['abplive_marathi']
		res = requests.get(urli)

		if(res.status_code == 200):
			soup = BeautifulSoup(res.content,'lxml')
			title = soup.findAll("div",{'class':'text-div'})

			for i in title[0:3]:
				para = i.text
				msg = ''
				msg += '<b>Covid-19 | Marathi | @covid_india</b>\n\n'			
				msg += para

				telegram.pushMessage(msg,"Html",grp_type)
		else:
			print('Invalid Response')

	def tamil_news(self,arg,grp_type):

		if(arg == 1):
			msg = ''
			msg += '<b>Covid-19 | Tamil | @covid_india</b>\n\n'
			# url = 'https://www.mumbailive.com/hi/liveupdates/coronavirus-covid-19-live-updates'
			urli = url['tamil_news18']
			# url = 'https://www.maalaimalar.com/Topic/coronavirus'
			res = requests.get(urli)

			if(res.status_code == 200):
				soup = BeautifulSoup(res.content,'lxml')
				# title = soup.find("div",{'class':'lorbox liveb'})
				para = soup.findAll("p")

				# print(vars(title))
				msg += para[2].text+'\n\n'
				# msg += para.text.lstrip()
				# print(msg)
				# exit()

				telegram.pushMessage(msg,"Html",grp_type)

		if(arg == 2):
			msg = ''
			msg += '<b>Covid-19 | Tamil | @covid_india</b>\n\n'
			# url = 'https://www.mumbailive.com/hi/liveupdates/coronavirus-covid-19-live-updates'
			urli = url['toptamilnews']
			# url = 'https://www.maalaimalar.com/Topic/coronavirus'
			res = requests.get(urli)

			if(res.status_code == 200):
				soup = BeautifulSoup(res.content,'lxml')
				title = soup.find("h4",{'class':'post-title'})
				para = soup.find("p",{'class':'post-entry'})	

				msg += title.text+'\n\n'
				msg += para.text

				telegram.pushMessage(msg,"Html",grp_type)

	def safety(self,grp_type):
		msg = ''
		msg += '<b>Covid-19 | Health Safety</b>\n\n'
		urli = url['who_safety']
		res = requests.get(urli)
		if(res.status_code == 200):
			soup = BeautifulSoup(res.content,'lxml')
			clean_data = soup.findAll("h3")
			randno = random.randrange(0,len(clean_data))
			headline = clean_data[randno]
			para = clean_data[randno].next_sibling
			msg += str(headline.text)+'\n\n'
			msg += str(para.text)

			msg += '\n\n<i>Join @covid_india for more.</i>'

			print(msg)

			telegram.pushMessage(msg,'Html',grp_type)
		else:
			print('Invalid Response')

	def myth_buster(self,grp_type):
		msg = ''
		msg += '<b>Covid-19 | Myth Busters</b>\n\n'	
		urli = url['who_myth']
		res = requests.get(urli)
		if(res.status_code == 200):
			soup = BeautifulSoup(res.content,'lxml')
			clean_data = soup.findAll("h2")
			randno = random.randrange(0,len(clean_data))
			headline = clean_data[randno]
			para = clean_data[randno].next_sibling
			msg += str(headline.text)+'\n\n'
			msg += str(para.text)

			msg += '\n\n<i>Join @covid_india for more.</i>'

			print(msg)

			telegram.pushMessage(msg,'Html',grp_type)
		else:
			print('Invalid Response')

	def manualMsg(self,grp_type):
		msg = """ """
		if(msg == ' '):
			exit('Empty Msg')
		else:
			telegram.pushMessage(msg,'Html',grp_type)


def which_execute(arg):
	available = {
		'inStat' : 'indiaStat()',
		'mhStat' : 'mhStat()',
		'eng_news' : 'eng_news()',
		'marathi_news' : 'marathi_news()',
		'hindi_news' : 'hindi_news()',
		'safety' : 'safety()',
		'myth_buster' : 'myth_buster()'
	}

	return available.get(arg,'invalid')

def main():
	if not sys.version_info.major == 3:
		exit('Required Python Version >=3.x')
	op_type = sys.argv[1]
	grp_type = sys.argv[2]
	obj = covidStats()
	con = obj.dbcon()

	if(op_type == 'inStat'):
		obj.indiaStat(con,grp_type)
	elif(op_type == 'mhStat'):
		obj.mhStat(grp_type)
	elif(op_type == 'eng_news'):
		obj.eng_news(con,grp_type)
	elif(op_type == 'marathi_news'):
		obj.marathi_news(grp_type)
	elif(op_type == 'hindi_news'):
		obj.hindi_news(grp_type)	
	elif(op_type == 'tamil_news'):
		obj.tamil_news(random.randrange(1,3),grp_type)
	elif(op_type == 'safety'):
		obj.safety(grp_type)
	elif(op_type == 'myth_buster'):
		obj.myth_buster(grp_type)
	elif(op_type == 'manual'):
		obj.manualMsg(grp_type)
	else:
		exit('Invalid Option : See readme file')

main()