import cherrypy
import socket
import webbrowser
import os


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

ip = getIP() # socket to listen  
port = 10032 # TCP port to listen on 

class main(object):
	@cherrypy.expose
	def home(self):
		html = open('main.html')
		page = html.read()
		return page

	webbrowser.open_new('http://%s:%d/home' % (ip, port))

def runMain():
	conf = {
		'/': {
		'tools.sessions.on': True, # enable sessions to synchronise activity between users 
		'tools.staticdir.root:': os.path.abspath(os.getcwd()) # serve whole dir
		}
	}

	cherrypy.tree.mount(main(), "/", conf)

	cherrypy.config.update({'server.socket_host': ip,
						'server.socket_port': port,
						#'engine.autoreload.on': True,
						})


	cherrypy.engine.start() # start webserver

	cherrypy.engine.block() # stop doing anything else 
	#cherrypy.engine.stop() # terminate; stop the channel of the bus 
	cherrypy.server.unsubscribe() # disable built-in HTTP server 

runMain()