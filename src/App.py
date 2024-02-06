# -*- coding: utf-8 -*-

import os
import time
from os import listdir
from os.path import isfile, join
from xml.dom import minidom
from lxml import etree
import xml.etree.ElementTree as ET
import datetime
from datetime import datetime
from optparse import OptionParser
import xlsxwriter
import logging
import shutil

import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from optparse import OptionParser
import configparser
import pandas as pd
import numpy as np
import time
from datetime import datetime
import re

import gc

import Licitacion
import Utils

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-7s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
_logger = logging.getLogger("contrataciones_estado")

#  Constants
MAX_FILES_DOWNLOAD = 100
HTTP_REF_INIT = "https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"
ELEM_TAG_LINK = "{http://www.w3.org/2005/Atom}link"

PATH_INPUT = "./inputs/"
PATH_OUTPUT = "./outputs/"
PATH_ARCHIVE = "./archive/"

FILE_HEADER = "#fecha;#interesa;#expediente;#titulo;#administracion;#organo;#estado;#importe;#deadline;#detalles;"

def download_files(http_ref, count):
    # Manage command
    command = "wget " + http_ref + " "
    command += "-P " + PATH_INPUT
    command += " > /dev/null 2>&1"

    # Obtain file info
    file = http_ref.split("/")[-1]
    file_path = PATH_INPUT + file

    # Check if file has been processed
    files_archive = get_list_of_files(PATH_ARCHIVE)
    file_downloaded = False
    for file_archive in files_archive:
        if(file in file_archive):
            file_downloaded = True

    if((not file_downloaded) and (count < MAX_FILES_DOWNLOAD)):
            
        attemp = 0
        exists = False
        while((not exists) and attemp < 5):
            # Download file
            os.system(command)

            exists = os.path.isfile(file_path)
            attemp += 1

        if(exists):
            # Read the XML and process it
            _logger.info("Download file (%d/%d)'%s'" % (count+1, MAX_FILES_DOWNLOAD, file_path))

            next_links = []

            # parse an xml file by name
            with open(file_path, 'r') as file:
                tree = ET.parse(file)  
                root = tree.getroot()

                # all item attributes
                for elem in root:
                    if(elem.tag == ELEM_TAG_LINK):
                        href = elem.attrib['href']
                        rel = elem.attrib['rel']

                        if(rel == "next"):
                            next_links.append({'count': count+1, 'href': href})
                            #download_files(href, count+1)

                root.clear()
                root = None

            gc.collect()

            for link in next_links:
                download_files(link['href'], link['count'])

        else:
            _logger.error("ERROR! Number of attempts to download file '%s' reached" % (file_path))
    else:
        _logger.info("Download process finished")

def process_file(file, tender_list, filter):
    _logger.info("Start processing -> %s" % (file))
    # Counter
    elem_read = 0
    # parse an xml file by name
    mydoc = minidom.parse(file)
    entries = mydoc.getElementsByTagName('entry')

    # all item attributes
    for entry in entries:

        licitacion = Licitacion.Licitacion()

        # title
        list = entry.getElementsByTagName('title')
        aux = " ".join(t.nodeValue for t in list[0].childNodes if t.nodeType == t.TEXT_NODE)
        licitacion.title = aux.replace('\n',' ').replace(';',',')

        # updated
        list = entry.getElementsByTagName('updated')
        aux = " ".join(t.nodeValue for t in list[0].childNodes if t.nodeType == t.TEXT_NODE)
        valid, licitacion.fecha = Utils.string_to_datetime(aux.split("T")[0])

        # summary
        list = entry.getElementsByTagName('summary')
        aux = " ".join(t.nodeValue for t in list[0].childNodes if t.nodeType == t.TEXT_NODE)
        summary_list = aux.split('; ')

        if(len(summary_list) > 0) and (len(summary_list[0].split(': ')) > 1):
            licitacion.expediente = summary_list[0].split(': ')[1]

        if(len(summary_list) > 1) and (len(summary_list[1].split(': ')) > 1):
            licitacion.organo = summary_list[1].split(': ')[1]

        if(len(summary_list) > 2) and (len(summary_list[2].split(': ')) > 1):
            aux = summary_list[2].split(': ')[1].split(' ')[0]
            licitacion.importe = aux

        if(len(summary_list) > 3) and (len(summary_list[3].split(': ')) > 1):
            licitacion.estado = summary_list[3].split(': ')[1]

        #details
        list = entry.getElementsByTagName('link')
        for link in list:
            licitacion.details = link.attributes['href'].value
            break
        
        #deadline
        list = entry.getElementsByTagName('cac-place-ext:ContractFolderStatus')
        for info in list:
            list_tendering = info.getElementsByTagName('cac:TenderingProcess')
            for info_tendering in list_tendering:
                
                list_deadline = info_tendering.getElementsByTagName('cac:TenderSubmissionDeadlinePeriod')
                for info_deadline in list_deadline:

                    list_endate = info_deadline.getElementsByTagName('cbc:EndDate')
                    if(len(list_endate) > 0):
                        aux = " ".join(t.nodeValue for t in list_endate[0].childNodes if t.nodeType == t.TEXT_NODE)
                        valid, licitacion.deadline = Utils.string_to_datetime(aux)

        #email
        list = entry.getElementsByTagName('cac-place-ext:ContractFolderStatus')
        for info in list:
            list_contracting = info.getElementsByTagName('cac-place-ext:LocatedContractingParty')
            for info_contracting in list_contracting:
                list_party = info_contracting.getElementsByTagName('cac:Party')
                for info_party in list_party:
                    list_contact = info_party.getElementsByTagName('cac:Contact')
                    for info_contact in list_contact:
                        list_email = info_contact.getElementsByTagName('cbc:ElectronicMail')
                        licitacion.email = " ".join(t.nodeValue for t in list_email[0].childNodes if t.nodeType == t.TEXT_NODE)

        # Store the information
        key = licitacion.expediente + '_' + licitacion.organo
        if(key in tender_list.keys()):
            if(licitacion.fecha >= tender_list[key].fecha):
                tender_list[key] = licitacion
        else:
            tender_list[key] = licitacion
        
        elem_read += 1

    gc.collect()
    
    return elem_read

