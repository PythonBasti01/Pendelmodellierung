#Klasse für Datenbank
"""
Die Klasse soll die Infrastukur für die Stoffdatenbank stellen. Die Stoffdatenbank soll als ein Objekt
der Datenbank Klasse erstellt werden. Dort werden dann die einzelnen Tabellen mit den Daten importiert.
"""
# Bibliotheken
import sqlite3
import os
import csv
from scipy import interpolate


class Datenbank():

# Initialisierung der Klasse
    def __init__(self, name):
        self.name = name
        self.connection = None
        first = not os.path.exists("datenbanken/{}.db".format(self.name))
        self.start()
        if first:
            # Verzeichnis mit allen Tabellen in der Datenbank
            header = ["TabellenName","Interpolation","AnzahlParameter","ListeParameter"]
            dataType = ["TEXT","INTEGER" ,"INTEGER","TEXT"]
            self.creatTable("Tabellen", header, 0, dataType)
            self.check()

#Herstellung der Verbindung zur Datenbank
    def start(self):
        if self.connection is None: # Prüfen ob es schon eine Verbondung gibt
            try:
                self.connection = sqlite3.connect("datenbanken/{}.db".format(self.name))
                self.cursor = self.connection.cursor()
                self.connection.commit()
                print("Verbindung zur Datenbank hergestellt")
            except Error as e:
                print(e)

# Erstellung einer Tabelle
# header ist Liste mit Überschriften der Spalten
# dataType ist Format der später hinzugefügten Daten (nur ein Format für alle Daten möglich)
    def creatTable(self, tableName, header, interpolation = 1, dataType = "FLOAT"):
        sql_inst = "CREATE TABLE IF NOT EXISTS {} (id integer PRIMARY KEY,".format(tableName)
        i = 0
        for nr in header:
            if dataType == "FLOAT":
                sql_inst += " {} {},".format(nr, dataType)
            else:
                sql_inst += " {} {},".format(nr, dataType[i])
            i += 1
        sql_inst = sql_inst[:-1]
        sql_inst += ")"
        self.cursor.execute(sql_inst)
        self.connection.commit()
        print("Tabelle wurde erstellt")
        row = [ tableName, interpolation , len(header) , self.toText(header)]
        self.insterData( "Tabellen", row)


#Funktion fügt die Daten "data" zur Tabelle hinzu
    def insterData(self, tableName, data):
        columns = self.getColumns(tableName)
        dataDimension = 1
        try:
            if len(data) != len(columns):
                dataDimension = 2
                if len(data[0]) != len(columns):
                    print("Anzahl der Daten und Anzahl der Spalten in der Tabelle stimmen nicht überein")
                    print("Daten konnten nicht eingefügt werden")
                    return False
        except:
            print("Anzahl der Daten und Anzahl der Spalten in der Tabelle stimmen nicht überein")
            print("Daten konnten nicht eingefügt werden")
            return False
        columns_text = self.toText(columns)
        sql_inst = "INSERT INTO {} ( {} ) VALUES (".format(tableName , columns_text)
        counter = 0
        while counter < len(columns):
            sql_inst += "?,"
            counter += 1
        sql_inst = sql_inst[:-1]
        sql_inst += ")"
        if dataDimension == 2:
            self.cursor.executemany(sql_inst, data)
            self.connection.commit()
        else:
            self.cursor.execute(sql_inst, data)
        self.connection.commit()
        print("Die Daten wurden hinzugefügt")

#Funktion gibt einen Wert aus der Tabelle anhand eines Referenzwertes zurück[A1.3.2]
    def value(self,tableName, refParameter, refWert, parameter):
        value = None
        sql_inst = "SELECT {} From {} WHERE {} = '{}' ".format(parameter, tableName, refParameter, refWert)
        self.cursor.execute(sql_inst)
        value = self.cursor.fetchall()
        if value == [] or value == None:
            print("Kein passender Wert in der Tabelle, es wird interpoliert")
            value = self.interpolation(tableName, refParameter, refWert, parameter)
        else:
            value = value[0][0]
        return value

