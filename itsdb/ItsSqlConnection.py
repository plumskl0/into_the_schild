# -*- coding: utf-8 -*-

import mysql.connector as mysql

mydb = mysql.connect(
        host="192.168.0.19",
        user="root",
        passwd="1212"
)

mycursor = mydb.cursor()

mycursor.execute("SHOW DATABASES")

for x in mycursor:
    print(x)
