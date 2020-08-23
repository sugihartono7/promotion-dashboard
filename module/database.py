'''
@sugihartono
class for postgresql 
for flexible usage

'''

import psycopg2

class Database:

    def connect(self):
        return psycopg2.connect(host="172.16.9.118", port="5533", user="yogya", password="secret", dbname="yopromo")


