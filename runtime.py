from time import sleep
import math
import serial
import numpy as np
import simpleaudio as sa

def beep():
	filename = 'beep-02.wav'
	wave_obj = sa.WaveObject.from_wave_file(filename)
	play_obj = wave_obj.play()
	play_obj.wait_done()  # Wait until sound has finished playing

def boop():
	filename = 'beep-07.wav'
	wave_obj = sa.WaveObject.from_wave_file(filename)
	play_obj = wave_obj.play()
	play_obj.wait_done()  # Wait until sound has finished playing

def lpaln(zas, thresLow, thresHigh):
	s = False
	for x in zas:
		if x < thresLow:
			s = True
		if s and x > thresHigh:
			return True
	return False

def lastBitNegative(zas, thresLow, thresHigh):
	for i in zas[::-1]:
		if i > thresHigh:
			return False
		if i < thresLow:
			return True

def recognize(xas, yas, zas, xgs, ygs, zgs):
	if (max(yas) > 10000):
		return "toe"
	elif (min(yas) < -7000):
		return "stretch"
	elif (max(zas) > 4000 and min(zas) < -3000 and lpaln(zas, -3000, 4000)):
		return "crouch"
	elif (min(zas) < -4000 or max(zas) > 4000):#lastBitNegative(zas, -3500, 4000)):
		return "jump"
	elif (max(zgs) >= 2000 and min(zgs) <= -2000):
		return "twist"
	elif (max(zgs) >= 1000):
		return "turn"
	elif (max(xas) < 5000 and min(xas) > -4000 and max(yas) < 5000 and min(yas) > -5000 and max(zas) < 1000 and min(zas) > -1000 and max(xgs) < 400 and min(xgs) > -400 and max(ygs) < 400 and min(ygs) > -400 and max(zgs) < 1000 and min(zgs) > -1000):
		return "nothing"
	else:
		return "lunge"

def prettyprint(ans):
	command, x = ans
	if command == "toe":
		return "Touch your toes"
	elif command == "stretch": 
		return "Stretch your back"
	elif command == "crouch" and x == 1:
		return "Squat 1 time"
	elif command == "crouch":
		return "Squat "+str(x)+" times"
	elif command == "jump" and x == 1:
		return "Do 1 jumping jack"
	elif command == "jump":
		return "Do "+str(x)+" jumping jacks"
	elif command == "lunge" and x == 1:
		return "Lunge forward 1 time"
	elif command == "lunge":
		return "Lunge forward "+str(x)+" times"
	elif command == "twist" and x == 1:
		return "Twist right one time"
	elif command == "twist":
		return "Twist right "+str(x)+" times"
	elif command == "turn" and x == 1:
		return "Turn around"
	elif command == "turn":
		return ""

def updateProgram(program, status):
	if len(program) == 0:
		return [(status,1)]
	else: 
		(last, num) = program[-1]
		if last == status and status != "toe" and status != "stretch":
			return program[:-1] + [(status, num+1)]
		else:
			return program + [(status, 1)]

# '/dev/ttyACM0' on raspi
ser = serial.Serial('/dev/cu.usbmodem14101', 9600) # Establish the connection on a specific port
counter = 0 # Below 32 everything in ASCII is gibberish

xa, ya, za, xg, yg, zg = 0,0,0,0,0,0

its = 15

for i in range(its):
	info = ser.readline() # Read the newest output from the Arduino
	info = info.split()
	print(info)
	info = [int(x) for x in info]
	try:
		xa += info[0]
		ya += info[1]
		za += info[2]
		xg += info[3]
		yg += info[4]
		zg += info[5]
	except Exception:
		pass

xav, yav, zav, xgv, ygv, zgv = xa/its, ya/its, za/its, xg/its, yg/its, zg/its
xas, yas, zas, xgs, ygs, zgs = [],[],[],[],[],[]

xa, ya, za, xg, yg, zg = 0,0,0,0,0,0

cooldown = 5
statuses = []
timerCounter = 0
timeToDoAction = 5
timeDelay = 5
program = []

while True:
	if len(program) > 0 and program[-1] == ("turn",2):
		break

	info = ser.readline()
	info = info.split()
	info = [int(x) for x in info]
	counter += 1
	
	xa += info[0]
	ya += info[1]
	za += info[2]
	xg += info[3]
	yg += info[4]
	zg += info[5]

	if counter % its == 0:
		xas.append(xa/its-xav)
		yas.append(ya/its-yav)
		zas.append(za/its-zav)
		xgs.append(xg/its-xgv)
		ygs.append(yg/its-ygv)
		zgs.append(zg/its-zgv)
		xa, ya, za, xg, yg, zg = 0,0,0,0,0,0
		counter = 0
		cooldown -= 1

		timerCounter += 1
		#print(int(xas[-1]),'\t', int(yas[-1]),'\t', int(zas[-1]),'\t', int(xgs[-1]),'\t', int(ygs[-1]), '\t',int(zgs[-1]),'\t\t\t', int(yas[-1] - yas[max(-2,0)]))

		if timerCounter == timeToDoAction:
			boop()
			#print("boop")
			status = recognize(xas, yas, zas, xgs, ygs, zgs)
			xas, yas, zas, xgs, ygs, zgs = [],[],[],[],[],[] #[xas[0]],[yas[0]],[zas[0]],[xgs[0]],[ygs[0]],[zgs[0]]
			program = updateProgram(program, status)
			print(prettyprint(program[-1]))
			#print(program)
		elif timerCounter == timeToDoAction + timeDelay:
			beep()
			#print("beep")
			xas, yas, zas, xgs, ygs, zgs = [],[],[],[],[],[] #[xas[0]],[yas[0]],[zas[0]],[xgs[0]],[ygs[0]],[zgs[0]]
			timerCounter = 0

s = ""
print(program)
for (a,x) in program:
	print (a,x)
	if a == "nothing":
		pass
	else:
		s += prettyprint((a,x)) + "\n"

f = open("main.run", "w+")
f.write(s)
f.close()




