"use client"

import { useState, useEffect, useCallback } from "react"
import { File, Search, Trash2, RefreshCcw, Clock } from "lucide-react"
import { toast } from "sonner"
import { createClient } from "@/utils/supabase/client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"

interface DocRecord {
  id: string
  file_name: string
  original_name: string
  file_size: number
  mime_type: string
  upload_date: string
  deleted_at: string | null
  // AI and metadata fields (flattened from combined response)
  ai_category: string | null
  ai_status: string
  title: string | null
  description: string | null
  keywords: string[] | null
  summary: string | null
  processed_at: string | null
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function TrashPage() {
  const [documents, setDocuments] = useState<DocRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")

  const getAuthHeaders = useCallback(async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    return {
      "Authorization": `Bearer ${session?.access_token}`,
    }
  }, [])

  const fetchDocuments = useCallback(async () => {
    try {
      const headers = await getAuthHeaders()
      const url = new URL(`${API_URL}/api/v1/documents/trash/list`)
      if (search) url.searchParams.set("search", search)
      
      const res = await fetch(url.toString(), { 
        headers: {
          ...headers,
          "Content-Type": "application/json"
        }
      })
      if (res.ok) {
        setDocuments(await res.json())
      }
    } catch {
      toast.error("Failed to load trash")
    } finally {
      setLoading(false)
    }
  }, [search, getAuthHeaders])

  useEffect(() => {
    const t = setTimeout(() => fetchDocuments(), 0)
    return () => clearTimeout(t)
  }, [fetchDocuments])

  const handleRestore = async (id: string) => {
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/documents/${id}/restore`, {
        method: "POST",
        headers: {
          ...headers,
          "Content-Type": "application/json"
        }
      })
      if (res.ok) {
        toast.success("Document restored")
        fetchDocuments()
      } else {
        toast.error("Failed to restore document")
      }
    } catch {
      toast.error("Network error")
    }
  }

  const handlePermanentDelete = async (id: string) => {
    if (!confirm("Are you sure you want to permanently delete this document? This action cannot be undone.")) return;
    
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/documents/${id}/permanent`, {
        method: "DELETE",
        headers: {
          ...headers,
          "Content-Type": "application/json"
        }
      })
      if (res.ok) {
        toast.success("Document permanently deleted")
        fetchDocuments()
      } else {
        toast.error("Failed to permanently delete document")
      }
    } catch {
      toast.error("Network error")
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 B"
    const k = 1024
    const sizes = ["B", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric"
    })
  }

  const calculateDaysLeft = (deletedAtStr: string | null) => {
    if (!deletedAtStr) return 30;
    const deletedAt = new Date(deletedAtStr);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - deletedAt.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    const left = 30 - diffDays;
    return left > 0 ? left : 0;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Trash Bin</h1>
          <p className="text-muted-foreground mt-2">
            Documents deleted here will be permanently removed after 30 days.
          </p>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="p-4 border-b flex items-center justify-between gap-4 bg-muted/20">
            <div className="relative max-w-sm flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input 
                placeholder="Search trash..." 
                className="pl-9 bg-background"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Deleted On</TableHead>
                <TableHead>Days Left</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                    <TableCell><Skeleton className="h-8 w-20 ml-auto" /></TableCell>
                  </TableRow>
                ))
              ) : documents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">
                    <div className="flex flex-col items-center gap-2">
                      <Trash2 className="h-8 w-8 opacity-20" />
                      <p>Trash is empty.</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                documents.map((doc) => {
                  const daysLeft = calculateDaysLeft(doc.deleted_at);
                  return (
                    <TableRow key={doc.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <File className="h-4 w-4 text-muted-foreground" />
                          <span className="truncate max-w-[200px]" title={doc.original_name}>
                            {doc.original_name}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {formatSize(doc.file_size)}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {doc.deleted_at ? formatDate(doc.deleted_at) : formatDate(doc.upload_date)}
                      </TableCell>
                      <TableCell>
                        <Badge variant={daysLeft < 7 ? "destructive" : "secondary"} className="gap-1 font-medium">
                          <Clock className="h-3 w-3" />
                          {daysLeft} days
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button 
                            variant="outline" 
                            size="sm"
                            className="h-8"
                            onClick={() => handleRestore(doc.id)}
                          >
                            <RefreshCcw className="h-4 w-4 mr-1.5" />
                            Restore
                          </Button>
                          <Button 
                            variant="destructive" 
                            size="sm"
                            className="h-8"
                            onClick={() => handlePermanentDelete(doc.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                            <span className="sr-only">Delete</span>
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
