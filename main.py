import cherrypy
import socket
import webbrowser
import os
import hashlib

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
		html = open('main.html')
		page = html.read()
		return page

	@cherrypy.expose
	def signin(self): 
		try:
			username = cherrypy.session['username']
		except: 
			raise cherrypy.HTTPRedirect('/home')

		hash_pw = hashlib.sha256(str(password+salt)).hexdigest()
		self.auto_report = True
		error = self.authoriseLogin(username, hash_pw)

	def authoriseLogin(self, username, hash_pw):
		return self.report(username, hash_pw, True)

	def report(self, username, hash_pw):
		error = 0
		while (int(error) == 0):
			try:
				url = 'http://cs302.pythonanywhere.com/report?username=' + str(username)
				url += '&password=' + str(hash_pw) + '&ip' + ip
				url += '&port' + str(port) + '&location' + str(location) + '&enc=0'
			except:
				raise cherrypy.HTTPRedirect('/home')
			# Getting the error code from the server
			response_message = (urllib2.urlopen(url)).read()
			response = str(response_message)[0]
			# Display response message from the server
			print "Server response: " + str(response_message)

	webbrowser.open_new('http://%s:%d/home' % (ip, port))

def runMainApp():
	conf = {
		'/': {
		'tools.sessions.on': True, # enable sessions to synchronise activity between users 
		'tools.staticdir.root:': os.path.abspath(os.getcwd()) # serve whole dir
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