' VBScript script to run TET XSLT samples
'
' usage: cscript runxsl.vbs [ <input file> <stylesheet> <output file> [ { <param name> <param value> } ... ] ]
'
' As there is no documented way to produce UTF-8 output with MSXML from
' VBScript, all the output is encoded as UTF-16.
'
' If the script is invoked without arguments, it will run all the samples.
' If the script is invoked with the arguments <input file>, <stylesheet> and
' <output file>, the script will run the given stylesheet for the input file
' and write the results to the output file. Stylesheet parameters can be
' provided as pairwise arguments at the end of the command line.
'
' $Id: runxslt.vbs,v 1.13 2015/08/06 14:02:43 stm Exp $

Option Explicit

Dim fso
Set fso = WScript.CreateObject("Scripting.FileSystemObject")

Dim wsh
Set wsh = WScript.CreateObject("WScript.Shell")

Private Sub RunXslt(inputFile, styleSheet, outputFilename)
        Dim xslt
        Dim xslDoc
        Dim xmlDoc
        Dim result
        Dim outputFile
        Dim strErr
        
        Set xslt = CreateObject("MSXML2.XSLTemplate")
        Set xslDoc = CreateObject("Msxml2.FreeThreadedDOMDocument")
        
        WScript.Echo "Transforming input file """ & inputFile & """ with stylesheet """ & _
                styleSheet & """ to output file """ & outputFilename & """"
 
        xslDoc.async = False
        xslDoc.load styleSheet
       
        ' load the XSLT stylesheet
        If xslDoc.parseError.errorCode <> 0 Then
		strErr = xslDoc.parseError.reason & " line: " & xslDoc.parseError.Line & " col: " & xslDoc.parseError.linepos & " text: " & xslDoc.parseError.srcText
		MsgBox strErr, vbCritical, "Error loading the stylesheet "  & styleSheet
		Exit Sub
        End If
        
        Set xslt.stylesheet = xslDoc

        Set xmlDoc = CreateObject("Msxml2.DOMDocument")
        xmlDoc.async = False
        xmlDoc.load inputFile
	
        If xmlDoc.parseError.errorCode <> 0 Then
		strErr = xmlDoc.parseError.reason & " line: " & xmlDoc.parseError.Line & " col: " & xmlDoc.parseError.linepos & " text: " & xmlDoc.parseError.srcText
		MsgBox strErr, vbCritical, "Error loading the input file " & inputFile
		Exit Sub
        End If
        
        Dim xslProc
        Set xslProc = xslt.createProcessor()
        xslProc.input = xmlDoc
        
        ' Loop to add all the stylesheet parameters if they were provided on the
        ' command line
        Dim i
        For i = 3 to WScript.Arguments.Count - 1 Step 2
                xslProc.addParameter WScript.Arguments(i), WScript.Arguments(i + 1)
        Next
        
        ' Apply the stylesheet
        If Not xslProc.Transform Then
                ' The IXSLProcessor interface does not provided additional error information
        	MsgBox "Error executing the stylesheet " & styleSheet, vbCritical, "Error executing the stylesheet " & styleSheet
        	Exit Sub
        End If
         
        Set xslt = Nothing
        Set xslDoc = Nothing
        
        ' Write the output encoded as UTF-16
        Set outputFile = fso.CreateTextFile(outputFilename, True, True)
        outputFile.Write(xslProc.output)
        outputFile.Close
        
        Set xslProc = Nothing 
End Sub

Private Sub Usage()
        WScript.Echo "usage: runxsl.vbs [ <input file> <stylesheet> <output file> [ { <param name> <param value> } ... ] ]"
        WScript.Quit 1
End Sub

Private Sub MakeTetml(cmd, outFileName)
	WScript.Echo "Generating file '" & outFileName & "'..."
	WScript.Echo "Executing '" & cmd & "'"
	wsh.Run cmd, 10, True
End Sub

If WScript.Arguments.Count >= 3 Then
        ' If there are parameters provided, the arguments must occur pairwise
        If WScript.Arguments.Count > 3 Then
                Dim paramCount
                
                paramCount = WScript.Arguments.Count - 3
                If paramCount Mod 2 <> 0 Then
                        WScript.Echo "Arguments for stylesheet parameters must occur pairwise"
                        Usage
                End If
        End If                
        RunXslt WScript.Arguments(0), WScript.Arguments(1), WScript.Arguments(2)
ElseIf WScript.Arguments.Count = 0 Then
	Const tetExe = "..\..\bin\tet"
	Const pdfFile = "..\data\TET-datasheet.pdf"
	Const pbTetml = "TET-datasheet.pb.tetml"
	Const nopbTetml = "TET-datasheet.nopb.tetml"

	Dim cmd

	If Not fso.FileExists(pbTetml) Then
		cmd = tetExe & " --tetml wordplus --image " & _
			"-o " & pbTetml & " " & pdfFile
		MakeTetml cmd, pbTetml
	End If

	If Not fso.FileExists(nopbTetml) Then
		cmd = tetExe & " --tetml wordplus --image " & _
			"--pageopt contentanalysis={punctuationbreaks=false} " & _
			"-o " & nopbTetml & " " & pdfFile
		MakeTetml cmd, nopbTetml
	End If

        RunXslt pbTetml, "concordance.xsl", "TET-datasheet.concordance.txt"
        RunXslt pbTetml, "index.xsl", "TET-datasheet.index.txt"
        RunXslt pbTetml, "table.xsl", "TET-datasheet.table.csv"
        RunXslt nopbTetml, "textonly.xsl", "TET-datasheet.textonly.txt"
        RunXslt pbTetml, "metadata.xsl", "TET-datasheet.metadata.txt"
        RunXslt pbTetml, "fontfilter.xsl", "TET-datasheet.fontfilter.txt"
        RunXslt pbTetml, "fontstat.xsl", "TET-datasheet.fontstat.txt"
        RunXslt pbTetml, "fontfinder.xsl", "TET-datasheet.fontfinder.txt"
        RunXslt nopbTetml, "tetml2html.xsl", "TET-datasheet.tetml2html.html"
Else
        Usage
End If