def clean_input_files():
    # Remove input files
    file = PATH_INPUT + HTTP_REF_INIT.split("/")[-1]
    files = get_list_of_files(PATH_INPUT)
    for file_input in files:
        file_archive = PATH_ARCHIVE + file_input.split("/")[-1]
        os.remove(file_input)

def clean_archive_files():
    # Remove archive files
    files = get_list_of_files(PATH_ARCHIVE)
    for file_archive in files:
        os.remove(file_archive)

def clean_start_file():
    # Remove first input file
    file = PATH_INPUT + HTTP_REF_INIT.split("/")[-1]
    exists = os.path.isfile(file)
    if(exists):
        os.remove(file)

def get_list_of_files(path):
    files = []
    files_dir = [f for f in listdir(path) if isfile(join(path, f))]
    for file in files_dir:
        file_path = path + file
        files.append(file_path)

    return files

def output_csv_file(tender_list, filters):
    filtered = 0
    # Write output file
    output_filename = PATH_OUTPUT + time.strftime("%Y.%m.%d-%H.%M.%S") + ".csv"
    exists = os.path.isfile(output_filename)
    if(exists):
        os.remove(output_filename)
    foutput = open(output_filename, "w+")
    foutput.write(FILE_HEADER + "\n")

    for key in tender_list.keys():
        licitacion = tender_list[key]
        licitacion.filter(filters)
        line = licitacion.info()
        foutput.write(line)
        if(len(licitacion.interesa) == 0):
            filtered += 1
        
    foutput.close()

    return filtered

