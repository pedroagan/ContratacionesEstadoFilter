
import datetime
from datetime import datetime
from time import gmtime, strftime
import re
import logging

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-7s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
_logger = logging.getLogger("contrataciones_estado")

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
        self.filter_applied = ""

    def filter(self, filters):
        no_interesa = False
        filter_applied = ""
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
                    filter_applied = filter

        if(len(self.organo) > 0):
            filters_organo = filters['organo']
            for filter in filters_organo:
                if filter in self.organo.lower():
                    filtered = True
                    filter_applied = filter

        if(len(self.email) > 0):
            filters_email = filters['email']
            for filter in filters_email:
                if filter in self.email.lower():
                    filtered = True
                    filter_applied = filter

        if(len(self.title) > 0):
            filters_title = filters['title']
            for filter in filters_title:
                if filter in self.title.lower():
                    filtered = True
                    filter_applied = filter

        if(no_interesa or not filtered):
            self.interesa = "NO"

        self.filter_applied = filter_applied


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