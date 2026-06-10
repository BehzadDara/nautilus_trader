# Sync the Kalshi adapter from the git source tree into the installed wheel (site-packages)
# so it runs against the compiled framework. See KALSHI_ADAPTER_IMPLEMENTATION.md (dev layout).
$src = "D:\Projects\Nautilustrader\nautilus_trader\adapters\kalshi"
$dst = "D:\Projects\Nautilustrader\.venv\Lib\site-packages\nautilus_trader\adapters\kalshi"
if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
Copy-Item -Recurse $src $dst
Write-Output "Synced kalshi/ -> site-packages"
