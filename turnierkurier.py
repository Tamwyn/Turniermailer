import mysql.connector
import datetime

#Stelle eine Verbindung zur Turniermanagement Datenbank her
cnxTurnier = mysql.connector.connect(user='root', password='', host='localhost', database='turniermanagment')

#Stelle eine Verbindung zur Datenbank mit den Daten der Fechter her
cnxFechter = mysql.connector.connect(user='root', password='', host='localhost', database='fechten')

def GetTournaments():
	#Abfrage nach den Turnieren in den naechsten 6 Wochen
	cursor = cnxTurnier.cursor()
	query =  ("SELECT ID , Name , Datum, Ort, Ausschreibung From turnier WHERE Datum BETWEEN %s AND %s AND casted = 0")

	today = datetime.date.today()
	nextDate = datetime.date.today() + datetime.timedelta(weeks=6)

	cursor.execute(query, (today, nextDate)) #Fuehre die SQL Abfrage aus und ersetze die %s Platzhalter durch die angegebenen Variablen

	GetAge(cursor.fetchall())
	print("Executed")
	cursor.close()	

def GetAge(tournaments):
	print("In Function")
	cursor = cnxTurnier.cursor()
	for rows in tournaments:
		print("In For")
		TurID = rows[0] #Hole die ID des Turniers aus der Abfrage
		TurID = int(TurID)
		query = ("SELECT JahrgID FROM altersklassen WHERE TurnierID = %s")
		
		cursor.execute(query, TurID)

		altersklassen = cursor.fetchall()

		for row in altersklassen:
			print("2nd Function")
			print(row[0])
	cursor.close()
	print("End of Function")

GetTournaments()

#Schließe die Verbindung zu den Datenbanken
cnxTurnier.close()
cnxFechter.close()