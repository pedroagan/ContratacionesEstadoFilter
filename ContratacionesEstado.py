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

from Licitacion import Licitacion
import Utils

#  Constants
MAX_FILES_DOWNLOAD = 10
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
            print("Download file '%s'" % (file_path))

            # parse an xml file by name
            tree = ET.parse(file_path)  
            root = tree.getroot()

            # all item attributes
            for elem in root:        
                if(elem.tag == ELEM_TAG_LINK):
                    href = elem.attrib['href']
                    rel = elem.attrib['rel']
                    if(rel == "next"):
                        download_files(href, count+1)
        else:
            print("ERROR! Number of attempts to download file '%s' reached" % (file_path))
    else:
        print("Download process finished")

def process_file(file, tender_list, filter):
    print("Start processing -> %s" % (file))
    # Counter
    elem_read = 0
    # parse an xml file by name
    mydoc = minidom.parse(file)
    entries = mydoc.getElementsByTagName('entry')

    # all item attributes
    for entry in entries:

        licitacion = Licitacion()

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
        #print(summary)
        #print(summary_list)

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
        #print(key)
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
    worksheet = workbook.add_worksheet()

    number = workbook.add_format({'num_format': '#,##0'})

    row = 0

    # Header
    worksheet.write(row, 0, '#fecha')
    worksheet.write(row, 1, '#interesa')
    worksheet.write(row, 2, '#expediente')
    worksheet.write(row, 3, '#title')
    #worksheet.write(row, 4, '#administracion')
    worksheet.write(row, 4, '#organo')
    worksheet.write(row, 5, '#estado')
    worksheet.write(row, 6, '#importe')
    worksheet.write(row, 7, '#deadline')
    worksheet.write(row, 8, '#email')
    worksheet.write(row, 9, '#details')
    row += 1

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
            print("ERROR! Cannot convert to float -> %s" % (licitacion.importe))

        worksheet.write(row, 0, date)
        worksheet.write(row, 1, licitacion.interesa)
        worksheet.write(row, 2, licitacion.expediente)
        worksheet.write(row, 3, licitacion.title)
        #worksheet.write(row, 4, licitacion.administracion)
        worksheet.write(row, 4, licitacion.organo)
        worksheet.write(row, 5, licitacion.estado)
        worksheet.write(row, 6, importe, number)
        if(licitacion.deadline != None):
            date = licitacion.deadline.strftime("%Y-%m-%d")
        else:
            date = ""
        worksheet.write(row, 7, date)
        worksheet.write(row, 8, licitacion.email)
        worksheet.write(row, 9, licitacion.details)

        if(len(licitacion.interesa) == 0):
            filtered += 1

        row += 1

    workbook.close()

    return filtered

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
                    print("Filter added for '%s' = %s" % (filter[0], filter[1]))
                else :
                    print("ERROR! Invalid key in filters config file : %s" % (filter[0]) )
            else:
                print("ERROR! Invalid line in filters config file : %s" % (line) )
    
    return filters

def main(options):

    if(options.nodownload):
        print("WARN! Files are not going to be downloaded")
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
    filtered = output_xlsx_file(tender_list, filters)

    # Move files to archive after processing
    if(options.noarchive):
        print("WARN! Files are not going to be archived")
    else:
        # Remove first input file
        clean_start_file()
        files = get_list_of_files(PATH_INPUT)
        for file_input in files:
            file_archive = PATH_ARCHIVE + file_input.split("/")[-1]
            os.rename(file_input, file_archive)

    print("\nResults:")
    print("  - Elements read    : %d" % (elem_read))
    print("  - Elements stored  : %d" % (len(tender_list)))
    print("  - Interesa         : %d" % (filtered))
    print("\n")
    
    
##
# Main method
#
if __name__ == '__main__':

	# Check arguments
    parser = OptionParser(usage="%prog: [options]")
    parser.add_option("--nodownload", dest="nodownload", default=False, action="store_true")
    parser.add_option("--noarchive", dest="noarchive", default=False, action="store_true")
    parser.add_option("--reset", dest="reset", default=False, action="store_true")
    parser.add_option("--filter", dest="filter", default="./filters.conf")
    (options, args) = parser.parse_args()

    # Laun main method
    main(options)
