import sys

import mysql.connector
from mysql.connector import errorcode

TABLES = {}

TABLES["Ap"] = (
"CREATE TABLE Ap ("
"  apRadioMac varchar(17),"
"  apName varchar(255),"
"  apEthMac varchar(255),"
"  rfTag varchar(255),"
"  siteTag varchar(255),"
"  model varchar(255),"
"  wlcName varchar(255),"
"  PRIMARY KEY (apRadioMac)"
"  );"
)

TABLES["Slot"] = (
"CREATE TABLE Slot ("
"  apRadioMac varchar(17),"
"  slot int,"
"  operState varchar(255),"
"  radioMode varchar(255),"
"  band varchar(255),"
"  channel int,"
"  power int,"
"  UNIQUE KEY UC_Slot (apRadioMac,slot)"
"  );"
)

TABLES["SlotMetrics"] = (
"CREATE TABLE SlotMetrics ("
"  apRadioMac varchar(17),"
"  slot int,"
"  stations int,"
"  cca int,"
"  UNIQUE KEY UC_SlotMetrics (apRadioMac,slot)"
"  );"
)


class SetupDB():


    def __init__(self):

        self.mysql_host = input("MySQL host (ENTER=127.0.0.1):")
        self.mysql_user = input("MySQL username:")
        self.mysql_pass = input("MySQL password:")
        self.mysql_db = input("Database Name:")

        if self.mysql_host == "": self.mysql_host = "127.0.0.1"

        self.db = mysql.connector.connect(host=self.mysql_host, user=self.mysql_user, password=self.mysql_pass)
        self.cursor = self.db.cursor()

        self.setup_db()
        self.setup_tables()
        

    def setup_db(self):

        print("\nWorking ..")
        try:
            self.cursor.execute(f"DROP DATABASE {self.mysql_db}")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DB_DROP_EXISTS:
                print(f"Not deleting - database '{self.mysql_db}' does not exist")
        else:
            print(f"Deleted database '{self.mysql_db}'")

        try:
            self.cursor.execute(f"CREATE DATABASE {self.mysql_db}")
        except mysql.connector.Error as err:
            print(f"Error creating database '{self.mysql_db}'\n>>{err}")
            sys.exit()
        else:
            print(f"Created new database '{self.mysql_db}'")

        try:
            self.cursor.execute(f"USE {self.mysql_db}")
        except mysql.connector.Error as err:
            print(f"Error accessing database '{self.mysql_db}'\n>>{err}")
            sys.exit()


    def setup_tables(self):

        count = 0
        for table_name in TABLES:
            table_description = TABLES[table_name]
            try:
                self.cursor.execute(table_description)
            except mysql.connector.Error as err:
                print(f"Error creating table '{table_name}' - skipping\n>>{err}")
            else:
                print(f"Created table {table_name}")
                count += 1

        print(f"\nCreated {count} out of {len(TABLES)} tables")


if __name__ == "__main__":

    SetupDB()