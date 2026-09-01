# outlook.ps1 — Outlook COM 操作工具(直连经典 Outlook,不依赖 MCP)
#
# 用法:
#   添加日程  .\outlook.ps1 -Action add-calendar -Subject "主题" -Start "2026-09-15 09:00" -End "2026-09-15 11:00" [-Location 地点] [-Body 备注] [-AllDay] [-ReminderMinutes 15]
#   查询日历  .\outlook.ps1 -Action list-calendar -DateFrom "2026-09-01 00:00" -DateTo "2026-09-30 00:00"
#   列出邮件  .\outlook.ps1 -Action list-mails [-Folder Inbox] [-UnreadOnly] [-Limit 50]
#   读取邮件  .\outlook.ps1 -Action get-mail -EntryId "邮件EntryID"
#   新建草稿  .\outlook.ps1 -Action create-draft -To "a@x.com","b@x.com" [-Cc ...] [-Bcc ...] -Subject "主题" [-Body 正文] [-AttachmentPaths "C:\a.pdf"]
#
# 注意:
#   - New-Object -ComObject Outlook.Application 会自动启动经典 Outlook(如果没开),无需预先手动打开
#   - 本脚本以 UTF-8 输出,保证中文不乱码;文件本身必须为 UTF-8 带 BOM,否则 Windows PowerShell 5.1 会按 GBK 解析中文

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('add-calendar', 'list-calendar', 'update-calendar', 'delete-calendar', 'list-folders', 'list-mails', 'get-mail', 'create-draft', 'update-draft', 'delete-draft')]
    [string]$Action,

    # --- 日程字段 ---
    [string]$Subject,
    [string]$Start,
    [string]$End,
    [string]$Location,
    [string]$Body,
    [switch]$AllDay,
    [int]$ReminderMinutes = -1,

    # --- 日历查询 ---
    [string]$DateFrom,
    [string]$DateTo,

    # --- 邮件 ---
    [string]$Folder = 'Inbox',
    [switch]$UnreadOnly,
    [int]$Limit = 50,
    [string]$EntryId,

    # --- 草稿 ---
    [string[]]$To,
    [string[]]$Cc,
    [string[]]$Bcc,
    [string[]]$AttachmentPaths
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 建立 COM 会话。优先复用已运行的 Outlook;拿不到则新建(COM 会自动拉起进程)。
# Outlook 忙时(启动/同步中)会拒绝调用(RPC_E_CALL_REJECTED),故带重试等待。
function Connect-Outlook {
    $app = $null
    try {
        $app = [System.Runtime.InteropServices.Marshal]::GetActiveObject('Outlook.Application')
    } catch {
        # 无运行实例,走新建
    }
    if (-not $app) {
        for ($attempt = 1; $attempt -le 6; $attempt++) {
            try {
                $app = New-Object -ComObject Outlook.Application
                break
            } catch {
                if ($attempt -ge 6) { throw }
                Start-Sleep -Seconds 2
            }
        }
    }
    return $app
}

# 按 EntryID 在所有 Store 中定位邮件/日程项。
function Find-ItemByEntryId($ns, $entryId) {
    foreach ($store in $ns.Stores) {
        try {
            $item = $ns.GetItemFromID($entryId, $store.ID)
            if ($item) { return $item }
        } catch {
            # 该 Store 中没有此 ID,继续下一个
        }
    }
    return $null
}

# 递归搜索子文件夹。
function Search-Folder($folder, $name) {
    if ($folder.Name -eq $name) { return $folder }
    foreach ($sub in $folder.Folders) {
        $r = Search-Folder $sub $name
        if ($r) { return $r }
    }
    return $null
}