def output_xlsx_file(tender_list, filters):
    filtered = 0
    # Write output file
    output_filename = PATH_OUTPUT + time.strftime("%Y.%m.%d-%H.%M.%S") + ".xlsx"
    exists = os.path.isfile(output_filename)
    if(exists):
        os.remove(output_filename)

    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook(output_filename)
    worksheet_interesa = workbook.add_worksheet("Interesa")
    worksheet_no_interesa = workbook.add_worksheet("NO Interesa")

    number = workbook.add_format({'num_format': '#,##0'})

    row_interesa = 0
    row_no_interesa = 0

    # Header Interesa
    worksheet_interesa.write(row_interesa, 0, '#fecha')
    worksheet_interesa.set_column(0, 0, 10)
    worksheet_interesa.write(row_interesa, 1, '#interesa')
    worksheet_interesa.set_column(1, 1, 10)
    worksheet_interesa.write(row_interesa, 2, '#expediente')
    worksheet_interesa.set_column(2, 2, 15)
    worksheet_interesa.write(row_interesa, 3, '#title')
    worksheet_interesa.set_column(3, 3, 50)
    worksheet_interesa.write(row_interesa, 4, '#organo')
    worksheet_interesa.set_column(4, 4, 30)
    worksheet_interesa.write(row_interesa, 5, '#estado')
    worksheet_interesa.set_column(5, 5, 10)
    worksheet_interesa.write(row_interesa, 6, '#importe')
    worksheet_interesa.set_column(6, 6, 10)
    worksheet_interesa.write(row_interesa, 7, '#deadline')
    worksheet_interesa.set_column(7, 7, 10)
    worksheet_interesa.write(row_interesa, 8, '#email')
    worksheet_interesa.set_column(8, 8, 20)
    worksheet_interesa.write(row_interesa, 9, '#details')
    worksheet_interesa.set_column(9, 9, 25)
    worksheet_interesa.write(row_interesa, 10, '#filter')
    worksheet_interesa.set_column(10, 10, 10)
    row_interesa += 1

    # Header NO interesa
    worksheet_no_interesa.write(row_interesa, 0, '#fecha')
    worksheet_no_interesa.write(row_interesa, 1, '#interesa')
    worksheet_no_interesa.write(row_interesa, 2, '#expediente')
    worksheet_no_interesa.write(row_interesa, 3, '#title')
    worksheet_no_interesa.write(row_interesa, 4, '#organo')
    worksheet_no_interesa.write(row_interesa, 5, '#estado')
    worksheet_no_interesa.write(row_interesa, 6, '#importe')
    worksheet_no_interesa.write(row_interesa, 7, '#deadline')
    worksheet_no_interesa.write(row_interesa, 8, '#email')
    worksheet_no_interesa.write(row_interesa, 9, '#details')
    worksheet_no_interesa.write(row_interesa, 10, '#filter')
    row_no_interesa += 1

    for key in tender_list.keys():
        licitacion = tender_list[key]
        licitacion.filter(filters)

        date = ""
        if(licitacion.fecha != None):
            date = licitacion.fecha.strftime("%Y-%m-%d")
        else:
            date = ""

        importe = 0.0
        try:
            importe = float(licitacion.importe)

        except:
            _logger.error("ERROR! Cannot convert to float -> %s" % (licitacion.importe))

        if(len(licitacion.interesa) == 0):
            worksheet_interesa.write(row_interesa, 0, date)
            worksheet_interesa.write(row_interesa, 1, licitacion.interesa)
            worksheet_interesa.write(row_interesa, 2, licitacion.expediente)
            worksheet_interesa.write(row_interesa, 3, licitacion.title)
            #worksheet_interesa.write(row, 4, licitacion.administracion)
            worksheet_interesa.write(row_interesa, 4, licitacion.organo)
            worksheet_interesa.write(row_interesa, 5, licitacion.estado)
            worksheet_interesa.write(row_interesa, 6, importe, number)
            if(licitacion.deadline != None):
                date = licitacion.deadline.strftime("%Y-%m-%d")
            else:
                date = ""
            worksheet_interesa.write(row_interesa, 7, date)
            worksheet_interesa.write(row_interesa, 8, licitacion.email)
            worksheet_interesa.write(row_interesa, 9, licitacion.details)
            worksheet_interesa.write(row_interesa, 10, licitacion.filter_applied)
        
            filtered += 1
            row_interesa += 1
        else:
            worksheet_no_interesa.write(row_no_interesa, 0, date)
            worksheet_no_interesa.write(row_no_interesa, 1, licitacion.interesa)
            worksheet_no_interesa.write(row_no_interesa, 2, licitacion.expediente)
            worksheet_no_interesa.write(row_no_interesa, 3, licitacion.title)
            #worksheet_no_interesa.write(row_no_interesa, 4, licitacion.administracion)
            worksheet_no_interesa.write(row_no_interesa, 4, licitacion.organo)
            worksheet_no_interesa.write(row_no_interesa, 5, licitacion.estado)
            worksheet_no_interesa.write(row_no_interesa, 6, importe, number)
            if(licitacion.deadline != None):
                date = licitacion.deadline.strftime("%Y-%m-%d")
            else:
                date = ""
            worksheet_no_interesa.write(row_no_interesa, 7, date)
            worksheet_no_interesa.write(row_no_interesa, 8, licitacion.email)
            worksheet_no_interesa.write(row_no_interesa, 9, licitacion.details)
            worksheet_no_interesa.write(row_no_interesa, 10, licitacion.filter_applied)
        
            row_no_interesa += 1

    workbook.close()

    return filtered, output_filename

def check_filters(filters_file):
    keys = ['administracion', 'organo', 'email', 'title']
    filters = {}
    for key in keys:
        filters[key] = []

    if os.path.exists(filters_file):
        f = open(filters_file)
        lines = f.readlines()

        for line in lines:
            filter = line.strip().split('=')
            if (len(filter) == 2):
                
                if(filter[0] in keys) :
                    filters[filter[0]].append(filter[1])
                    _logger.info("Filter added for '%s' = %s" % (filter[0], filter[1]))
                else :
                    _logger.error("ERROR! Invalid key in filters config file : %s" % (filter[0]) )
            else:
                _logger.error("ERROR! Invalid line in filters config file : %s" % (line) )
    
    return filters

