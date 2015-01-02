 # coding=utf-8

import mysql.connector
import datetime

import formatize #Formatiere die Ausgaben der SQL Query in eine nuetzliches Dateiformat

##Die Email Module
import smtplib 
from email.mime.text import MIMEText

#####LOGLEVEL#############################################################
##Veraendere den Output des Loglevels um Unterschiedlich praezise 		##
##Daten zu bekommen:													##
##0 : keine; 															##
##1 : Die Werte der Variablen; 											##
##2: Die SQL Queries;													##
loglvl = 0 																##
##########################################################################
try:
	#Stelle eine Verbindung zur Turniermanagement Datenbank her
	cnxTurnier = mysql.connector.connect(user='root', password='', host='localhost', database='turniermanagment')

	#Stelle eine Verbindung zur Datenbank mit den Daten der Fechter her
	cnxFechter = mysql.connector.connect(user='root', password='', host='localhost', database='fechten')

except: #Der Datenbankserver ist anscheinend nicht erreichbar brich daher die Ausfuehrung ab
	exit("Mindestens eine Datenbank konnte nicht erreicht werden")

###################################BEGIN FUNCTIONS##############################################

def GetTournaments():
	if (loglvl ==1): print("GetTournaments")
	#Abfrage nach den Turnieren in den naechsten 6 Wochen
	cursor = cnxTurnier.cursor()
	query =  ("SELECT ID From turnier WHERE Datum BETWEEN %s AND %s AND casted = 0")

	today = datetime.date.today()
	nextDate = datetime.date.today() + datetime.timedelta(weeks=6)

	if (loglvl == 2): print ("Query: " + query + " Heute: " + str(today) + " Ende: " + str(nextDate))

	cursor.execute(query, (today, nextDate)) #Fuehre die SQL Abfrage aus und ersetze die %s Platzhalter durch die angegebenen Variablen

	tournaments = formatize.format(cursor.fetchall()) #Formatiere den Output
	cursor.close()

	if (loglvl ==1): print("TurnierIDs: " + str(tournaments))

	return tournaments
		

def GetAndProcessData(TurID):
	if (loglvl ==1): print("GetAndProcessData")

	informQuery = list()

	
	altersklassen = GetAge(TurID)  #Frage erweiterte Daten zu dem Turnier ab. Dafuer wird jeweils die ID uebergeben Ergebnis: AltersklassenIDs
	if (loglvl ==1): print("AKS: " + str(altersklassen)) 
		
	weapons = CheckWeapon(TurID) #WaffenIDs
	if (loglvl ==1): print("Waffe: " + str(weapons))

	fechter = FindFencers(altersklassen , weapons , TurID)#Suche nach Fechtern fuer die dieses Turnier geeignet ist
	if (loglvl ==1): print("Fechter(GetAndProcessData): " + str(fechter))

	return fechter #Diese Fechter sollen informiert werden


def GetAge(TurID):
	if (loglvl ==1): print("GetAge")
	cursor = cnxTurnier.cursor()

	query = ("SELECT JahrgID FROM altersklassen WHERE TurnierID =")
	query += str(TurID) #Da ein insert via %s fehlschlug der Umweg ueber append
	cursor.execute(query)
    
	result = formatize.format(cursor.fetchall())
	
	cursor.close()
	
	return result


def CheckWeapon(TurID):
	if (loglvl ==1): print("CheckWeapon")
	cursor = cnxTurnier.cursor()
	query = ("SELECT WaffeID FROM waffetur WHERE TurnierID =")
	query += str(TurID) #Da ein insert via %s fehlschlug der Umweg ueber append
	cursor.execute(query)
	
	result = formatize.format(cursor.fetchall())
	
	cursor.close()
	
	return result

def FindFencers(altersklassen, weapons, TurID):
	if (loglvl ==1): print("FindFencers")
	
	cursorFechter = cnxFechter.cursor()
	cursorJahrg   = cnxTurnier.cursor()

	matchingFencers = list()  #Die Fechter deren Waffe und Altersklasse mit der des Turniers uebereinstimmen (Liste)

	for rowAK in altersklassen:
		
		if (loglvl ==1): 
			print("")
			print("Turnier ID:  " + str(TurID))
			print("Altersklasse ID: " + str(rowAK))

		queryZeitraum = ("SELECT Beginn , Ende FROM jahrgaenge WHERE ID =")
		queryZeitraum += str(rowAK) #Appende die Jahrgangs ID an die Query
		 
		cursorJahrg.execute(queryZeitraum)
		zeitraum = cursorJahrg.fetchall() 

		for rowZ in zeitraum: #Speichere den Zeitraum in lesbareren Variablen
		 	beginn = rowZ[0]
		 	ende = rowZ[1]

		if (loglvl ==1): print("Beginn: " + str(beginn) + " Ende: " + str(ende))
		
		queryFencers = ("SELECT DISTINCT ID  From fechter as f JOIN fechterwaffe AS fw ON f.ID = fw.FechterID WHERE Jahrgang BETWEEN %s AND %s AND WaffeID =") #Alle Fechter deren Geburtsjahr innerhalb der Range der erfragten Altersklasse liegt und ihre Waffe übereinstimmt
		
		if (len(weapons) == 1):
			queryFencers += str(weapons[0]) #Appende die ID der Waffe
			if (loglvl ==2): print("Eine WaffenID: " + str(queryFencers)) 
			
		if (len(weapons) == 2): #Wenn ein Turnier fue Beide Waffen verfuegbar ist Frage auch beide ab. Druch DISTINCT erscheint jeder Fechter nur einmal
			queryFencers += str(weapons[0]) + " OR WaffeID =" + str(weapons[1])
			if (loglvl ==2): print("Zwei WaffenIDs: " + str(queryFencers))
			
		else:
			#Should never happen, sonst informiere welches Turnier keine Waffen hat und beende
			exit("[ERR]Keine Waffe angegeben in diesem Turnier"+ str(TurID))
			
		
		cursorFechter.execute(queryFencers, (beginn , ende)) #Fuege Beginn und Ende beim Between ein
				
		matchingFencers.extend(formatize.format(cursorFechter.fetchall()))
		if (loglvl ==1): 
			print("matchingFencers: " + str(matchingFencers))	
			print("")
		
	cursorFechter.close()
	cursorJahrg.close()

	#Sorge dafür, dass fuer dieses Turnier jeder Fechter nur einmal vorhanden ist
	uniqueFencers =list(set(matchingFencers))
	return uniqueFencers


