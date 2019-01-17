package com.pdflib.tet.tika;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;
import java.util.Calendar;
import java.util.Collections;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.List;
import java.util.Set;
import java.util.SimpleTimeZone;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.tika.exception.TikaException;
import org.apache.tika.io.TemporaryResources;
import org.apache.tika.io.TikaInputStream;
import org.apache.tika.metadata.AccessPermissions;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.PagedText;
import org.apache.tika.metadata.Property;
import org.apache.tika.metadata.TikaCoreProperties;
import org.apache.tika.mime.MediaType;
import org.apache.tika.parser.ParseContext;
import org.apache.tika.parser.AbstractParser;
import org.apache.tika.sax.XHTMLContentHandler;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;

import com.pdflib.TET;
import com.pdflib.TETException;

/**
 * Tika PDF parser implementation using PDFlib TET. The implementation aims
 * to be compatible with Tika's built-in PDF parser (e.g. how the password
 * is provided for encrypted documents).
 * 
 * @version $Id: TETPDFParser.java,v 1.11 2015/10/13 08:07:51 rjs Exp $ 
 */
public class TETPDFParser extends AbstractParser {

    /**
     * Serial version UID
     */
    private static final long serialVersionUID = 941201790573619574L;

    /**
     * Metadata key for giving the document password to the parser. For
     * compatibility with Tika's built-in parser the same name for the
     * metadata entry for the password is used.
     */
    public static final String PASSWORD = "org.apache.tika.parser.pdf.password";
    
    /**
     * The options for the TET open_document function.
     * 
     * Indexing of password-protected documents that disallow text extraction is
     * possible by using the "shrug" option of TET_open_document(). Please read
     * the relevant section in the PDFlib Terms and Conditions and the TET
     * Manual about the "shrug" option to understand the implications of
     * using this feature.
     * 
     * private static final String DOC_OPT_LIST = "shrug";
     */
    private static final String DOC_OPT_LIST = "";
    
    /**
     * Page-specific option list. Note that "granularity=page" is hard-wired in
     * the invocation of the TET open_page function. Image extraction is
     * not needed for Tika, so we suppress it here.
     */
    static final String PAGE_OPT_LIST = "skipengines={image}";
    
    /**
     * Searchpath for resources such as CJK CMaps; can be overridden with
     * a Java property, i.e. -Dtet.searchpath=...
     */
    private static final String SEARCHPATH = "../../resource/cmap ../../resource";
 
    /**
     * PDF media type.
     */
    private static final MediaType MEDIA_TYPE = MediaType.application("pdf");
    
    /**
     * Registration for PDF MIME type.
     */
    private static final Set<MediaType> SUPPORTED_TYPES =
        Collections.singleton(MEDIA_TYPE);

    /* (non-Javadoc)
     * @see org.apache.tika.parser.Parser#getSupportedTypes(org.apache.tika.parser.ParseContext)
     */
    public Set<MediaType> getSupportedTypes(ParseContext context) {
        return SUPPORTED_TYPES;
    }

    /* (non-Javadoc)
     * @see org.apache.tika.parser.Parser#parse(java.io.InputStream, org.xml.sax.ContentHandler, org.apache.tika.metadata.Metadata, org.apache.tika.parser.ParseContext)
     */
    public void parse(InputStream stream, ContentHandler handler,
            Metadata metadata, ParseContext context) throws IOException,
            SAXException, TikaException {
        final TemporaryResources tmp = new TemporaryResources();
        
        try {
            final TikaInputStream tis = TikaInputStream.get(stream, tmp);
            final File tmpFile = tis.getFile();

            final TET tet = new TET();
            
            final String password = metadata.get(PASSWORD);
            String docOpts = DOC_OPT_LIST;
            if (password != null) {
                docOpts += " password={" + password + "}";
            }

            tet.set_option("searchpath={" + SEARCHPATH + "}");
            
            final String searchpath = System.getProperty("tet.searchpath");
            if (searchpath != null) {
            	tet.set_option("searchpath={" + searchpath + "}");
            }
            
            final int doc = tet.open_document(tmpFile.getAbsolutePath(), docOpts);
            
            try {
                if (doc != -1) {
                    try {
                        final int pageCount = (int) tet.pcos_get_number(doc, "length:pages");

                        extractMetadata(tet, doc, pageCount, metadata);
                        parseDocument(handler, metadata, tet, doc, pageCount);
                    }
                    finally {
                        tet.close_document(doc);
                    }
                }
                else {
                    throw new TikaException("Unable to open PDF document with TET: " + tet.get_errmsg());
                }
            }
            finally {
                tet.delete();
            }
        }
        catch (TETException e) {
            throw new TikaException("Exception occurred in TET parser" , e);
        }
        finally {
            tmp.dispose();
        }
    }