def main(options):

    # Load configuration file
    config = configparser.ConfigParser()
    config.read(options.config)

    if(options.nodownload):
        _logger.warn("WARN! Files are not going to be downloaded")
    else:
        # Generate directories (if it does not exists)
        if not os.path.exists(PATH_INPUT):
            os.makedirs(PATH_INPUT)

        if not os.path.exists(PATH_OUTPUT):
            os.makedirs(PATH_OUTPUT)

        if not os.path.exists(PATH_ARCHIVE):
            os.makedirs(PATH_ARCHIVE)

        # Clean archive files
        if options.reset:
            clean_archive_files()

        # Clean all input files
        clean_input_files()
        
        # Download first file
        download_files(HTTP_REF_INIT, 0)

    # Check filters
    filters = check_filters(options.filter)

    # Process files downloaded
    elem_read = 0
    filtered = 0
    tender_list = {}
    files = get_list_of_files(PATH_INPUT)
    for file in files:
        elem_read += process_file(file, tender_list, filters)

    #filtered = output_csv_file(tender_list)
    filtered, xlsx_filename = output_xlsx_file(tender_list, filters)

    if(config['EMAIL_CONF']['EMAIL_ENABLED']):
        send_email(config, xlsx_filename)

    _logger.info("\nResults:")
    _logger.info("  - Elements read    : %d" % (elem_read))
    _logger.info("  - Elements stored  : %d" % (len(tender_list)))
    _logger.info("  - Interesa         : %d" % (filtered))
    _logger.info("\n")

    # Move files to archive after processing
    try:
        if(options.noarchive):
            _logger.warn("WARN! Files are not going to be archived")
        else:
            # Remove first input file
            clean_start_file()
            files = get_list_of_files(PATH_INPUT)
            for file_input in files:
                file_archive = PATH_ARCHIVE + file_input.split("/")[-1]
                _logger.info(f"Move file from {file_input} to {file_archive}")
                #os.rename(file_input, file_archive)
                shutil.move(file_input, file_archive)
    except Exception as ex:
        _logger.error("ERROR! File cannot archived : " + str(ex))

    

def send_email(config, attachment):
    email_server = config['EMAIL_CONF']['EMAIL_SERVER']
    email_port = int(config['EMAIL_CONF']['EMAIL_PORT'])
    email_from = config['EMAIL_CONF']['EMAIL_FROM']
    email_password = config['EMAIL_CONF']['EMAIL_PASSWD']
    email_to = config['EMAIL_CONF']['EMAIL_TO']

    email_subject = config['EMAIL_MSG']['EMAIL_SUBJECT']

    _logger.info("Send email to '%s'" % (email_to))

    if(check_email(email_to)):
        _logger.info("Connect to '%s:%d'" % (email_server, email_port))

        s = smtplib.SMTP(email_server, email_port)
        s.ehlo('mylowercasehost')
        s.starttls()
        s.ehlo('mylowercasehost')

        s.login(email_from, email_password)

        text_email = ""

        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = email_subject

        # Add body to email
        msg.attach(MIMEText(text_email, "plain"))

        # Add attachment to message and convert message to string
        part = adjuntar_archivo_xlsx(attachment)
        if(part):
            msg.attach(part)

        s.sendmail(email_from, email_to, msg.as_string().encode('utf-8'))

        _logger.info("Email enviado a '%s'" % (email_to))
    else:
        _logger.error("ERROR! Email invalido '%s'" % (email_to))


def adjuntar_archivo_xlsx(attachment_filename):
    part = None

    if(len(attachment_filename) > 0):
        # Open PDF file in binary mode
        #with open(attachment, "rb") as attachment:
        #    # Add file as application/octet-stream
        #    # Email client can usually download this automatically as attachment
        #    part = MIMEBase("application", "octet-stream")
        #    part.set_payload(attachment.read())

        # Open PDF file in binary mode
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(attachment_filename, "rb").read())
        encoders.encode_base64(part)
        # Add header as key/value pair to attachment part
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {os.path.basename(attachment_filename)}",
        )

    return part


def check_email(email):
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,4})+$'
    if(re.search(regex,email)):
        return True
    else:
        return False

##
# Main method
#
if __name__ == '__main__':

	# Check arguments
    parser = OptionParser(usage="%prog: [options]")
    parser.add_option("--nodownload", dest="nodownload", default=False, action="store_true", help='No Download Data')
    parser.add_option("--noarchive", dest="noarchive", default=False, action="store_true", help='No archive the data downloaded')
    parser.add_option("--reset", dest="reset", default=False, action="store_true", help='Reset the search')
    parser.add_option("--filter", dest="filter", default="./filters.conf", help='Filters search')
    parser.add_option("--config", dest="config", default="./config.ini", type="string", help='Configuration File')
    (options, args) = parser.parse_args()

    # Laun main method
    main(options)
