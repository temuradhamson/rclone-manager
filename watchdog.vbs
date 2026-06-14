Set WshShell = CreateObject("WScript.Shell")
Set oHTTP = CreateObject("MSXML2.XMLHTTP")

Do While True
    alive = False
    On Error Resume Next
    oHTTP.Open "GET", "http://127.0.0.1:8001/api/health", False
    oHTTP.Send
    If Err.Number = 0 And oHTTP.Status = 200 Then
        alive = True
    End If
    On Error GoTo 0

    If Not alive Then
        WshShell.CurrentDirectory = "C:\Users\xtech\Projects\rclone-manager\backend"
        WshShell.Run "cmd /c .venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8001 >> service.log 2>&1", 0, False
        WScript.Sleep 15000
    End If

    WScript.Sleep 10000
Loop
