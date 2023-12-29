
import datetime
from datetime import datetime
from time import gmtime, strftime
import logging

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-7s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
_logger = logging.getLogger("contrataciones_estado")

def string_to_datetime(t):
   valid = False
   data = None

   # Check format '%Y-%m-%d'
   if(not valid):
      try:
         t_FMT = '%Y-%m-%d'
         data = datetime.strptime(t, t_FMT)
         valid = True
      except ValueError:
         data = None

   # Check format '%Y-%m-%dT%H'
   if(not valid):
      try:
         t_FMT = '%Y-%m-%dT%H'
         data = datetime.strptime(t, t_FMT)
         valid = True
      except ValueError:
         data = None

   # Check format '%Y-%m-%dT%H:%M'
   if(not valid):
      try:
         t_FMT = '%Y-%m-%dT%H:%M'
         data = datetime.strptime(t, t_FMT)
         valid = True
      except ValueError:
         data = None

   # Check format '%Y-%m-%dT%H:%M:%S'
   if(not valid):
      try:
         t_FMT = '%Y-%m-%dT%H:%M:%S'
         data = datetime.strptime(t, t_FMT)
         valid = True
      except ValueError:
         data = None

   return valid, data