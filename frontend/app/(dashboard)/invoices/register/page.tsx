"use client"

import { useState, useEffect, useCallback } from "react"
import { FilePlus, Search, Download, Eye } from "lucide-react"
import Link from "next/link"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"

interface Invoice {
  id: string
  invoice_number: string
  customer_id: string
  invoice_date: string
  month_of_supply: string | null
  gross_amount: number | null
  net_amount: number | null
  gst_amount: number | null
  tds_amount: number | null
  status: string | null
  payment_date: string | null
  created_at: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  draft: "secondary",
  sent: "outline",
  paid: "default",
  overdue: "destructive",
  cancelled: "destructive",
}

const statusLabel: Record<string, string> = {
  draft: "Draft",
  sent: "Sent",
  paid: "Paid",
  overdue: "Overdue",
  cancelled: "Cancelled",
}

export default function InvoiceRegisterPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState("all")

  const getAuthHeaders = useCallback(async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${session?.access_token}`,
    }
  }, [])

  const fetchInvoices = useCallback(async () => {
    try {
      const headers = await getAuthHeaders()
      const url = new URL(`${API_URL}/api/v1/invoices`)
      if (statusFilter !== "all") url.searchParams.set("status", statusFilter)
      const res = await fetch(url.toString(), { headers })
      if (res.ok) {
        setInvoices(await res.json())
      }
    } catch {
      toast.error("Failed to fetch invoices")
    } finally {
      setLoading(false)
    }
  }, [statusFilter, getAuthHeaders])

  useEffect(() => {
    fetchInvoices()
  }, [fetchInvoices])

  const formatCurrency = (n: number | null) =>
    n != null
      ? new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(n)
      : "—"

  const formatDate = (d: string | null) =>
    d ? new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—"

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
            Invoice Register
          </h1>
          <p className="text-muted-foreground mt-1">
            View and manage all invoices.
          </p>
        </div>
        <Button asChild>
          <Link href="/invoices/generator">
            <FilePlus className="h-4 w-4 mr-2" />
            New Invoice
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setLoading(true); }}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="sent">Sent</SelectItem>
            <SelectItem value="paid">Paid</SelectItem>
            <SelectItem value="overdue">Overdue</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice #</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Month</TableHead>
                <TableHead className="text-right">Gross</TableHead>
                <TableHead className="text-right">GST (18%)</TableHead>
                <TableHead className="text-right">TDS (1%)</TableHead>
                <TableHead className="text-right">Net Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Payment Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 9 }).map((_, j) => (
                      <TableCell key={j}><Skeleton className="h-4 w-20" /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : invoices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-12 text-muted-foreground">
                    No invoices found. Click &ldquo;New Invoice&rdquo; to create one.
                  </TableCell>
                </TableRow>
              ) : (
                invoices.map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell className="font-medium font-mono">{inv.invoice_number}</TableCell>
                    <TableCell>{formatDate(inv.invoice_date)}</TableCell>
                    <TableCell>{inv.month_of_supply ? formatDate(inv.month_of_supply) : "—"}</TableCell>
                    <TableCell className="text-right font-mono">{formatCurrency(inv.gross_amount)}</TableCell>
                    <TableCell className="text-right font-mono text-accent">{formatCurrency(inv.gst_amount)}</TableCell>
                    <TableCell className="text-right font-mono text-destructive">{formatCurrency(inv.tds_amount)}</TableCell>
                    <TableCell className="text-right font-mono font-semibold">{formatCurrency(inv.net_amount)}</TableCell>
                    <TableCell>
                      <Badge variant={statusVariant[inv.status || "draft"] || "secondary"}>
                        {statusLabel[inv.status || "draft"] || inv.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(inv.payment_date)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
