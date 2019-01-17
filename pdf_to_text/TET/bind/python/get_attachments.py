#!/usr/bin/python
# Id: extractor.rb,v 1.1 2011/11/29 15:43:26 rjs Exp 
#
# PDF text extractor which also searches PDF file attachments.
#

from sys import argv, exc_info, version_info
from traceback import print_tb, print_exc
from PDFlib.TET import *

#Global option list.
globaloptlist = "searchpath={{../data} " +   "{../../../resource/cmap}}"

# Document specific option list.
docoptlist = ""

# Page-specific option list.
pageoptlist = "granularity=page"

# Separator to emit after each chunk of text. This depends on the
# application's needs for granularity=word a space character may be
# useful.
separator = "\n"

# Extract text from a document for which a tet->handle is already available.
# @param tet
#            The tet->object
# @param doc
#            A valid tet->document handle
# @param outfp
#            Output file handle

def extract_text(tet, doc, outfp):
      
      # Get number of pages in the document.

      n_pages = tet.pcos_get_number(doc, "length:pages")

      # loop over pages 
      for pageno in range(1, int(n_pages)+1):
          page = tet.open_page(doc, pageno, pageoptlist)

          if (page == -1):
            print("Error ['%d] in %s() on page %d: %s\n" % (tet.get_errnum(), tet.get_apiname(), pageno, tet.get_errmsg()))
            continue # try next page 


          # Retrieve all text fragments This loop is actually not required
          # for granularity=page, but must be used for other granularities.
          text = tet.get_text(page)
          while (text != None):
              outfp.write(text) # print the retrieved text

              # print a separator between chunks of text 
              outfp.write(separator) 
              text = tet.get_text(page)


          if (tet.get_errnum() != 0):
            print("Error ['%d] in %s() on page %d: %s\n" % (tet.get_errnum(), tet.get_apiname(), pageno, tet.get_errmsg()))
          
          tet.close_page(page)


  
  # Open a named physical or virtual file, extract the text from it, search
  # for document or page attachments, and process these recursively. Either
  # filename must be supplied for physical files, or data+length from which a
  # virtual file will be created. The caller cannot create the PVF file since
  # we create a new tet.object here in case an exception happens with the
  # embedded document - the caller can happily continue with his tet.object
  # even in case of an exception here.
  # 
  # @param outfp
  # @param filename
  # @param realname
  # @param data
  # 
  # @return 0 if successful, otherwise a non-null code to be used as exit
  #         status
  
def process_document(outfp, filename, realname, data):
    retval = 0
    try:
        pvfname = "/pvf/attachment"
       
        tet = TET()

        # Construct a PVF file if data instead of a filename was provided
        if (filename == None):
            tet.create_pvf(pvfname, data, "")
            filename = pvfname

        tet.set_option(globaloptlist)

        doc = tet.open_document(filename, docoptlist)

        if (doc == -1):
          print("Error [%d] in %s (source : attachment '%s'): %s\n" % (tet.get_errnum(), tet.get_apiname(), realname, tet.get_errmsg()))

          retval = 5
        else:
          process_document_single(outfp, tet, doc)


        # If there was no PVF file deleting it won't do any harm
        
        tet.delete_pvf(pvfname)

    except TETException:
        if pageno == 0:
            stderr.write("Error %d in %s(): %s\n" % (tet.get_errnum(), tet.get_apiname(), tet.get_errmsg()))
        else:
            stderr.write("Error %d in %s() on page %d: %s\n" %
                (tet.get_errnum(), tet.get_apiname(), pageno,
                tet.get_errmsg()))
            
        print_tb(exc_info()[2])

    except Exception:
        print ("Exception occurred: %s" % (exc_info()[0]))
        print_exc()
        
    finally:
        tet.delete()        


  # Process a single file.
  # 
  # @param outfp Output stream for messages
  # @param tet.The tet.object
  # @param doc The tet.document handle
  
def process_document_single(outfp, tet, doc):

    #-------------------- Extract the document's own page contents
    extract_text(tet, doc, outfp)

    #-------------------- Process all document-level file attachments

    # Get the number of document-level file attachments.
    filecount = tet.pcos_get_number(doc, "length:names/EmbeddedFiles")

    for filen in range(0, int(filecount) + 1):
        # fetch the name of the file attachment check for Unicode file
        # name (a PDF 1.7 feature)

        objtype = tet.pcos_get_string(doc, "type:names/EmbeddedFiles[%d]/UF" % filen)

        if (objtype == "string"):
            attname = tet.pcos_get_string(doc,
                "names/EmbeddedFiles[%d]/UF" %filen)
        else:
            objtype = tet.pcos_get_string(doc, "type:names/EmbeddedFiles[%d]/F" %filen)

            if (objtype == "string"):

                attname = tet.pcos_get_string(doc, "names/EmbeddedFiles[%d]/F" %filen)
            else:

                attname = "(unnamed)"

        # fetch the contents of the file attachment and process it
        objtype = tet.pcos_get_string(doc, "type:names/EmbeddedFiles[%d]/EF/F" %filen)

        if (objtype == "stream"):
            outfp.write("----- File attachment '%s':\n" %attname)
            attdata = tet.pcos_get_stream(doc, "",
                    "names/EmbeddedFiles[%d]/EF/F" %filen)

            process_document(outfp, None, attname, attdata)
            outfp.write("----- End file attachment '%s'\n" %attname)


    # -------------------- Process all page-level file attachments

    pagecount = tet.pcos_get_number(doc, "length:pages")

    # Check all pages for annotations of type FileAttachment
    
    for page in range(0, int(pagecount) - 1):      
        annotcount = tet.pcos_get_number(doc, "length:pages[%d]/Annots" %page)

        for annot in range(0, int(annotcount) - 1):      
            val = tet.pcos_get_string(doc, "pages[%d]/Annots[%d]/Subtype" % (page, annot))

            attname = "page %d, annotation %d" % (page + 1), (annot + 1)
            if (val == "FileAttachment"):
                attpath = "pages[%d]/Annots[%d]/FS/EF/F" % (page, annot)
                # fetch the contents of the attachment and process it
                
                objtype = tet.pcos_get_string(doc, "type:%s" % attpath)

                if (objtype == "stream"):
                    outfp.write("----- Page level attachment '%s':\n" % attname)
                    attdata = tet.pcos_get_stream(doc, "", attpath)
                    process_document(outfp, None, attname, attdata)
                    outfp.write("----- End page level attachment '%s':\n" % attname)


    tet.close_document(doc)

try:
    if len(argv) != 3:
      raise "usage: get_attachments.py <infilename> <outfilename>"

    if (version_info[0] < 3):
        outfp = open(argv[2], 'w')
    else:
        outfp = open(argv[2], 'w', 2, 'utf-8')

    process_document(outfp, argv[1], argv[1], None)

except Exception:
    print("Exception occurred: %s" % (exc_info()[0]))
    print_exc()    

    