# 按名字解析邮件文件夹:优先常见默认文件夹,否则递归搜索整个文件夹树。
function Resolve-Folder($ns, $name) {
    $map = @{
        'inbox' = 6; '收件箱' = 6
        'drafts' = 16; '草稿' = 16
        'sent' = 5; 'sentitems' = 5; 'sent items' = 5; '已发送' = 5
        'outbox' = 4; '发件箱' = 4
        'deleted' = 3; 'deleteditems' = 3; '已删除' = 3
        'junk' = 23; 'junkemail' = 23; '垃圾邮件' = 23
    }
    $key = $name.ToLowerInvariant()
    if ($map.ContainsKey($key)) {
        return $ns.GetDefaultFolder($map[$key])
    }
    foreach ($root in $ns.Folders) {
        $found = Search-Folder $root $name
        if ($found) { return $found }
    }
    return $null
}

function Add-CalendarEntry($ns) {
    if (-not $Start -or -not $End) { throw 'add-calendar 必须提供 -Start 和 -End' }

    $cal = $ns.GetDefaultFolder(9)          # olFolderCalendar
    $item = $cal.Items.Add(1)               # olAppointmentItem
    $item.Subject = $Subject

    $startDt = [datetime]::Parse($Start)
    $endDt = [datetime]::Parse($End)

    if ($AllDay) {
        $item.AllDayEvent = $true
        $item.Start = $startDt.Date
        # 全天事件:End 与 Start 同日时自动顺延一天,符合 Outlook 惯例
        if ($endDt.Date -le $startDt.Date) {
            $item.End = $startDt.Date.AddDays(1)
        } else {
            $item.End = $endDt.Date
        }
    } else {
        $item.Start = $startDt
        $item.End = $endDt
    }

    if ($Location) { $item.Location = $Location }
    if ($Body) { $item.Body = $Body }

    if ($ReminderMinutes -ge 0) {
        $item.ReminderSet = $true
        $item.ReminderMinutesBeforeStart = $ReminderMinutes
    } elseif ($AllDay) {
        $item.ReminderSet = $false          # 全天事件默认不弹提醒,避免打扰
    }

    $item.Save()
    Write-Output "已创建日程: $($item.Subject)"
    Write-Output "  时间: $($item.Start.ToString('yyyy-MM-dd HH:mm')) - $($item.End.ToString('yyyy-MM-dd HH:mm'))"
    if ($item.Location) { Write-Output "  地点: $($item.Location)" }
    Write-Output "  EntryID: $($item.EntryID)"
}

function List-Calendar($ns) {
    $cal = $ns.GetDefaultFolder(9)
    $from = if ($DateFrom) { [datetime]::Parse($DateFrom) } else { (Get-Date).Date.AddDays(-30) }
    $to = if ($DateTo) { [datetime]::Parse($DateTo) } else { $from.AddMonths(3) }

    $count = 0
    $events = @()
    foreach ($ev in $cal.Items) {
        if ($ev.Class -ne 26) { continue }   # 只处理 olAppointment
        $s = [datetime]$ev.Start
        if ($s -lt $from -or $s -ge $to) { continue }
        $events += $ev
    }
    if ($events.Count -eq 0) {
        Write-Output "(该时间段内没有日程)"
    } else {
        $events | Sort-Object -Property Start | ForEach-Object {
            $loc = $_.Location
            if ($_.AllDayEvent) {
                $line = "[全天 $($_.Start.ToString('yyyy-MM-dd'))] $($_.Subject)"
            } else {
                $line = "[$($_.Start.ToString('yyyy-MM-dd HH:mm')) - $($_.End.ToString('HH:mm'))] $($_.Subject)"
            }
            if ($loc) { $line += "  @ $loc" }
            Write-Output $line
            Write-Output "    EntryID: $($_.EntryID)"
        }
    }
}

