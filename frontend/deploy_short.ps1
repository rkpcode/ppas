$lines = Get-Content "d:\New folder\.env"
foreach ($line in $lines) {
    if ($line -match '^\s*([A-Za-z0-9_]+)=(.*)$') {
        $key = $matches[1]
        $val = $matches[2]
        [System.Environment]::SetEnvironmentVariable($key, $val, [System.EnvironmentVariableTarget]::Process)
    }
}

npm run build
npx wrangler deploy
