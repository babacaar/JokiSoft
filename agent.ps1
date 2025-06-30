# agent.ps1 — Agent HTTP local pour inventaire logiciel et déploiement
$port = 8080
$listener = New-Object System.Net.HttpListener
$prefix = "http://+:{0}/" -f $port
$listener.Prefixes.Add($prefix)
$listener.Start()
Write-Output "Agent PowerShell actif sur le port $port"

while ($true) {
    $context = $listener.GetContext()
    $request = $context.Request
    $response = $context.Response
    $url = $request.Url.AbsolutePath
    $method = $request.HttpMethod
    $apiKey = $request.Headers["X-Api-Key"]

    if ($apiKey -ne "SECRET123") {
        $response.StatusCode = 403
        $response.Close()
        continue
    }

    if ($url -eq "/inventory" -and $method -eq "GET") {
        $softs = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* |
            Where-Object { $_.DisplayName } |
            Select-Object DisplayName, DisplayVersion |
            ConvertTo-Json -Depth 3
        $buffer = [System.Text.Encoding]::UTF8.GetBytes($softs)
    }
    elseif ($url -eq "/deploy" -and $method -eq "POST") {
        $reader = New-Object IO.StreamReader $request.InputStream, [System.Text.Encoding]::UTF8
        $bodyRaw = $reader.ReadToEnd()
        $reader.Close()
        $body = $bodyRaw | ConvertFrom-Json
        $cmd = $body.install_command
        Start-Process powershell -ArgumentList "-Command", $cmd -WindowStyle Hidden
        $buffer = [System.Text.Encoding]::UTF8.GetBytes('{"status":"installing"}')
    }
    else {
        $response.StatusCode = 404
        $buffer = [System.Text.Encoding]::UTF8.GetBytes('{"error":"Not found"}')
    }

    $response.ContentLength64 = $buffer.Length
    $response.OutputStream.Write($buffer, 0, $buffer.Length)
    $response.Close()
}
