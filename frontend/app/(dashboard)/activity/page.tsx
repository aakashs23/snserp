"use client"

import { useState, useEffect, useCallback } from "react"
import { Activity, ShieldAlert, FileText, User as UserIcon, LogIn, HardDrive } from "lucide-react"
import { toast } from "sonner"
import { createClient } from "@/utils/supabase/client"
import { format } from "date-fns"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"

interface ActivityLog {
  id: number
  action: string
  entity_type: string | null
  module: string | null
  object_affected: string | null
  ip_address: string | null
  created_at: string
  user_name: string | null
  user_email: string | null
}

import { RoleGuard } from "@/components/role-guard"
import { ExportMenu } from "@/components/ui/export-menu"
import { downloadFile } from "@/lib/utils"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function ActivityLogsPage() {
  const [logs, setLogs] = useState<ActivityLog[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  const fetchLogs = useCallback(async (pageNum: number) => {
    setLoading(true)

    try {
      const supabase = createClient()
      const {
        data: { session },
      } = await supabase.auth.getSession()

      const res = await fetch(`${API_URL}/api/v1/activity?page=${pageNum}&size=20`, {
        headers: {
          Authorization: `Bearer ${session?.access_token}`,
        },
      })

      if (res.ok) {
        const data = await res.json()
        setLogs(data.items)
        setTotal(data.total)
      } else {
        toast.error("Failed to load activity logs")
      }
    } catch {
      toast.error("Network error")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => fetchLogs(page), 0)
    return () => clearTimeout(t)
  }, [page, fetchLogs])

  const handleExport = async (format: "csv" | "xlsx" | "pdf") => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      const res = await fetch(`${API_URL}/api/v1/activity/export?format=${format}`, {
        headers: { Authorization: `Bearer ${session?.access_token}` },
      })
      if (!res.ok) throw new Error("Export failed")
        
      const blob = await res.blob()
      const ext = format === "xlsx" ? "xlsx" : format
      downloadFile(blob, `activity_logs_${new Date().getTime()}.${ext}`)
    } catch (error) {
      toast.error("Failed to export data")
    }
  }

  const getActionIcon = (action: string) => {
    const normalizedAction = action.toLowerCase()

    if (normalizedAction.includes("delete")) {
      return <ShieldAlert className="size-4 text-destructive" />
    }
    if (normalizedAction.includes("document") || normalizedAction.includes("invoice")) {
      return <FileText className="size-4 text-primary" />
    }
    if (normalizedAction.includes("login")) {
      return <LogIn className="size-4 text-chart-2" />
    }
    if (normalizedAction.includes("user")) {
      return <UserIcon className="size-4 text-chart-4" />
    }

    return <HardDrive className="size-4 text-muted-foreground" />
  }

  const totalPages = Math.ceil(total / 20)

  return (
    <RoleGuard allowedRoles={["admin"]}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
              Activity Logs
            </h1>
            <p className="text-muted-foreground mt-1">
              System audit trail for security and monitoring.
            </p>
          </div>
          <ExportMenu onExport={handleExport} />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="size-5" />
              Audit Trail
            </CardTitle>
            <CardDescription>Recent actions performed by users.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Module</TableHead>
                    <TableHead>Object Affected</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    Array.from({ length: 5 }).map((_, i) => (
                      <TableRow key={i}>
                        <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-48" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-48" /></TableCell>
                      </TableRow>
                    ))
                  ) : logs.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-10 text-muted-foreground">
                        No activity logs found.
                      </TableCell>
                    </TableRow>
                  ) : (
                    logs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="whitespace-nowrap text-sm text-muted-foreground">
                          {format(new Date(log.created_at), "dd MMM yyyy, HH:mm")}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="font-medium text-sm">{log.user_name || "System"}</span>
                            <span className="text-xs text-muted-foreground">{log.user_email || "N/A"}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {getActionIcon(log.action)}
                            <span className="text-sm">{log.action}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          {log.module ? (
                            <Badge variant="outline" className="text-xs">{log.module}</Badge>
                          ) : (
                            <span className="text-muted-foreground text-xs">{log.entity_type || "-"}</span>
                          )}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {log.object_affected || "-"}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                Showing {Math.min(total, (page - 1) * 20 + 1)} to {Math.min(total, page * 20)} of {total} entries
              </div>
              <div className="flex items-center gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1 || loading}
                >
                  Previous
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages || loading}
                >
                  Next
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  )
}
