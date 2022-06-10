
import datetime
from datetime import datetime
from time import gmtime, strftime
import re

class Licitacion(object):

    def __init__(self):
        self.fecha = None
        self.estado = ""
        self.title = ""
        self.details = ""
        self.importe = ""
        self.administracion = ""
        self.organo = ""
        self.expediente = ""
        self.interesa = ""
        self.email = ""
        self.deadline = None

    def filter(self, filters):
        no_interesa = False
        filtered = False
        if(self.estado == 'ADJ'):
            no_interesa = True
        elif(self.estado == 'EV'):
            no_interesa = True
        elif(self.estado == 'PRE'):
            pass
        elif(self.estado == 'PUB'):
            pass
        elif(self.estado == 'RES'):
            no_interesa = True

        if((not self.deadline) or (self.deadline <= datetime.today())):
            no_interesa = True

        if(len(self.administracion) > 0):
            filters_admin = filters['administracion']
            for filter in filters_admin:
                if filter in self.administracion.lower():
                    filtered = True

        if(len(self.organo) > 0):
            filters_organo = filters['organo']
            for filter in filters_organo:
                if filter in self.organo.lower():
                    filtered = True

        if(len(self.email) > 0):
            filters_email = filters['email']
            for filter in filters_email:
                if filter in self.email.lower():
                    filtered = True

        if(len(self.title) > 0):
            filters_title = filters['title']
            for filter in filters_title:
                if filter in self.title.lower():
                    filtered = True

        if(no_interesa or not filtered):
            self.interesa = "NO"


    def info(self):
        fecha = ""
        if(self.fecha != None):
            fecha = self.fecha.strftime("%d-%m-%Y")
        deadline = ""
        if(self.deadline != None):
            deadline = self.deadline.strftime("%d-%m-%Y")

        line = "%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;\n" % (fecha, self.interesa, self.expediente, 
            self.title, self.administracion, self.organo, self.estado, self.importe, deadline, self.details)
        return line