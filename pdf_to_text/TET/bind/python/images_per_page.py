#!/usr/bin/python
# Page-based image extractor based on PDFlib TET
#
# $Id: images_per_page.py,v 1.4 2015/08/17 12:18:16 rjs Exp $

from sys import exc_info, argv, stdout, stderr
from traceback import print_tb, print_exc
from PDFlib.TET import *

# global option list */
globaloptlist = "searchpath={{../data}}"

# document-specific option list */
docoptlist = ""

# page-specific option list, e.g.
# "imageanalysis={merge={gap=1} smallimages={maxwidth=20}}"
pageoptlist = ""

# Print the following information for each image:
# - pCOS id (required for indexing the images[] array)
# - pixel size of the underlying PDF Image XObject
# - number of components, bits per component, and colorspace
# - mergetype if different from "normal", i.e. "artificial" (=merged)
#   or "consumed"
# - "stencilmask" property, i.e. /ImageMask in PDF
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

    stdout.write("\n")

if len(argv) != 2:
    raise Exception("usage: image_resources <filename>\n")

pageno = 0

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

        # get number of pages in the document
        n_pages = int(tet.pcos_get_number(doc, "length:pages"))

        # Loop over all pages and extract images */
        for pageno in range(1, n_pages + 1):
            imagecount = 0
            
            page = tet.open_page(doc, pageno, pageoptlist)

            if page == -1:
                print("Error " + repr(tet.get_errnum()) + "in " \
                    + tet.get_apiname() + "(): " + tet.get_errmsg())
                continue                        # process next page

            # Retrieve all images on the page
            ti = tet.get_image_info(page)
            while ti:
                imagecount += 1
        
                # Report image details: pixel geometry, color space, etc.
                report_image_info(tet, doc, ti["imageid"])
        
                # Report placement geometry
                stdout.write(("  placed on page %d at position (%g, %g): "
                       "%dx%dpt, alpha=%g, beta=%g\n") %
                    (pageno, ti["x"], ti["y"],
                      int(ti["width"]), int(ti["height"]),
                      ti["alpha"], ti["beta"]))
        
                # Write image data to file
                imageoptlist = ("filename={%s_p%d_%d_I%d}" %
                        (outfilebase, pageno, imagecount, ti["imageid"]))
        
                if tet.write_image_file(doc, ti["imageid"], imageoptlist) == -1:
                    stdout.write("\nError %d in %s(): %s\n" %
                                    (tet.get_errnum(), tet.get_apiname(),
                                     tet.get_errmsg()))
                    continue                  # process next image
        
                # Check whether the image has a mask attached...
                maskid = int(tet.pcos_get_number(doc,
                            "images[%d]/maskid" % ti["imageid"]))
        
                # ...and retrieve it if present
                if maskid != -1:
                    stdout.write("  masked with ")

                    report_image_info(tet, doc, maskid)

                    imageoptlist = ("filename={%s_p%d_%d_I%d_mask_I%d}" %
                       (outfilebase, pageno, imagecount, ti["imageid"], maskid))

                    if tet.write_image_file(doc, maskid, imageoptlist) == -1:
                        stdout.write("\nError %d in %s() for mask image: %s\n" %
                            (tet.get_errnum(), tet.get_apiname(),
                            tet.get_errmsg()))

                ti = tet.get_image_info(page)

            if tet.get_errnum() != 0:
                stderr.write("Error %d in %s() on page %d: %s\n" %
                    (tet.get_errnum(), tet.get_apiname(), pageno,
                    tet.get_errmsg()))

            tet.close_page(page)

        tet.close_document(doc)

    except TETException:
        if pageno == 0:
            stderr.write("Error %d in %s(): %s\n" %
                (tet.get_errnum(), tet.get_apiname(), tet.get_errmsg()))
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
