#!/usr/bin/python
# Resource-based image extractor based on PDFlib TET
#
# $Id: image_resources.py,v 1.12 2015/08/17 12:18:16 rjs Exp $

from sys import exc_info, argv, stdout
from traceback import print_tb, print_exc
from PDFlib.TET import *

# global option list */
globaloptlist = "searchpath={{../data}}"

# document-specific option list */
docoptlist = ""

# page-specific option list */
pageoptlist = ""

# here you can insert basic image extract options (more below) */
baseimageoptlist = ""

# Print the following information for each image:
# - pCOS id (required for indexing the images[] array)
# - pixel size of the underlying PDF Image XObject
# - number of components, bits per component, and colorspace
# - mergetype if different from "normal", i.e. "artificial" (=merged)
#   or "consumed"
# - "stencilmask" property, i.e. /ImageMask in PDF
# - pCOS id of mask image, i.e. /Mask or /SMask in PDF
def report_image_info(tet, doc, imageid):
    width = tet.pcos_get_number(doc, "images[%d]/Width" % imageid)
    height = tet.pcos_get_number(doc, "images[%d]/Height" % imageid)
    bpc = tet.pcos_get_number(doc,  "images[%d]/bpc" % imageid)
    cs = tet.pcos_get_number(doc, "images[%d]/colorspaceid" % imageid)
    components = tet.pcos_get_number(doc, "colorspaces[%d]/components" % cs)

    stdout.write("image %d: %dx%d pixel, " % (imageid, width, height))

    csname = tet.pcos_get_string(doc, "colorspaces[%d]/name" % cs)
    stdout.write("%dx%d bit %s" % (components, bpc, csname))

    if csname == "Indexed":
        basecs = int(tet.pcos_get_number(doc, "colorspaces[%d]/baseid" % cs))
        basecsname = tet.pcos_get_string(doc, "colorspaces[%d]/name" % basecs)
        stdout.write(" %s" % basecsname)

    # Check whether the image has been created by merging smaller images
    mergetype = int(tet.pcos_get_number(doc, "images[%d]/mergetype" % imageid))
    if mergetype == 1:
        stdout.write(", mergetype=artificial")

    stencilmask = int(tet.pcos_get_number(doc,"images[%d]/stencilmask" % imageid))
    if stencilmask != 0:
        stdout.write(", used as stencil mask")

    # Check whether the image has an attached mask
    maskid = int(tet.pcos_get_number(doc, "images[%d]/maskid" % imageid))

    if maskid != -1:
        stdout.write(", masked with image %d" % maskid)

    stdout.write("\n")

if len(argv) != 2:
    raise Exception("usage: image_resources <filename>\n")

try:
    try:
        tet = TET()

        # strip .pdf suffix if present
        outfilebase = argv[1]
        if outfilebase.endswith(".pdf") or outfilebase.endswith(".PDF"):
            outfilebase = outfilebase[:-4]

        tet.set_option(globaloptlist)

        doc = tet.open_document(argv[1], docoptlist)

        if (doc == -1):
            raise Exception("Error " + repr(tet.get_errnum()) + "in "
                + tet.get_apiname() + "(): " + tet.get_errmsg())

        # Images will only be merged upon opening a page.
        # In order to enumerate all merged image resources
        # we open all pages before extracting the images.

        # get number of pages in the document
        n_pages = int(tet.pcos_get_number(doc, "length:pages"))

        # loop over pages in the document */
        for pageno in range(1, n_pages + 1):

            page = tet.open_page(doc, pageno, pageoptlist)

            if page == -1:
                print("Error " + repr(tet.get_errnum()) + "in " \
                    + tet.get_apiname() + "(): " + tet.get_errmsg())
                continue                        # process next page

            if tet.get_errnum() != 0:
                print ("\nError " + repr(tet.get_errnum()) \
                    + "in " + tet.get_apiname() + "() on page " + \
                    repr(pageno) + ": " + tet.get_errmsg() + "\n")

            tet.close_page(page)


        # Get the number of pages in the document.
        # This includes plain images as well as image masks.
        n_images = int(tet.pcos_get_number(doc, "length:images"))

        # loop over image resources in the document */
        for imageid in range(n_images):

            # skip images which have been consumed by merging
            mergetype = int(tet.pcos_get_number(doc,
                        "images[%d]/mergetype" % imageid))
            if mergetype == 2:
                continue
            
            # Skip small images (see "smallimages" option)
            if tet.pcos_get_number(doc, "images[%d]/small" % imageid) > 0:
                continue
            
            # Report image details: pixel geometry, color space, etc.
            report_image_info(tet, doc, imageid)
            
            # Write image data to file
            imageoptlist = "filename={%s_I%d}" % (outfilebase, imageid)
            
            if tet.write_image_file(doc, imageid, imageoptlist) == -1:
                stdout.write("\nError " + repr(tet.get_errnum()) + "in " +
                    tet.get_apiname() + "():" + tet.get_errmsg() + "\n")

        tet.close_document(doc)

    except TETException:
        print ("TET exception occurred:\n[%d] %s: %s" %
            (tet.get_errnum(), tet.get_apiname(), tet.get_errmsg()))
        print_tb(exc_info()[2])

    except Exception:
        print ("Exception occurred: %s" % (exc_info()[0]))
        print_exc()

finally:
    tet.delete()
