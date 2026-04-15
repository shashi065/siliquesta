$ports = 8000, 8080

foreach ($port in $ports) {
  $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($connection in $connections) {
    try {
      Stop-Process -Id $connection.OwningProcess -Force -ErrorAction Stop
      Write-Host "Stopped process on port $port (PID $($connection.OwningProcess))"
    } catch {
      Write-Host "Could not stop process on port $port (PID $($connection.OwningProcess))"
    }
  }
}
