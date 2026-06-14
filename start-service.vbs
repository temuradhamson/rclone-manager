Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\xtech\Projects\rclone-manager\backend"
WshShell.Run "cmd /c .venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8001 > service.log 2>&1", 0, False
