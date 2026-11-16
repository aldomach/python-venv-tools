param([ValidateSet('Add','Remove')][string]$Action,[Parameter(Mandatory=$true)][string]$Directory)
$ErrorActionPreference = 'Stop'
$key = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey('Environment')
try {
 $old = [string]$key.GetValue('Path','',[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
 $parts = @($old -split ';' | Where-Object { $_ -and $_.TrimEnd('\') -ine $Directory.TrimEnd('\') })
 if ($Action -eq 'Add') { $parts += $Directory }
 $key.SetValue('Path',($parts -join ';'),[Microsoft.Win32.RegistryValueKind]::ExpandString)
} finally { $key.Close() }
Add-Type -Namespace Native -Name Broadcast -MemberDefinition '[System.Runtime.InteropServices.DllImport("user32.dll", CharSet=System.Runtime.InteropServices.CharSet.Auto)] public static extern System.IntPtr SendMessageTimeout(System.IntPtr hWnd, uint Msg, System.UIntPtr wParam, string lParam, uint flags, uint timeout, out System.UIntPtr result);'
$result=[UIntPtr]::Zero
[void][Native.Broadcast]::SendMessageTimeout([IntPtr]0xffff,0x1a,[UIntPtr]::Zero,'Environment',2,2000,[ref]$result)
