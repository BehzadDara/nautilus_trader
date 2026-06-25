& "$PSScriptRoot\sync_to_venv.ps1"
$k = "D:\Projects\Nautilustrader\tests\integration_tests\adapters\kalshi"
Push-Location $env:TEMP
& "D:\Projects\Nautilustrader\.venv\Scripts\python.exe" -m pytest $k -c "$k\pytest.ini" --rootdir $k --import-mode=importlib -q
Pop-Location