    /**
     * Save the metadata from the PDF's document information fields into the
     * Tika metadata object.
     * 
     * @param tet
     *            the TET object
     * @param doc
     *            the TET document handle
     * @param pageCount
     *            the document's page count
     * @param metadata
     *            the Tika metadata object
     * @throws TETException
     *             something went wrong during PDF parsing
     */
    private void extractMetadata(TET tet, int doc, int pageCount, Metadata metadata) throws TETException {
        metadata.set(PagedText.N_PAGES, pageCount);
        
        // PDF permissions
        addPdfPermission(tet, doc, metadata,
                AccessPermissions.EXTRACT_FOR_ACCESSIBILITY, "noaccessible");
        addPdfPermission(tet, doc, metadata,
                AccessPermissions.EXTRACT_CONTENT, "nocopy");
        addPdfPermission(tet, doc, metadata,
                AccessPermissions.ASSEMBLE_DOCUMENT, "noassemble");
        addPdfPermission(tet, doc, metadata,
                AccessPermissions.FILL_IN_FORM, "noforms");
        addPdfPermission(tet, doc, metadata,
                AccessPermissions.CAN_MODIFY, "nomodify");
        addPdfPermission(tet, doc, metadata,
                AccessPermissions.CAN_MODIFY_ANNOTATIONS, "noannots");
        addPdfPermission(tet, doc, metadata,
                AccessPermissions.CAN_PRINT, "nohiresprint");
        addPdfPermission(tet, doc, metadata,
                AccessPermissions.CAN_PRINT_DEGRADED, "noprint");
        
        final String INFO_DICT = "/Info";
        addMetadata(tet, doc, metadata, TikaCoreProperties.TITLE, INFO_DICT + "/Title");
        addMetadata(tet, doc, metadata, TikaCoreProperties.CREATOR, INFO_DICT + "/Author");
        addMetadata(tet, doc, metadata, TikaCoreProperties.CREATOR_TOOL, INFO_DICT + "/Creator");
        
        // As Tika decided that DublinCore subject is to be stored as KEYWORDS, we have
        // two information dictionary entries that are stored as KEYWORDS properties.
        // This is ok as KEYWORDS is a bag property.
        addMetadata(tet, doc, metadata, TikaCoreProperties.KEYWORDS, INFO_DICT + "/Keywords");
        addMetadata(tet, doc, metadata, TikaCoreProperties.KEYWORDS, INFO_DICT + "/Subject");
        
        // The metadata framework of Tika does not allow to distinguish between
        // Creator and Producer in the PDF sense. Therefore store the PDF Producer
        // property with its XMP name.
        addMetadata(tet, doc, metadata, "pdf:Producer", INFO_DICT + "/Producer");
        addMetadataDate(tet, doc, metadata, TikaCoreProperties.CREATED, INFO_DICT + "/CreationDate");
        addMetadataDate(tet, doc, metadata, TikaCoreProperties.MODIFIED, INFO_DICT + "/ModDate");
        
        // All remaining metadata is custom, copy this over as-is
        List<String> handledMetadata = Arrays.asList(new String[] {
             "Author", "Creator", "CreationDate", "ModDate",
             "Keywords", "Producer", "Subject", "Title", "Trapped"
        });
        
        final int infoCount = (int) tet.pcos_get_number(doc, "length:" + INFO_DICT);
        for (int i = 0; i < infoCount; i += 1) {
            final String name = tet.pcos_get_string(doc, INFO_DICT + "[" + i + "].key");
            if (!handledMetadata.contains(name)) {
                addMetadata(tet, doc, metadata, name, INFO_DICT + "[" + i + "].val");
            }
        }
        
        final String pdfversion = tet.pcos_get_string(doc, "pdfversionstring");
        metadata.set("pdf:PDFVersion", pdfversion);
        metadata.add(TikaCoreProperties.FORMAT,
                MEDIA_TYPE.toString() + "; version=" + pdfversion);
    }