function List-Mails($ns) {
    $folder = Resolve-Folder $ns $Folder
    if (-not $folder) { throw "找不到文件夹: $Folder" }

    $mails = @()
    foreach ($msg in $folder.Items) {
        if ($msg.Class -ne 43) { continue }  # 只处理 olMail
        if ($UnreadOnly -and -not $msg.UnRead) { continue }
        $mails += $msg
    }
    if ($mails.Count -eq 0) {
        Write-Output "(没有符合条件的邮件)"
    } else {
        $mails | Sort-Object -Property ReceivedTime -Descending | Select-Object -First $Limit | ForEach-Object {
            $from = $_.SenderName
            if (-not $from) { $from = $_.SenderEmailAddress }
            $readFlag = if ($_.UnRead) { '未读' } else { '已读' }
            Write-Output "$readFlag | $($_.ReceivedTime.ToString('yyyy-MM-dd HH:mm')) | $from | $($_.Subject)"
            Write-Output "  EntryID: $($_.EntryID)"
        }
    }
}

function Get-Mail($ns) {
    if (-not $EntryId) { throw 'get-mail 必须提供 -EntryId' }
    $item = Find-ItemByEntryId $ns $EntryId
    if (-not $item) { throw "找不到该 EntryID 对应的邮件: $EntryId" }

    Write-Output "主题: $($item.Subject)"
    Write-Output "发件人: $($item.SenderName) <$($item.SenderEmailAddress)>"
    Write-Output "收件人: $($item.To)"
    if ($item.CC) { Write-Output "抄送: $($item.CC)" }
    Write-Output "时间: $($item.ReceivedTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Output "已读: $(if ($item.UnRead) { '否' } else { '是' })"
    if ($item.Attachments.Count -gt 0) {
        Write-Output "附件 ($($item.Attachments.Count) 个):"
        foreach ($att in $item.Attachments) {
            Write-Output "  - $($att.FileName) ($([math]::Round($att.Size / 1KB, 1)) KB)"
        }
    }
    Write-Output "---- 正文 ----"
    Write-Output $item.Body
}

# 将纯文本转换为 HTML 正文。
# 原因:本机 COM 实例下 MailItem.Body 属性写入/读回会损坏非 ASCII 文本(出现 U+FFFD 与内容重复),
# 而 HTMLBody 属性经实测完全正常,故所有正文统一走 HTMLBody。
function ConvertTo-HtmlBody($text) {
    $escaped = $text -replace '&', '&amp;' -replace '<', '&lt;' -replace '>', '&gt;'
    $escaped = $escaped -replace "`r`n", '<br>' -replace "`n", '<br>'
    return "<html><body>$escaped</body></html>"
}

function Create-Draft($ns) {
    $mail = $app.CreateItem(0)              # olMailItem
    if ($To) { $mail.To = $To -join ';' }
    if ($Cc) { $mail.CC = $Cc -join ';' }
    if ($Bcc) { $mail.BCC = $Bcc -join ';' }
    if ($Subject) { $mail.Subject = $Subject }
    if ($Body) {
        if ($Body -match '<[a-zA-Z][^>]*>') {
            $mail.HTMLBody = $Body          # 含标签视为 HTML
        } else {
            $mail.HTMLBody = ConvertTo-HtmlBody $Body   # 纯文本走 HTMLBody,规避 Body 编码 bug
        }
    }
    if ($AttachmentPaths) {
        foreach ($p in $AttachmentPaths) {
            $resolved = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($p)
            if (Test-Path $resolved) {
                $mail.Attachments.Add($resolved) | Out-Null
            } else {
                Write-Warning "附件不存在,已跳过: $p"
            }
        }
    }
    $mail.Save()                            # 保存到草稿箱,不发送
    Write-Output "草稿已保存: $($mail.Subject)"
    Write-Output "  EntryID: $($mail.EntryID)"
    Write-Output "  收件人: $($mail.To)"
}

# 递归输出文件夹树。
function Write-FolderTree($folder, $indent) {
    Write-Output "$indent$($folder.Name)"
    foreach ($sub in $folder.Folders) {
        Write-FolderTree $sub ($indent + '  ')
    }
}

# 列出整个文件夹树(每个账号一个根)。
function List-Folders($ns) {
    foreach ($root in $ns.Folders) {
        Write-FolderTree $root ''
    }
}

