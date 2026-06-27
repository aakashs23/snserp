"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { UploadCloud, File, Search, Trash2, Eye, Download, FileText, CheckCircle2, Clock, Share2 } from "lucide-react"
import { toast } from "sonner"
import { createClient } from "@/utils/supabase/client"
import { useAuth } from "@/components/providers/auth-provider"
import { DocumentPermissionsDialog } from "@/components/document-permissions-dialog"

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

export default function DocumentsPage() {
  const { roleName } = useAuth()
  const [documents, setDocuments] = useState<DocRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [uploading, setUploading] = useState(false)
  const [permissionsDocId, setPermissionsDocId] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

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
      const url = new URL(`${API_URL}/api/v1/documents`)
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
      toast.error("Failed to load documents")
    } finally {
      setLoading(false)
    }
  }, [search, getAuthHeaders])

  useEffect(() => {
    const t = setTimeout(() => fetchDocuments(), 0)
    return () => clearTimeout(t)
  }, [fetchDocuments])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append("file", file)

    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/documents/upload`, {
        method: "POST",
        headers, // Do not set Content-Type, let browser set boundary for multipart
        body: formData,
      })
      
      if (res.ok) {
        toast.success("Document uploaded successfully")
        fetchDocuments()
      } else {
        const err = await res.json()
        toast.error(err.detail || "Failed to upload")
      }
    } catch {
      toast.error("Network error during upload")
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
    }
  }

  const handleDownload = async (id: string) => {
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/documents/${id}/download`, { headers })
      if (res.ok) {
        const data = await res.json()
        window.open(data.url, "_blank")
      } else {
        const err = await res.json()
        toast.error(err.detail || "Failed to get download link")
      }
    } catch {
      toast.error("Network error")
    }
  }

  const handleDelete = async (id: string) => {
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/documents/${id}`, {
        method: "DELETE",
        headers: {
          ...headers,
          "Content-Type": "application/json"
        }
      })
      if (res.ok) {
        toast.success("Document deleted")
        fetchDocuments()
      } else {
        toast.error("Failed to delete document")
      }
    } catch {
      toast.error("Network error")
    }
  }

  const handlePreview = async (id: string) => {
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/documents/${id}/preview`, {
        headers: {
          ...headers,
          "Content-Type": "application/json"
        }
      })
      if (res.ok) {
        const data = await res.json()
        window.open(data.url, "_blank")
      } else {
        toast.error("Could not generate preview link")
      }
    } catch {
      toast.error("Network error")
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (d: string) => new Date(d).toLocaleDateString("en-IN", {
    day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
            Documents
          </h1>
          <p className="text-muted-foreground mt-1">
            Upload and manage company files. AI automatically categorizes and indexes them for search.
          </p>
        </div>
        
        {roleName !== "viewer" && (
          <div>
            <input 
              type="file" 
              className="hidden" 
              ref={fileInputRef} 
              onChange={handleUpload}
              accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
            />
            <Button onClick={() => fileInputRef.current?.click()} disabled={uploading}>
              <UploadCloud className="h-4 w-4 mr-2" />
              {uploading ? "Uploading..." : "Upload Document"}
            </Button>
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by original filename..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Uploaded</TableHead>
                <TableHead>AI Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                    <TableCell><Skeleton className="h-8 w-20 ml-auto" /></TableCell>
                  </TableRow>
                ))
              ) : documents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                    <div className="flex flex-col items-center gap-2">
                      <FileText className="h-8 w-8 opacity-20" />
                      <p>No documents found.</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                documents.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <File className="h-4 w-4 text-muted-foreground" />
                        <span className="truncate max-w-[200px]" title={doc.original_name}>
                          {doc.original_name}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="bg-muted">
                        {doc.ai_status === "completed" && doc.ai_category ? (
                          <div className="flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3" />
                            {doc.ai_category}
                          </div>
                        ) : doc.ai_category ? (
                          doc.ai_category
                        ) : (
                          "Processing..."
                        )}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {formatSize(doc.file_size)}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {formatDate(doc.upload_date)}
                    </TableCell>
                    <TableCell>
                      {doc.ai_status === "completed" ? (
                        <div className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                          <CheckCircle2 className="h-4 w-4" /> Indexed
                        </div>
                      ) : doc.ai_status === "failed" ? (
                        <div className="flex items-center gap-1 text-destructive text-sm">
                          <CheckCircle2 className="h-4 w-4" /> Failed
                        </div>
                      ) : (
                        <div className="flex items-center gap-1 text-muted-foreground text-sm">
                          <Clock className="h-4 w-4" /> Pending
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon" onClick={() => handlePreview(doc.id)} title="Preview">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDownload(doc.id)} title="Download">
                          <Download className="h-4 w-4" />
                        </Button>
                        {roleName === "admin" && (
                          <Button variant="ghost" size="icon" onClick={() => setPermissionsDocId(doc.id)} title="Manage Permissions">
                            <Share2 className="h-4 w-4 text-blue-500" />
                          </Button>
                        )}
                        {roleName !== "viewer" && (
                          <Button variant="ghost" size="icon" className="text-destructive" onClick={() => handleDelete(doc.id)} title="Delete">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <DocumentPermissionsDialog
        documentId={permissionsDocId}
        open={!!permissionsDocId}
        onOpenChange={(open) => !open && setPermissionsDocId(null)}
      />
    </div>
  )
}
