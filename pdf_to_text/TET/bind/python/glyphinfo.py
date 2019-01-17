#!/usr/bin/python
# Simple Python text and image glyphinfo based on PDFlib TET
#
# $Id: glyphinfo.py,v 1.17 2017/04/03 13:00:23 rjs Exp $

from sys import exc_info, argv
from traceback import print_tb, print_exc
from PDFlib.TET import *

#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')

# global option list
globaloptlist = "searchpath={{../data} {../../../resource/cmap}}"

# document-specific option list
docoptlist = ""

# page-specific option list
pageoptlist = "granularity=word"

# tet.char_info character types with real geometry info.
TET_CT__REAL            = 0
TET_CT_NORMAL           = 0
TET_CT_SEQ_START        = 1

# tet.char_info character types with artificial geometry info.
TET_CT__ARTIFICIAL      = 10
TET_CT_SEQ_CONT         = 10
TET_CT_INSERTED         = 12

# tet.char_info text rendering modes.
TET_TR_FILL             = 0     # fill text
TET_TR_STROKE           = 1     # stroke text (outline)
TET_TR_FILLSTROKE       = 2     # fill and stroke text
TET_TR_INVISIBLE        = 3     # invisible text
TET_TR_FILL_CLIP        = 4     # fill text and
                                # add it to the clipping path
TET_TR_STROKE_CLIP      = 5     # stroke text and
                                #  add it to the clipping path
TET_TR_FILLSTROKE_CLIP  = 6     # fill and stroke text and
                                #  add it to the clipping path
TET_TR_CLIP             = 7     # add text to the clipping path

# tet.char_info attributes
TET_ATTR_NONE      = 0x00000000
TET_ATTR_SUB       = 0x00000001 # subscript
TET_ATTR_SUP       = 0x00000002 # superscript
TET_ATTR_DROPCAP   = 0x00000004 # initial large letter
TET_ATTR_SHADOW    = 0x00000008 # shadowed text
# character before hyphenation
TET_ATTR_DEHYPHENATION_PRE       = 0x00000010
# hyphenation artifact, i.e. the dash
TET_ATTR_DEHYPHENATION_ARTIFACT  = 0x00000020
# character after hyphenation
TET_ATTR_DEHYPHENATION_POST      = 0x00000040

import traceback
def formatExceptionInfo(maxTBlevel=5):
    cla, exc, trbk = exc_info()
    excName = cla.__name__
    try:
        excArgs = exc.__dict__["args"]
    except KeyError:
        excArgs = "<no args>"
    excTb = traceback.format_tb(trbk, maxTBlevel)
    return (excName, excArgs, excTb)

# Print color space and color value details of a glyph's fill color
def print_color_value(outfp, tet, doc, colorid):

    # We handle only the fill color, but ignore the stroke color.
    # The stroke color can be retrieved analogously with the
    # keyword "stroke".
    colorinfo = tet.get_color_info(doc, colorid, "usage=fill")

    if colorinfo["colorspaceid"] == -1 and colorinfo["patternid"] == -1:
        outfp.write(" (not filled)")
        return

    outfp.write(" (")

    if colorinfo["patternid"] != -1:
        patterntype = tet.pcos_get_number(doc,
                "patterns[%d]/PatternType" % colorinfo["patternid"])

        if patterntype == 1:        # Tiling pattern
            painttype = tet.pcos_get_number(doc,
                 "patterns[%d]/PaintType" % colorinfo["patternid"])
            if painttype == 1:
                outfp.write("colored Pattern)")
                return
            elif painttype == 2:
                outfp.write("uncolored Pattern, base color: ")
                # FALLTHROUGH to colorspaceid output
        elif patterntype == 2:        # Shading pattern
            shadingtype = tet.pcos_get_number(doc,
                 "patterns[%d]/Shading/ShadingType" % colorinfo["patternid"])

            outfp.write("shading Pattern, ShadingType=%d)" % shadingtype)
            return

    csname = tet.pcos_get_string(doc,
                "colorspaces[%d]/name" % colorinfo["colorspaceid"])

    outfp.write(csname)

    # Emit more details depending on the colorspace type
    if csname == "ICCBased":
        iccprofileid = tet.pcos_get_number(doc,
                 "colorspaces[%d]/iccprofileid" % colorinfo["colorspaceid"])

        errormessage = tet.pcos_get_string(doc,
                        "iccprofiles[%d]/errormessage" % iccprofileid);

        # Check whether the embedded profile is damaged
        if len(errormessage) > 0:
            outfp.write(" (%s)" % errormessage)
        else:
            profilename = tet.pcos_get_string(doc,
                    "iccprofiles[%d]/profilename" % iccprofileid);
            outfp.write(" '%s'" % profilename)

            profilecs = tet.pcos_get_string(doc,
                    "iccprofiles[%d]/profilecs" % iccprofileid);
            outfp.write(" '%s'" % profilecs)
    elif csname == "Separation":
        colorantname = tet.pcos_get_string(doc,
                 "colorspaces[%d]/colorantname" % colorinfo["colorspaceid"])
        outfp.write(" '%s'" % colorantname)
    elif csname == "DeviceN":
        outfp.write(" ")

        for i in range(len(colorinfo["components"])):
            colorantname = tet.pcos_get_string(doc,
                    "colorspaces[%d]/colorantnames[%d]" %
                            (colorinfo["colorspaceid"], i))

            outfp.write(colorantname)

            if i != len(colorinfo["components"]) - 1:
                outfp.write("/")
    elif csname == "Indexed":
        baseid = tet.pcos_get_number(doc,
                 "colorspaces[%d]/baseid" % colorinfo["colorspaceid"]);

        csname = tet.pcos_get_string(doc, "colorspaces[%d]/name", baseid);

        outfp.write(" %s" % csname)

    outfp.write(" ")
    for i in range(len(colorinfo["components"])):
        outfp.write("%g" % colorinfo["components"][i])

        if (i != len(colorinfo["components"]) - 1):
            outfp.write("/")
    outfp.write(")")

