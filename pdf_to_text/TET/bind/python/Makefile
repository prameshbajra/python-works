# Sample Makefile for TET's Python binding
# $Id: Makefile.sample,v 1.17 2017/05/10 14:57:14 rp Exp $

RM	= rm -f
PYBIN	= python

all: test

test::
	$(PYBIN) dumper.py TET-datasheet.pdf
	$(PYBIN) extractor.py TET-datasheet.pdf TET-datasheet.txt
	$(PYBIN) fontfilter.py TET-datasheet.pdf
	$(PYBIN) get_attachments.py Portfolio_sample.pdf attachments.txt
	$(PYBIN) images_per_page.py TET-datasheet.pdf
	$(PYBIN) image_resources.py TET-datasheet.pdf
	$(PYBIN) tetml.py TET-datasheet.pdf TET-datasheet.tetml

test-python2: test
	$(PYBIN) glyphinfo.py TET-datasheet.pdf TET-datasheet.info.txt

test-python3: test
	$(PYBIN) glyphinfo.py3 TET-datasheet.pdf TET-datasheet.info.txt

clean::
	$(RM) TET-datasheet.pdf dumper.txt TET-datasheet.txt fontfilter.txt
	$(RM) TET-datasheet.tetml TET-datasheet*.tif attachments.txt m.out
	$(RM) TET-datasheet.info.txt
