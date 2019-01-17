package com.pdflib.tet.tika;

import java.io.BufferedWriter;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;

import org.apache.tika.metadata.Metadata;
import org.apache.tika.parser.ParseContext;
import org.apache.tika.sax.WriteOutContentHandler;
import org.xml.sax.ContentHandler;

/**
 * Small test program that uses the Tika API directly to extract text with
 * PDFlib TET. The output is written to an UTF-8-encoded file. Demonstrates
 * how to provide a password for documents that require the master password
 * for text extraction.
 * <p>
 * usage: com.pdflib.tet.tika.TikaApiTest &lt;input PDF&gt; &lt;output file&gt; [ &lt;password&gt; ]
 *  
 * @version $Id: TikaApiTest.java,v 1.1 2012/02/15 15:40:26 stm Exp $
 */
public class TikaApiTest {

    static final byte UTF_8_BOM[] = { (byte) 0xEF, (byte) 0xBB, (byte) 0xBF };
    
    /**
     * @param args<br>
     *            args[0] input PDF
     *            <br>
     *            args[1] output file
     *            <br>
     *            args[2] optional password
     */
    public static void main(String[] args) {
        ParseContext context = new ParseContext();
        Metadata metadata = new Metadata();

        try {
            InputStream is = new FileInputStream(args[0]);
            OutputStream os = new FileOutputStream(args[1]);
            
            os.write(UTF_8_BOM);
            
            Writer osw = new BufferedWriter(new OutputStreamWriter(os, "UTF-8"));
            ContentHandler handler = new WriteOutContentHandler(osw);

            if (args.length == 3) {
                metadata.add(TETPDFParser.PASSWORD, args[2]);
            }
            
            TETPDFParser pdfParser = new TETPDFParser();
            pdfParser.parse(is, handler, metadata, context);
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }
}