    /**
     * Add a PDF permission as metadata property.
     * 
     * @param tet
     *            the TET object
     * @param doc
     *            the TET document handle
     * @param metadata
     *            Metadata object for saving document information field values 
     * @param permissionProperty
     *            the Tika property identifier for the permission
     * @param pCosName
     *            the name of the pCOS encrypt subobject for the property
     * @throws TETException 
     */
    private void addPdfPermission(TET tet, int doc, Metadata metadata,
            Property permissionProperty, String pCosName) throws TETException {
        // Get permission from pCos. Note that the permissions are inverted
        // compated to what Tika expects.
        int permission = (int) tet.pcos_get_number(doc, "encrypt/" + pCosName);
        metadata.set(permissionProperty, Boolean.toString(permission == 0));
    }

    /**
     * Save a PDF date field into the Tika metadata object, if it is actually
     * available.
     * 
     * @param tet
     *            the TET object
     * @param doc
     *            the TET document handle
     * @param metadata
     *            Metadata object for saving document information field values
     * @param tikaProperty
     *            the Tika property to save
     * @param pcosPath
     *            the pCOS path for the document info field
     * @throws TETException
     *            something went wrong during PDF parsing
     */
    private void addMetadataDate(TET tet, int doc, Metadata metadata,
            Property tikaProperty, String pcosPath) throws TETException {
        final String type = tet.pcos_get_string(doc, "type:" + pcosPath);
        if ("string".equals(type)) {
            final String value = tet.pcos_get_string(doc, pcosPath);
            if (value != null && value.length() > 0) {
                Date date = parsePdfDate(value);
                if (date != null) {
                    metadata.set(tikaProperty, date);
                }
            }
        }
    }

    /**
     * Regular expression for parsing PDF date.
     */
    final static Pattern pdfDatePattern =
        //                      YYYY       MM         DD         HH         mm         SS      O    TZ_SIGN   HH'     mm'
        Pattern.compile("(?:D:)?(\\d{4})(?:(\\d{2})(?:(\\d{2})(?:(\\d{2})(?:(\\d{2})(?:(\\d{2})(Z|(?:(\\+|\\-)(?:(\\d{2})'(?:(\\d{2})')?)))?)?)?)?)?)?");
    
    /**
     * Symbolic names for the groups of the pattern.
     */
    private enum PdfDateGroups {
        dummy, // groups start at 1
        YYYY,
        MM,
        DD,
        HH,
        mm,
        SS,
        O,
        TZ_SIGN,
        TZ_HH,
        TZ_mm
    }
    
    /**
     * Parse a PDF date string.
     * 
     * @param value
     *          The string from the PDF document information entry.
     * @return
     *          The converted Date if the format was correct, null otherwise.
     */
    private Date parsePdfDate(String value) {
        Date result = null;
        
        final Matcher matcher = pdfDatePattern.matcher(value);
        if (matcher.matches()) {
            // First determine timezone for constructing the calendar in the
            // correct timezone
            String O = matcher.group(PdfDateGroups.O.ordinal());
            
            Calendar calendar;
            if (O == null || O.equals("")) {
                calendar = new GregorianCalendar();
            }
            else {
                SimpleTimeZone zone;
                
                if (O.equals("Z")) {
                    zone = new SimpleTimeZone(0, "GMT");
                }
                else {
                    int sign = "-".equals(matcher.group(PdfDateGroups.TZ_SIGN.ordinal())) ? -1 : 1;
                    String TZ_HH = matcher.group(PdfDateGroups.TZ_HH.ordinal());
                    int tzHour = parseInt(TZ_HH, 0);
                    String TZ_mm = matcher.group(PdfDateGroups.TZ_mm.ordinal());
                    int tzMinutes = parseInt(TZ_mm, 0);
                    zone = new SimpleTimeZone(sign * (tzHour * 1000 * 60 * 60 + tzMinutes * 1000 * 60), "unknown");
                }
                
                calendar = new GregorianCalendar(zone);
            }

            String YYYY = matcher.group(PdfDateGroups.YYYY.ordinal());
            int year = Integer.parseInt(YYYY);
            String MM = matcher.group(PdfDateGroups.MM.ordinal());
            int month = parseInt(MM, 1);
            String DD = matcher.group(PdfDateGroups.DD.ordinal());
            int date = parseInt(DD, 1);
            String HH = matcher.group(PdfDateGroups.HH.ordinal());
            int hourOfDay = parseInt(HH, 0);
            String mm = matcher.group(PdfDateGroups.mm.ordinal());
            int minute = parseInt(mm, 0);
            String SS = matcher.group(PdfDateGroups.SS.ordinal());
            int second = parseInt(SS, 0);
            
            calendar.set(Calendar.MILLISECOND, 0);
            calendar.set(year, month - 1, date, hourOfDay, minute, second);
            
            result = calendar.getTime();
        }
        
        return result;
    }