def Inform(informQuery, TurID):
	if (loglvl ==1): print("Inform")
	if (loglvl ==1): print("Fechter IDs " + str(informQuery) + " fuer TurnierID: " + str(TurID))

	#Hole weitere Turnierangaben
	cursorTurnier = cnxTurnier.cursor()
	
	queryTournament = ("SELECT Name , Ausschreibung , Pflichtturnier , Datum , Ort FROM turnier WHERE ID =")
	queryTournament += str(TurID)
	if (loglvl == 2): print(queryTournament)

	cursorTurnier.execute(queryTournament)
	dump = cursorTurnier.fetchall()
	turnier = dump[0]

	TurName = turnier[0]
	TurLink = turnier[1]
	TurPflicht = turnier[2]
	TurDatum = turnier[3].strftime("%a, den %d. %b %Y")
	TurOrt = turnier[4]

	if (loglvl == 1):	
		print(TurName)
		print(TurLink)
		print(TurPflicht)
		print(TurDatum)
		print(TurOrt)
		print("Die Daten des Turniers: " + str(turnier))

	#####Erstelle die Email#####
	mail = "Hallo zusammen, \n"
	mail += "In kürze steht ein neues Turnier an:\n"
	mail += "Das " + TurName + ".\n"
	mail += "Es findet am " + TurDatum + " in " + TurOrt + " statt.\n"
	mail += "Eine Ausschreibung findet sich unter folgendem Link: <a href='" + TurLink  + "'>" + TurLink + "</a>\n"
	if (TurPflicht == 1): mail += "Dieses Turnier ist ein wichtiges Turnier und es ist ärgerlich dieses zu verpassen\n"
	mail += "Bitte meldet euch rechtzeitig zurück, ob ihr starten könnt\n"
	mail += "Mit Fechtergruß\n"
	mail += "Das Turniermanagmentsystem des FC Lütjensee"

	if (loglvl == 1): print(mail)

	try: #Versuche eine Verbindung zum Mailserver herzustellen
		s = smtplib.SMTP('localhost')
	except:
		quit("Der Mailserver konnte nicht erreicht werden")

	msg = MIMEText(mail.encode("utf-8"), "plain", "utf-8")
	msg["Subject"] = "Ein Turnier kommt: " + TurName
	msg["From"] = "thore@datensumpf.de"

	cursorAdresse = cnxFechter.cursor()
	for fechter in informQuery:
		if (loglvl == 1): print("FechterID: " + str(fechter))
		
		queryMail = ("SELECT Email FROM fechter WHERE ID=") #Hole die Mailadresse des Fechters
		queryMail += str(fechter)
		if (loglvl == 2): print(queryMail)

		cursorAdresse.execute(queryMail)
		email = formatize.format(cursorAdresse.fetchall())
		if (loglvl == 1): print("Emailadresse: " + str(email[0].decode("utf-8")))

		#Verfollstaendige das Mail-Formular
		msg["To"] = str(email[0].decode("utf-8"))

		##Versende die Email##
		s.sendmail("thore@datensumpf.de", str(email[0].decode("utf-8")) , msg.as_string())
	
	s.quit() ##Schließe die Verbindung zum Mailserver

	cursorAdresse.close()	
	
def MarkTournament(TurID):
	if (loglvl ==1): print("Inform")
	cursor = cnxTurnier.cursor()

	query = ("UPDATE turnier SET casted='1' WHERE ID=")
	query += str(TurID)
	if (loglvl == 2): print(query)

	cursor.execute() #Schreibe, dass das Turnier gecasted wurde und bestaetige mit commit
	cnxTurnier.commit()

##########################################END OF FUNCTIONS##############################################

########################################################################################################

##########################################BEGIN IMPLEMENTATION##########################################
tournaments = GetTournaments() #Rufe eine Liste der Turniere ab

for TurID in tournaments:
	informQuery = GetAndProcessData(TurID) #Rufe eine Liste mit FechterIDs und zugewiesenen TurnierIDs ab

	Inform(informQuery, TurID)#Versende Emails mit den Ausschreibungen an die Fechter fuer die dieses Turnier geeignet ist

	MarkTournament(TurID) #Speichere in der Datenbank, dass das Turnier gemeldet wurde




#Schliesse die Verbindung zu den Datenbanken
cnxTurnier.close()
cnxFechter.close()
