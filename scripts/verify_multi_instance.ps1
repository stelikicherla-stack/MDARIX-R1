param([string[]]$BaseUrls = @('http://127.0.0.1:8007','http://127.0.0.1:8008'))
foreach ($url in $BaseUrls) {
  $health = Invoke-RestMethod "$url/health"
  if ($health.status -ne 'ok') { throw "Health failed: $url" }
  Write-Host "PASS | $url | $($health.status) | $($health.database)"
}
Write-Host 'Manual gate: sign in once, call /api/v1/auth/session against both URLs with the same cookie, then revoke and verify both reject it.'