#Interpolation wenn Wert zwischen zwei Werten in der Tabelle liegt
    def interpolation(self, tableName, refParameter, refWert, parameter):
        sql_inst = "SELECT Interpolation From Tabellen WHERE TabellenName= '{}' ".format(tableName)
        self.cursor.execute(sql_inst)
        interpolation = self.cursor.fetchall()
        if interpolation == 0:  #Überprüfen ob Tabelle für Interpolation geeignet ist
            print("Die Tabelle ist nicht für Interpolation geeignet")
            return False
        sql_inst = "SELECT {} From {} ORDER BY id ".format(parameter, tableName)
        self.cursor.execute(sql_inst)
        parameterList = convert2DArray(self.cursor.fetchall())
        sql_inst = "SELECT {} From {} ORDER BY id ".format(refParameter, tableName)
        self.cursor.execute(sql_inst)
        refparameterList = convert2DArray(self.cursor.fetchall())
        try:
            f = interpolate.interp1d(refparameterList, parameterList, kind = 'linear')
            valueInter = f(refWert)
            self.connection.commit()
        except ValueError:
            print("Der Wert ist außerhalb des Zahlen Bereiches der vorhandenen Daten")
            return False
        except :
            print("Es gab einen Error")
            return False
        return valueInter

# Die Funktion gibt die Spaltennamen der Tabelle als Liste zurück (ohne id PRIMARY KEY)
    def getColumns(self,tableName):
        sql_inst = "SELECT * from {}".format(tableName)
        self.cursor.execute(sql_inst)
        columns = [tuple[0] for tuple in self.cursor.description]
        columns.pop(0)
        return columns

#Funktion liest eine CSV Datei ein , erzeugt eine neue Tabelle falls noch nicht vorhanden und fügt die Daten aus der CSV Datei in die TAbelle ein
#Die erste Zeile der CSV Datei wird aös header eingelesen und sind die Überschriften der Spalten der Tabelle
    def importcsv(self, file, tableName = None):
        file = file.strip()
        file = file.lower()
        if file.endswith(".csv") == False:
            file = file + ".csv"
        print("datenbanken/" + file)
        if os.path.exists("datenbanken/" + file) == False:
            print("Datei konnte nicht gefunden werden")         #Arbeitsverzeichnis checken
            return False
        data = []
        with open('datenbanken/'+file) as csvdatei:
            csvreader = csv.reader(csvdatei, delimiter = ';')   #vlt anderes Trennzeichen prüfen
            header = next(csvreader)
            for row in csvreader:
                data.append(row)
        if tableName == None:                                   #Wenn kein Tabellenname gegeben wird Dateiname genommen
            tableName = file[:-4]
        self.creatTable(tableName, header)
        self.insterData(tableName, data)
        print("Die Datei " + file + " wurde erfolgreich eingelesen")

# Funktion gibt Stadardmässig alle Daten einer Tabelle zurück oder nur bestimmte Spalten bei übergabe der parameter
    def read(self,tableName ,parameter = ["*"]): #default alle spalten, sonst spalten =[...,...,...]
        sql_inst = "SELECT "
        for nr in parameter:
            sql_inst += nr
            sql_inst += ","
        sql_inst = sql_inst[:-1]
        sql_inst += " FROM {}".format(tableName)
        print(sql_inst)
        self.cursor.execute(sql_inst)
        data = self.cursor.fetchall()
        print("Daten aus Datenbank abgerufen")
        return data