# 更新日程:只改传入的字段。
function Update-Calendar($ns) {
    if (-not $EntryId) { throw 'update-calendar 必须提供 -EntryId' }
    $item = Find-ItemByEntryId $ns $EntryId
    if (-not $item) { throw "找不到该 EntryID 对应的日程: $EntryId" }

    if ($Subject) { $item.Subject = $Subject }
    if ($Start) { $item.Start = [datetime]::Parse($Start) }
    if ($End) { $item.End = [datetime]::Parse($End) }
    if ($AllDay.IsPresent) { $item.AllDayEvent = $true }
    if ($Location) { $item.Location = $Location }
    if ($Body) { $item.Body = $Body }
    if ($ReminderMinutes -ge 0) {
        $item.ReminderSet = $true
        $item.ReminderMinutesBeforeStart = $ReminderMinutes
    }
    $item.Save()
    Write-Output "已更新日程: $($item.Subject)"
    Write-Output "  时间: $($item.Start.ToString('yyyy-MM-dd HH:mm')) - $($item.End.ToString('HH:mm'))"
    if ($item.Location) { Write-Output "  地点: $($item.Location)" }
}

# 删除日程。
function Delete-Calendar($ns) {
    if (-not $EntryId) { throw 'delete-calendar 必须提供 -EntryId' }
    $item = Find-ItemByEntryId $ns $EntryId
    if (-not $item) { throw "找不到该 EntryID 对应的日程: $EntryId" }
    $subj = $item.Subject
    $item.Delete()
    Write-Output "已删除日程: $subj"
}

# 更新草稿:只改传入的字段,可追加附件。
function Update-Draft($ns) {
    if (-not $EntryId) { throw 'update-draft 必须提供 -EntryId' }
    $item = Find-ItemByEntryId $ns $EntryId
    if (-not $item) { throw "找不到该 EntryID 对应的草稿: $EntryId" }

    if ($To) { $item.To = $To -join ';' }
    if ($Cc) { $item.CC = $Cc -join ';' }
    if ($Bcc) { $item.BCC = $Bcc -join ';' }
    if ($Subject) { $item.Subject = $Subject }
    if ($Body) {
        if ($Body -match '<[a-zA-Z][^>]*>') {
            $item.HTMLBody = $Body
        } else {
            $item.HTMLBody = ConvertTo-HtmlBody $Body   # 纯文本走 HTMLBody,规避 Body 编码 bug
        }
    }
    if ($AttachmentPaths) {
        foreach ($p in $AttachmentPaths) {
            $resolved = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($p)
            if (Test-Path $resolved) {
                $item.Attachments.Add($resolved) | Out-Null
            } else {
                Write-Warning "附件不存在,已跳过: $p"
            }
        }
    }
    $item.Save()
    Write-Output "已更新草稿: $($item.Subject)"
}

# 删除草稿。
function Delete-Draft($ns) {
    if (-not $EntryId) { throw 'delete-draft 必须提供 -EntryId' }
    $item = Find-ItemByEntryId $ns $EntryId
    if (-not $item) { throw "找不到该 EntryID 对应的草稿: $EntryId" }
    $subj = $item.Subject
    $item.Delete()
    Write-Output "已删除草稿: $subj"
}

# ---- 主逻辑 ----
$app = Connect-Outlook
$ns = $app.GetNamespace('MAPI')
switch ($Action) {
    'add-calendar'    { Add-CalendarEntry $ns }
    'list-calendar'   { List-Calendar $ns }
    'update-calendar' { Update-Calendar $ns }
    'delete-calendar' { Delete-Calendar $ns }
    'list-folders'    { List-Folders $ns }
    'list-mails'      { List-Mails $ns }
    'get-mail'        { Get-Mail $ns }
    'create-draft'    { Create-Draft $ns }
    'update-draft'    { Update-Draft $ns }
    'delete-draft'    { Delete-Draft $ns }
}
