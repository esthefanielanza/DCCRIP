# coding=utf-8
import select, socket, sys, json, threading, time


def routeMessage(source, destinaton, typeT):
	outMessage = {
		"source": source,
		"destination": destination,
		"type": typeT											
	}		

def addEnlace(ip, weight, enlaces):
	enlaces[ip] = weight
	print('==== Enlaces ====')
	print(enlaces)

def delEnlace(ip, enlaces):
	if(ip in enlaces):
		del enlaces[ip]
		print("Removed ip ", ip)		
	
def updateRoutes(period, enlaces):
	while(True):
		time.sleep(period)
		print('Updating')
		for key, value in enlaces.items():
			print(key)

			# searching how to send a json
			# updateMessage = {
			# 	'type': 'update'
			# 	'source': e
			# }

def main(addr, period, startup):
	udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	dest = (addr, 55151)
	enlaces = {}
	
	updateThread = threading.Thread(target=updateRoutes, args=(period, enlaces))
	updateThread.start()

	while(True):
		command = input().lower().split(' ')

		if(command[0] == 'add'):
			if(len(command) >= 3):
				addEnlace(command[1], command[2], enlaces)
			else:
				print('Invalid params, add should have an ip and weight.')
		elif(command[0] == 'del'):
			if(len(command) >= 2):
				delEnlace(command[1], enlaces)
			else:
				print('Invalid params, del should have an ip')
		elif(command[0] == 'trace'):
			print('Should thrace')
		elif(command[0] == 'quit'):
			exit(1)
		else:
			print('Invalid command, please try again.')

if __name__ == "__main__":
	main(sys.argv[1], int(sys.argv[2]), len(sys.argv) == 4 and sys.argv[3])
