
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

    def filter(self):
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
            if('defensa' in self.administracion.lower()):
                filtered = True

            if('interior' in self.administracion.lower()):
                filtered = True

            if('defensa' in self.organo.lower()):
                filtered = True

            if('interior' in self.organo.lower()):
                filtered = True
        #else:
        #    print("WARN! 'Administracion' of Exp '%s' is NULL (%s)" % (self.expediente, self.administracion) )

        if(len(self.email) > 0):
            if('mde.es' in self.email.lower()):
                filtered = True

            if('interior.es' in self.email.lower()):
                filtered = True

        if(len(self.title) > 0):
            if('enaire' in self.title.lower()):
                filtered = True

            if('cpd' in self.title.lower()):
                filtered = True

            if('cctv' in self.title.lower()):
                filtered = True

            if('comunicaciones' in self.title.lower()):
                filtered = True

            if('ciber' in self.title.lower()):
                filtered = True

            if('incibe' in self.title.lower()):
                filtered = True

            if('software' in self.title.lower()):
                filtered = True

            if('sw' in self.title.lower()):
                filtered = True

            if('hardware' in self.title.lower()):
                filtered = True

            if('hw' in self.title.lower()):
                filtered = True

            if('polic' in self.title.lower()):
                filtered = True

            if('scada' in self.title.lower()):
                filtered = True

            if('virtual' in self.title.lower()):
                filtered = True
        else:
            print("WARN! 'Title' of Exp '%s' is NULL (%s)" % (self.expediente, self.title) )

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