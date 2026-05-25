Attribute VB_Name = "TrongkaiAPI"
' =====================================================================
' TrongkAI API integration - VBA module
' Importar via Alt+F11 -> File -> Import File... -> TrongkaiAPI.bas
'
' Endpoints del motor TrongkAI:
'   GET  /api/snapshot           - estado completo del modelo
'   GET  /api/tearsheet.pdf      - PDF ejecutivo
'   GET  /readiness/score        - score 0-100
'   POST /sensitivity/heatmap    - heatmap 2D TIR
'   GET  /sensitivity/breakeven  - break-even por driver
'   GET  /sensitivity/curves     - curvas 1D
'   GET  /macro/chile            - macro Banco Central
'   GET  /carbon/footprint       - LCA carbono
'   GET  /compliance/rep         - Ley REP timeline
'
' Author: TrongkAI Platform
' =====================================================================
Option Explicit

Public Const ENGINE_URL As String = "https://trongkai-engine.fly.dev"


' Helper genérico: GET un endpoint y devuelve texto JSON
Public Function ApiGET(path As String) As String
    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "GET", ENGINE_URL & path, False
    http.setRequestHeader "Accept", "application/json"
    http.Send
    ApiGET = http.responseText
End Function


' Helper genérico: POST con JSON body
Public Function ApiPOST(path As String, jsonBody As String) As String
    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "POST", ENGINE_URL & path, False
    http.setRequestHeader "Content-Type", "application/json"
    http.setRequestHeader "Accept", "application/json"
    http.Send jsonBody
    ApiPOST = http.responseText
End Function


' ===== Macro 1: Refrescar Dashboard =====
Public Sub RefrescarDashboard()
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Dashboard")
    On Error GoTo 0
    If ws Is Nothing Then
        MsgBox "No existe la hoja 'Dashboard'", vbExclamation
        Exit Sub
    End If

    Application.StatusBar = "Conectando al motor TrongkAI..."
    Dim json As String
    json = ApiGET("/api/snapshot")

    ' Parse manual de campos clave (sin librería JSON externa)
    Dim tir As Double, van As Double
    tir = ExtractNumber(json, """tir"":")
    van = ExtractNumber(json, """van"":")

    ws.Range("A6").Value = Format(tir, "0.00%")
    ws.Range("C6").Value = "$" & Format(van / 1000000000, "0.0") & "B CLP"
    ws.Range("A3").Value = "Actualizado: " & Format(Now, "dd/mm/yyyy hh:mm")

    Application.StatusBar = False
    MsgBox "Dashboard actualizado desde el motor en vivo.", vbInformation, "TrongkAI"
End Sub


' ===== Macro 2: Descargar PDF tearsheet =====
Public Sub DescargarTearsheetPDF()
    Dim url As String
    url = ENGINE_URL & "/api/tearsheet.pdf"
    ThisWorkbook.FollowHyperlink url
End Sub


' ===== Macro 3: Recalcular Investment Readiness =====
Public Sub RecalcularReadiness()
    Application.StatusBar = "Calculando 8 dimensiones + Monte Carlo..."
    Dim json As String
    json = ApiGET("/readiness/score?n_sims_mc=500")

    Dim score As Double
    score = ExtractNumber(json, """score_total"":")

    Application.StatusBar = False
    MsgBox "Investment Readiness Score: " & Format(score, "0.0") & "/100", _
           vbInformation, "TrongkAI Readiness"
End Sub


' ===== Macro 4: Heatmap Sensibilidad 5x5 =====
Public Sub EjecutarHeatmap5x5()
    Application.StatusBar = "Ejecutando 25 simulaciones..."
    Dim json As String
    Dim body As String
    body = "{""driver_x"":""precio"",""driver_y"":""costo_mmpp"",""n"":5,""hurdle_pct"":0.15}"
    json = ApiPOST("/sensitivity/heatmap", body)

    Dim pctSafe As Double
    pctSafe = ExtractNumber(json, """pct_zona_segura"":")

    Application.StatusBar = False
    MsgBox "Heatmap 5x5 completado." & vbCrLf & _
           "Zona segura: " & Format(pctSafe, "0.0%"), vbInformation, "TrongkAI Sensibilidad"
End Sub


' ===== Macro 5: Refrescar Macro Chile =====
Public Sub RefrescarMacroChile()
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Macro Chile")
    On Error GoTo 0
    If ws Is Nothing Then
        MsgBox "No existe la hoja 'Macro Chile'", vbExclamation
        Exit Sub
    End If

    Application.StatusBar = "Consultando Banco Central via mindicador.cl..."
    Dim json As String
    json = ApiGET("/macro/chile")

    ws.Range("B5").Value = ExtractNumber(json, """dolar_clp"":")
    ws.Range("B6").Value = ExtractNumber(json, """uf_clp"":")
    ws.Range("B7").Value = ExtractNumber(json, """ipc_pct_mensual"":")
    ws.Range("B8").Value = ExtractNumber(json, """tpm_pct"":")
    ws.Range("B9").Value = ExtractNumber(json, """tasa_desempleo_pct"":")

    Application.StatusBar = False
    MsgBox "Macro Chile actualizado.", vbInformation, "TrongkAI"
End Sub


' ===== Macro 6: Refrescar todo =====
Public Sub RefrescarTodo()
    Application.ScreenUpdating = False
    Call RefrescarDashboard
    Call RefrescarMacroChile
    Application.ScreenUpdating = True
    MsgBox "Todas las hojas refrescadas desde el motor TrongkAI.", _
           vbInformation, "TrongkAI"
End Sub


' ===== Helper: parser JSON minimalista =====
Private Function ExtractNumber(json As String, key As String) As Double
    Dim startPos As Long, endPos As Long
    Dim valStr As String

    startPos = InStr(json, key)
    If startPos = 0 Then
        ExtractNumber = 0
        Exit Function
    End If
    startPos = startPos + Len(key)

    ' Skip espacios
    Do While Mid(json, startPos, 1) = " "
        startPos = startPos + 1
    Loop

    ' Buscar fin (coma, llave o corchete)
    endPos = startPos
    Do While endPos <= Len(json) And InStr("0123456789.-eE", Mid(json, endPos, 1)) > 0
        endPos = endPos + 1
    Loop

    valStr = Mid(json, startPos, endPos - startPos)
    If IsNumeric(valStr) Then
        ExtractNumber = CDbl(valStr)
    Else
        ExtractNumber = 0
    End If
End Function
