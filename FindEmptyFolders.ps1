Function Find-EmptyDirectories ($directory) {
    $result = @()
    $dirs = Get-ChildItem -recurse -Path $directory | Where-Object {$_.PSIsContainer -eq $True}

    foreach($file in $dirs) {
        if($file.GetFileSystemInfos().Count -eq 0) {
            $result += $file.FullName
        }
    }
    
    return $result
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
    
    $result = Find-EmptyDirectories $args[0] 
    
    Write-Output $result
}
