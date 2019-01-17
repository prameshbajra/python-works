package com.pdflib.tet.lucene;

import org.apache.lucene.analysis.Analyzer;

/**
 * (C) PDFlib GmbH 2015 www.pdflib.com
 *
 * This code is based on the Lucene Java command-line demo, which is part of the
 * Lucene Java distribution available at http://lucene.apache.org/java. This
 * code has been tested with Lucene Java 5.2.1.
 * 
 * The original code carried the following copyright notice:
 *
 * Copyright 2004 The Apache Software Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * 
 * @version $Id: IndexPdfFiles.java,v 1.5 2015/07/29 08:26:45 stm Exp $
 */

import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.IndexWriterConfig.OpenMode;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;

import com.pdflib.TETException;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.Date;

public class IndexPdfFiles {
    private IndexPdfFiles() {
    }

    public static void main(String[] args) throws IOException {
        String usage = "java " + IndexPdfFiles.class
                + " [-index INDEX_PATH] [-docs DOCS_PATH]\n\n"
                + "This indexes the documents in DOCS_PATH, creating a Lucene index"
                + "in INDEX_PATH that can be searched with SearchFiles";
        String index_dir = "index";
        String docsPath = null;
        for (int i = 0; i < args.length; i++) {
            if ("-index".equals(args[i])) {
                index_dir = args[i + 1];
                i++;
            }
            else if ("-docs".equals(args[i])) {
                docsPath = args[i + 1];
                i++;
            }
        }

        if (docsPath == null) {
            System.err.println("Usage: " + usage);
            System.exit(1);
        }

        final Path docDir = Paths.get(docsPath);
        if (!Files.isReadable(docDir)) {
            System.out.println("Document directory '" + docDir.toAbsolutePath()
                    + "' does not exist or is not readable, please check the path");
            System.exit(1);
        }

        Date start = new Date();
        try {
            Directory dir = FSDirectory.open(Paths.get(index_dir));
            Analyzer analyzer = new StandardAnalyzer();
            IndexWriterConfig iwc = new IndexWriterConfig(analyzer);

            // Create a new index in the directory, removing any
            // previously indexed documents:
            iwc.setOpenMode(OpenMode.CREATE);
            IndexWriter writer = new IndexWriter(dir, iwc);

            indexDocs(writer, docDir);
            writer.close();

            Date end = new Date();

            System.out.print(end.getTime() - start.getTime());
            System.out.println(" total milliseconds");
        }
        catch (IOException e) {
            System.out.println(" caught a " + e.getClass() + "\n with message: "
                    + e.getMessage());
        }
    }

    public static void indexDocs(final IndexWriter writer, Path path)
            throws IOException {
        if (Files.isDirectory(path)) {
            Files.walkFileTree(path, new SimpleFileVisitor<Path>() {
                @Override
                public FileVisitResult visitFile(Path file,
                        BasicFileAttributes attrs) throws IOException {
                    try {
                        if (file.toString().toLowerCase().endsWith(".pdf")) {
                            indexDoc(writer, file,
                                    attrs.lastModifiedTime().toMillis());
                        }
                    }
                    catch (IOException ignore) {
                        // don't index files that can't be read.
                    }
                    return FileVisitResult.CONTINUE;
                }
            });
        }
        else {
            if (path.toString().toLowerCase().endsWith(".pdf")) {
                indexDoc(writer, path,
                        Files.getLastModifiedTime(path).toMillis());
            }
        }
    }
    
    static void indexDoc(IndexWriter writer, Path file, long lastModified)
            throws IOException {
        System.out.println("adding " + file);
        try {
            writer.addDocument(PdfDocument.Document(file, lastModified));
        }
        // at least on windows, some temporary files raise this
        // exception with an "access denied" message
        // checking if the file can be read doesn't help
        catch (FileNotFoundException fnfe) {
            ;
        }
        catch (TETException e) {
            e.printStackTrace();
        }
    }
}