#Gibt Bestimmte Parameter (Standard alle) einer Tabelle in eine CSV Datei aus
    def printcsv(self, tableName , file, parameter = ["*"] ):
        file = file.strip()
        file = file.lower()
        if file.endswith(".csv") == False:
            file = file + ".csv"
        if parameter[0] == "*" :
            parameter = self.getColumns(tableName)
        data = self.read(tableName,parameter)
        header = parameter
        with open(file,'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ';')
            writer.writerow(header)
            writer.writerows(data)
            print("Daten wurden in Ausgabedatei gespeichert")

#Checkt ob die im Ordner Datebank vorhandenen Tabellen schon in der Datenbank vorhanden sind
    def check(self):
        if not os.path.isdir('datenbanken/'):
            print("das Unterverzeichnis datenbank/ konnte nicht gefunden werden")
        files = os.listdir('datenbanken/')
        for nr in files:
            if nr.endswith(".CSV") or nr.endswith(".csv") :
                tableName = nr[:-4]
                if self.exist(tableName):
                    sql_inst = "SELECT count() FROM '{}'".format(tableName)
                    self.cursor.execute(sql_inst)
                    countRowsTable = self.cursor.fetchall()
                    countRowsTable = countRowsTable [0][0]
                    with open("datenbanken/" + nr) as f:
                        countRowsfile = sum(1 for line in f)-1
                    if countRowsTable != countRowsfile:
                        print("Die Daten in der CSV Datei {} und Datenbank stimmen nicht überein".format(nr))
                        self.update(tableName)
                    else:
                        print("Die Tabelle {} ist bereits in der Datenbank".format(nr))
                else:
                    print("es wurde eine neue Datei gefunden. {} wird in die Datenbank integriert".format(nr))
                    self.importcsv(nr)
        return True

#Funktion überprüft ob es eine Tabelle mit dem übergebenen Namen bereits in der Datenbank gibt
    def exist(self, tableName):
        sql_inst = "SELECT id From Tabellen WHERE TabellenName = '{}' ".format(tableName)
        self.cursor.execute(sql_inst)
        result = self.cursor.fetchall()
        if result == []:
            return False
        else:
            return True

#Funktion Löscht eine Tabelle aus der Datenbank
    def delete(self, tableName):
        sql_inst = "DROP TABLE '{}' ".format(tableName)
        self.cursor.execute(sql_inst)
        sql_inst = "DELETE FROM Tabellen WHERE TabellenName = '{}' ".format(tableName)
        print("Tabelle wurde gelöscht")

#Funktion updatet eine Tabell aus der Datenbank mit einer CSV Datei
    def update(self, tableName):
        self.delete(tableName)
        self.importcsv(tableName)

# Beenden der Verbindung zur Datenbank
    def end(self):
        self.connection.commit()
        self.connection.close()
        self.connection = None
        print("Die Verbindung wurde getrennt")

# Wandelt die übergebene Liste in einen Text um, der in den SQL Anweisungen eingefügt werden kann
    def toText(self, list):
        text = ""
        for nr in list:
            text += nr
            text += ","
        text = text[:-1]
        return text

#Konvertiert ein zweidimesnionales Array in ein eindimensionales Array mit nur den ersten Einträgen der zweiten dimension
def convert2DArray(list):
    result =[]
    for nr in list:
        result.append(nr[0])
    return result

#Test Funktion zum Testen der Datenbank Klasse
def test():
    name = "testdatenbank"
    test = Datenbank(name)
    spalten = ["spalte1","spalte2","spalte3","spalte4"]
    test.creatTable("testTabelle", spalten)
    spalten = test.getColumns("testTabelle")
    print(spalten)
    data =[(1.1 , 1.2 , 1.3 , 1.4),(2.1 , 2.2 , 2.3 , 2.4),(3.1 , 3.2 , 3.3 , 3.4),(4.1 , 4.2 , 4.3 , 4.4)]
    print(data)
    test.insterData("testTabelle", data)
    test.end()

#Testen des einlesens von CSV Dateien
def csvtest():
    name = "csvtest"
    csvtest = Datenbank(name)
    file = "csvtest"
    csvtest.importcsv(file)
    parameter = ["spalte2","spalte4"]
    value = csvtest.value(name,"spalte1","8","spalte2")
    print(value)
    value = csvtest.value(name,"spalte1","8","spalte3")
    print(value)
    value = csvtest.value(name,"spalte1","8","spalte4")
    print(value)
    value = csvtest.value(name,"spalte1","13","spalte4")
    print(value)

    #csvtest.printcsv(file , "ausgabeDatei")
    csvtest.end()

def valuetest():
    print(csvtest.value(file, "spalte1" , 12, "spalte2"))
    print(csvtest.value(file, "spalte4" , 44, "spalte1"))
    print(csvtest.value(file, "spalte2" , 23, "spalte3"))

def testCheck():
    name = "testcheck"
    test = Datenbank(name)
    test.check()
    test.end()