    /**
     * Parse a string that is supposed to be an integer.
     * 
     * @param intString
     *            the string to parse
     * @param defaultValue
     *            the default value to return if intString is null or empty
     * @return converted string
     */
    private int parseInt(String intString, int defaultValue) {
        return (intString == null || intString.equals("")) ? defaultValue : Integer.parseInt(intString);
    }

    /**
     * Save value of a document info field in the metadata object, if the
     * document info field actually exists.
     * 
     * @param tet
     *            the TET object
     * @param doc
     *            the TET document handle
     * @param metadata
     *            Metadata object for saving document information field values
     * @param property
     *            the Tika property identifier
     * @param pcosPath
     *            the pCOS path for the document info field
     * @throws TETException
     *            something went wrong during PDF parsing
     */
    private void addMetadata(TET tet, int doc, Metadata metadata, Property property, String pcosPath) throws TETException {
        final String type = tet.pcos_get_string(doc, "type:" + pcosPath);
        if (type.equals("name") || type.equals("string")) {
            final String value = tet.pcos_get_string(doc, pcosPath);
            if (value != null && value.length() > 0) {
                metadata.add(property, value);
            }
        }
    }
    
    /**
     * Save value of a document info field in the metadata object, if the
     * document info field actually exists.
     * 
     * @param tet
     *            the TET object
     * @param doc
     *            the TET document handle
     * @param metadata
     *            Metadata object for saving document information field values
     * @param property
     *            free-form name of the property
     * @param pcosPath
     *            the pCOS path for the document info field
     * @throws TETException
     *            something went wrong during PDF parsing
     */
    private void addMetadata(TET tet, int doc, Metadata metadata, String name, String pcosPath) throws TETException {
        final String type = tet.pcos_get_string(doc, "type:" + pcosPath);
        if ("name".equals(type) || "string".equals(type)) {
            final String value = tet.pcos_get_string(doc, pcosPath);
            if (value != null && value.length() > 0) {
                metadata.add(name, value);
            }
        }
    }

    /**
     * Parse PDF document and extract the text.
     * 
     * @param handler
     *            the ContentHandler
     * @param metadata
     *            the Metada object for saving metadata items
     * @param tet
     *            the TET object
     * @param doc
     *            the TET document handle
     * @throws TETException
     *             something went wrong during PDF parsing
     * @throws SAXException
     */
    private void parseDocument(ContentHandler handler, Metadata metadata,
            TET tet, int doc, int pageCount) throws TETException, SAXException {

        final XHTMLContentHandler xhtml = new XHTMLContentHandler(handler,
                metadata);
        xhtml.startDocument();

        int i;
        for (i = 1; i <= pageCount; i += 1) {
            final int page = tet.open_page(doc, i,
                    PAGE_OPT_LIST + " granularity=page");

            if (page != -1) {
                xhtml.startElement("div", "class", "page");

                xhtml.startElement("p");

                String text;
                boolean first = true;
                while ((text = tet.get_text(page)) != null) {
                    if (first) {
                        first = false;
                    }
                    else {
                        /* provide a separator between chunks of text */
                        xhtml.characters(" ");
                    }
                    xhtml.characters(text);
                }

                xhtml.endElement("p");
                xhtml.endElement("div");

                tet.close_page(page);
            }
        }

        xhtml.endDocument();
    }
}
