import cherrypy
import socket
import webbrowser
import os
import hashlib
import urllib2
import time
import threading

# Returns the internal IP address of the current machine of which the server is to be hosted on 
def getIP():
	try:
		ip = socket.gethostbyname(socket.getfqdn()) # return fully-qualified domain name
	except:
		ip = ''
	if (not ip) or (ip.startswith('127.')): 
	# linux returns localhost 127.0.0.1, but we need eth0 IP 
	# sourced from http://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-of-eth0-in-python
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # create new socket 
		s.connect(("8.8.8.8", 80)) # open socket to google's DNS server 
		return s.getsockname()[0] # take address from that connection 

	return ip

#ip = getIP() # socket to listen  
ip = "127.0.0.1"
port = 10008 # TCP port to listen 
salt = "COMPSYS302-2017"

class MainApp(object):
	@cherrypy.expose
	def home(self):
		html = open('main.html', 'r')
		page = html.read()
		logged_in = False
		#page = self.checkLogin(page)
		return page

	@cherrypy.expose
	def loggedin(self):
		html = open('loggedin.html', 'r')
		page = str(html.read())
		#html.close()
		#page = self.checkLogin(page)
		return page

	@cherrypy.expose
	def signin(self, username=None, password=None): 
		hash_pw = hashlib.sha256(str(password+salt)).hexdigest()
		error = self.authoriseLogin(username, hash_pw)
		if (error == 0):
			cherrypy.session['username'] = username
			cherrypy.session['password'] = hash_pw 
			self.t = threading.Thread(target=self.report, args=[cherrypy.session['username'], cherrypy.session['password'], Falsae])
			self.daemon = True
			self.t.start()
		else:
			print "login failed!2"
			raise cherrypy.HTTPRedirect('/loggedin')

	@cherrypy.expose
	def report(self, username, hash_pw, first_login):
		response = 0
		if (int(response) == 0):
			#time.sleep(30)
			try:
				url = 'http://cs302.pythonanywhere.com/report?username=' + str(username)
				url += '&password=' + str(hash_pw)  + '&location=' + '2' + '&ip=' + ip # TODO: DON'T HARDCODE LOCATION
				url += '&port=' + str(port) + '&enc=0'
				print "logged in!"
			except:
				print "login failed!"
				raise cherrypy.HTTPRedirect('/home')
			# Getting the error code from the server
			response_message = (urllib2.urlopen(url)).read()
			response = str(response_message)[0]
			# Display response message from the server
			print "Server response: " + str(response_message)
		 

	def authoriseLogin(self, username, hash_pw):
		return self.report(username, hash_pw, True)

	def checkLogin(self, page):
		logged_in = True
		try:
			username = cherrypy.session['username']
		except KeyError:
			logged_in = False

		if (logged_in == True):
			html = open('loggedin.html', 'r')
			page = str(html.read())
			html.close()
			page = self.checkLogin(page)

		return page;

	@cherrypy.expose
	def getOnlineUsers(self):
		try: 
			url = 'http://cs302.pythonanywhere.com/getList?username=' + str(cherrypy.session['username']) + '&password=' + str(cherrypy.session['password']) + '&enc=0'
		except: 
			print "display online users failed"

		response = str((urllib2.urlopen(url)).read())
		error = int(response[0])

		if (error == 0):
			page = ''
			users = response.split()
			for (i in range (len(users))):
				if (',' in users[i]):
					split_users = users[i].split(',')
				# store online user in database (if it is not this current user)
				if (split_users[0] != cherrypy.session['username']):
					user = split_users[0]

	def storeUser(self, user):
		username = user[0]
		location = user[1]
		ip = user[2]
		port = user[3]
		login_time = user[4]

	webbrowser.open_new('http://%s:%d/home' % (ip, port))

def runMainApp():
	conf = {
         '/': {
             'tools.sessions.on': True,
             'tools.staticdir.root': os.path.abspath(os.getcwd())
         },
         '/generator': {
             'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
             'tools.response_headers.on': True,
             'tools.response_headers.headers': [('Content-Type', 'text/plain')],
         },
         '/static': {
             'tools.staticdir.on': True,
             'tools.staticdir.dir': './static'
         }
	}

	cherrypy.tree.mount(MainApp(), "/", conf)

	cherrypy.config.update({'server.socket_host': ip,
						'server.socket_port': port,
						#'engine.autoreload.on': True,
						})


	cherrypy.engine.start() # start webserver

	cherrypy.engine.block() # stop doing anything else 
	#cherrypy.engine.stop() # terminate; stop the channel of the bus 
	cherrypy.server.unsubscribe() # disable built-in HTTP server 

runMainApp()