if len(argv) != 3:
    raise Exception("usage: glyphinfo <infilename> <outfilename>\n")

try:
    try:
        tet = TET()

        fp = open(argv[2], 'w')
        from ctypes import *
        PyFile_SetEncoding = pythonapi.PyFile_SetEncoding
        PyFile_SetEncoding.argtypes = (py_object, c_char_p)
        PyFile_SetEncoding(fp, 'utf-8')

        tet.set_option(globaloptlist)

        doc = tet.open_document(argv[1], docoptlist)

        if doc == -1:
            raise Exception("Error " + repr(tet.get_errnum()) + "in "
                + tet.get_apiname() + "(): " + tet.get_errmsg())

        # get number of pages in the document
        n_pages = tet.pcos_get_number(doc, "length:pages")

        # write UTF-8 BOM
        fp.write("%c%c%c" % (0xef, 0xbb, 0xbf))

        # loop over pages in the document
        for pageno in range(1, int(n_pages) + 1):
            previouscolorid = -1
            page = tet.open_page(doc, pageno, pageoptlist)

            if page == -1:
                print("Error " + repr(tet.get_errnum()) + "in "
                    + tet.get_apiname() + "(): " + tet.get_errmsg())
                continue                        # try next page

            # Administrative information
            fp.write("[ Document: '%s' ]\n" %
                            tet.pcos_get_string(doc, "filename"))
            fp.write("[ Document options: '%s' ]\n" % docoptlist)
            fp.write("[ Page options: '%s' ]\n" % pageoptlist)
            fp.write("[ ----- Page %d ----- ]\n" % pageno)

            # Retrieve all text fragments
            text = tet.get_text(page)
            while text != None:
                fp.write("[%s]\n" % text)  # print the retrieved text

                # Loop over all characters
                ci = tet.get_char_info(page)
                while ci:
                    # Fetch the font name with pCOS (based on its ID)
                    fontname = tet.pcos_get_string(doc,
                                "fonts[%d]/name" % ci["fontid"])

                    # Print the Unicode code point
                    fp.write("U+%04X" % ci["uv"])

                    # ...and the character
                    fp.write(" '%s'" % unichr(ci["uv"]).encode('utf-8'))

                    # Print font name, size, and position
                    fp.write(" %s size=%.2f x=%.2f y=%.2f" %
                        (fontname, ci["fontsize"], ci["x"], ci["y"]))

                    # Print the color id
                    fp.write(" colorid=%d" % ci["colorid"])

                    # Check whether the text color changed
                    if ci["colorid"] != previouscolorid:
                        print_color_value(fp, tet, doc, ci["colorid"])
                        previouscolorid = ci["colorid"]

                    # Examine the "type" member
                    if ci["type"] == TET_CT_SEQ_START:
                        fp.write( " ligature_start")
                    elif ci["type"] == TET_CT_SEQ_CONT:
                        fp.write( " ligature_cont")
                    # Separators are only inserted for granularity > word
                    elif ci["type"] == TET_CT_INSERTED:
                        fp.write( " inserted")

                    # Examine the bit flags in the "attributes" member
                    if ci["attributes"] != TET_ATTR_NONE:
                        if ci["attributes"] & TET_ATTR_SUB:
                            fp.write("/sub")
                        if ci["attributes"] & TET_ATTR_SUP:
                            fp.write("/sup")
                        if ci["attributes"] & TET_ATTR_DROPCAP:
                            fp.write("/dropcap")
                        if ci["attributes"] & TET_ATTR_SHADOW:
                            fp.write("/shadow")
                        if ci["attributes"] & TET_ATTR_DEHYPHENATION_PRE:
                            fp.write("/dehyphenation_pre")
                        if ci["attributes"] & TET_ATTR_DEHYPHENATION_ARTIFACT:
                            fp.write("/dehyphenation_artifact")
                        if ci["attributes"] & TET_ATTR_DEHYPHENATION_POST:
                            fp.write("/dehyphenation_post")

                    fp.write("\n")
                    ci = tet.get_char_info(page)

                fp.write("\n")
                text = tet.get_text(page)

            if tet.get_errnum() != 0:
                print ("\nError " + repr(tet.get_errnum())
                    + "in " + tet.get_apiname() + "() on page " +
                    repr(pageno) + ": " + tet.get_errmsg() + "\n")

            tet.close_page(page)

        tet.close_document(doc)

    except TETException:
        print ("TET exception occurred:\n[%d] %s: %s" %
            ((tet.get_errnum()), tet.get_apiname(), tet.get_errmsg()))
        print_tb(exc_info()[2])

    except Exception:
        print ("Exception occurred: %s" % (exc_info()[0]))
        print_exc()

finally:
    tet.delete()
