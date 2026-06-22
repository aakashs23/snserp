"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { createClient } from "@/utils/supabase/client"
import { Save, Eye, ArrowLeft } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import Link from "next/link"

interface Customer {
  id: string
  customer_name: string
  gst_number: string | null
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function InvoiceGeneratorPage() {
  const router = useRouter()
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(false)

  // Form state
  const [invoiceNumber, setInvoiceNumber] = useState("")
  const [customerId, setCustomerId] = useState("")
  const [invoiceDate, setInvoiceDate] = useState(new Date().toISOString().split("T")[0])
  const [monthOfSupply, setMonthOfSupply] = useState("")
  const [paymentMode, setPaymentMode] = useState("")
  const [units, setUnits] = useState("")
  const [rate, setRate] = useState("")
  const [openAccessCharges, setOpenAccessCharges] = useState("0")
  const [notes, setNotes] = useState("")

  // Calculated values
  const grossAmount = units && rate ? parseFloat(units) * parseFloat(rate) : 0
  const gstAmount = grossAmount * 0.18
  const tdsAmount = grossAmount * 0.01
  const oac = parseFloat(openAccessCharges) || 0
  const netAmount = grossAmount + gstAmount - tdsAmount - oac

  const getAuthHeaders = useCallback(async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${session?.access_token}`,
    }
  }, [])

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const headers = await getAuthHeaders()
        const res = await fetch(`${API_URL}/api/v1/customers`, { headers })
        if (res.ok) setCustomers(await res.json())
      } catch {
        toast.error("Failed to load customers")
      }
    }
    fetchCustomers()
  }, [getAuthHeaders])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!invoiceNumber || !customerId || !invoiceDate) {
      toast.error("Please fill in all required fields")
      return
    }

    setLoading(true)
    try {
      const headers = await getAuthHeaders()
      const body = {
        invoice_number: invoiceNumber,
        customer_id: customerId,
        invoice_date: invoiceDate,
        month_of_supply: monthOfSupply || null,
        payment_mode: paymentMode || null,
        units: units ? parseFloat(units) : null,
        rate: rate ? parseFloat(rate) : null,
        gross_amount: grossAmount || null,
        open_access_charges: oac,
        net_amount: netAmount || null,
        notes: notes || null,
        status: "draft",
      }

      const res = await fetch(`${API_URL}/api/v1/invoices`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      })

      if (res.ok) {
        toast.success("Invoice created successfully")
        router.push("/invoices/register")
      } else {
        const err = await res.json()
        toast.error(err.detail || "Failed to create invoice")
      }
    } catch {
      toast.error("Network error")
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (n: number) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(n)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/invoices/register"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
            Invoice Generator
          </h1>
          <p className="text-muted-foreground mt-1">
            Create a new invoice. GST (18%) and TDS (1%) are calculated automatically.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Left: Form Fields */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Invoice Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="invoice_number">Invoice Number *</Label>
                    <Input id="invoice_number" value={invoiceNumber} onChange={(e) => setInvoiceNumber(e.target.value)} placeholder="INV-2026-001" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="customer_id">Customer *</Label>
                    <Select value={customerId} onValueChange={setCustomerId} required>
                      <SelectTrigger>
                        <SelectValue placeholder="Select customer" />
                      </SelectTrigger>
                      <SelectContent>
                        {customers.map((c) => (
                          <SelectItem key={c.id} value={c.id}>{c.customer_name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="invoice_date">Invoice Date *</Label>
                    <Input id="invoice_date" type="date" value={invoiceDate} onChange={(e) => setInvoiceDate(e.target.value)} required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="month_of_supply">Month of Supply</Label>
                    <Input id="month_of_supply" type="month" value={monthOfSupply} onChange={(e) => setMonthOfSupply(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="payment_mode">Payment Mode</Label>
                    <Select value={paymentMode} onValueChange={setPaymentMode}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select mode" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                        <SelectItem value="cheque">Cheque</SelectItem>
                        <SelectItem value="cash">Cash</SelectItem>
                        <SelectItem value="upi">UPI</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Billing</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="units">Units</Label>
                    <Input id="units" type="number" step="0.001" value={units} onChange={(e) => setUnits(e.target.value)} placeholder="0.000" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="rate">Rate (₹/unit)</Label>
                    <Input id="rate" type="number" step="0.0001" value={rate} onChange={(e) => setRate(e.target.value)} placeholder="0.0000" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="open_access">Open Access Charges (₹)</Label>
                    <Input id="open_access" type="number" step="0.01" value={openAccessCharges} onChange={(e) => setOpenAccessCharges(e.target.value)} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notes">Notes</Label>
                  <Textarea id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional notes..." rows={3} />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right: Live Preview */}
          <div className="space-y-6">
            <Card className="sticky top-20">
              <CardHeader>
                <CardTitle>Amount Preview</CardTitle>
                <CardDescription>Live calculation</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Gross Amount</span>
                  <span className="font-medium">{formatCurrency(grossAmount)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">GST (18%)</span>
                  <span className="text-accent font-medium">+ {formatCurrency(gstAmount)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">TDS (1%)</span>
                  <span className="text-destructive font-medium">- {formatCurrency(tdsAmount)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Open Access</span>
                  <span className="text-destructive font-medium">- {formatCurrency(oac)}</span>
                </div>
                <Separator />
                <div className="flex justify-between text-lg font-bold">
                  <span>Net Amount</span>
                  <span>{formatCurrency(netAmount)}</span>
                </div>
              </CardContent>
            </Card>

            <div className="flex flex-col gap-3">
              <Button type="submit" className="w-full" disabled={loading}>
                <Save className="h-4 w-4 mr-2" />
                {loading ? "Saving..." : "Save Invoice"}
              </Button>
            </div>
          </div>
        </div>
      </form>
    </div>
  )
}
