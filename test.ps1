$gcc = "C:\Users\turintech\scoop\apps\mingw\current\bin\gcc.exe"
& $gcc -O2 -o mbw mbw.c
if (-not $?) { exit 1 }

.\mbw.exe -n 1 10 | Out-Null
if ($?) { Write-Host "PASS: all-tests run" } else { Write-Error "FAIL: all-tests run"; exit 1 }

$out = .\mbw.exe 2>&1
if ($out -match "no array size") { Write-Host "PASS: missing arg error" } else { Write-Error "FAIL: missing arg error"; exit 1 }

$out = .\mbw.exe -n 1 0 2>&1
if ($out -match "array size wrong") { Write-Host "PASS: zero-size error" } else { Write-Error "FAIL: zero-size error"; exit 1 }

Write-Host "All tests passed."
exit 0
