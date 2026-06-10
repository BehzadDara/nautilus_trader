$src = "D:\Projects\Nautilustrader\nautilus_trader\adapters\kalshi"
$dst = "D:\Projects\Nautilustrader\.venv\Lib\site-packages\nautilus_trader\adapters\kalshi"
if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
Copy-Item -Recurse $src $dst
