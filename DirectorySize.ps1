Function Get-DirectorySize ($directory) {
    $size = 0
    Get-ChildItem -recurse -Path $directory | Select-Object Length | foreach{$size += $_.Length}
    
    return $size
}

$args_length = $args.length
if ($args_length -eq 0) {
    Write-Warning "Must supply directory name."
    break
} else {
    if (!(Test-Path $args[0])) {
        Write-Warning "Directory not found."
        break
    }
    
    foreach($dir in $args) {
        $result = Get-DirectorySize($dir) 
        $result /= 1mb
        
        $output = "$dir " + "{0:N4}" -f $result + " MB"
        Write-Output $output
    }
}
