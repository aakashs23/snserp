"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { createClient } from "@/utils/supabase/client"
import { Save, ArrowLeft, UploadCloud, FileSpreadsheet } from "lucide-react"

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

const buildMonthStartDate = (year: number, month: number) => {
  if (!Number.isInteger(year) || !Number.isInteger(month) || month < 1 || month > 12) {
    return null
  }
  return `${year}-${String(month).padStart(2, "0")}-01`
}

const normalizeMonthOfSupply = (value: string, invoiceDate: string) => {
  const raw = value.trim()
  if (!raw) return null
  if (/^\d{4}-\d{2}$/.test(raw)) return `${raw}-01`
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return `${raw.slice(0, 7)}-01`
  if (/^\d{1,2}[/-]\d{4}$/.test(raw)) {
    const [month, year] = raw.split(/[/-]/)
    return buildMonthStartDate(Number(year), Number(month))
  }
  if (/^\d{1,2}[/-]\d{1,2}[/-]\d{4}$/.test(raw)) {
    const [month, , year] = raw.split(/[/-]/)
    return buildMonthStartDate(Number(year), Number(month))
  }
  const invoiceYear = Number(invoiceDate.slice(0, 4))
  if (/^\d{1,2}$/.test(raw)) return buildMonthStartDate(invoiceYear, Number(raw))
  if (/^\d{1,2}[/-]\d{1,2}$/.test(raw)) {
    const [month] = raw.split(/[/-]/)
    return buildMonthStartDate(invoiceYear, Number(month))
  }
  const parsedWithYear = new Date(`${raw} 1`)
  if (!Number.isNaN(parsedWithYear.getTime())) {
    return buildMonthStartDate(parsedWithYear.getFullYear(), parsedWithYear.getMonth() + 1)
  }
  const parsedWithInvoiceYear = new Date(`${raw} 1, ${invoiceYear}`)
  if (!Number.isNaN(parsedWithInvoiceYear.getTime())) {
    return buildMonthStartDate(invoiceYear, parsedWithInvoiceYear.getMonth() + 1)
  }
  return null
}

import { RoleGuard } from "@/components/role-guard"

export default function InvoiceGeneratorPage() {
  const router = useRouter()
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(false)
  const [importMode, setImportMode] = useState<"manual" | "excel">("manual")
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [foundFields, setFoundFields] = useState<string[]>([])
  const [missingFields, setMissingFields] = useState<string[]>([])

  const [invoiceNumber, setInvoiceNumber] = useState("")
  const [customerId, setCustomerId] = useState("")
  const [invoiceDate, setInvoiceDate] = useState(new Date().toISOString().split("T")[0])
  const [monthOfSupply, setMonthOfSupply] = useState("")
  const [paymentMode, setPaymentMode] = useState("cheque")
  const [description, setDescription] = useState("Solar Power Allotted")
  const [units, setUnits] = useState("")
  const [rate, setRate] = useState("")
  const [openAccessCharges, setOpenAccessCharges] = useState("0")
  const [roundOff, setRoundOff] = useState("0")
  const [notes, setNotes] = useState("")

  const amount = (parseFloat(units) || 0) * (parseFloat(rate) || 0)
  const roundOffVal = parseFloat(roundOff) || 0
  const total = amount + roundOffVal
  const oac = parseFloat(openAccessCharges) || 0
  const netAmount = total - oac

  const getAuthHeaders = useCallback(async () => {
    const supabase = createClient()
    const {
      data: { session },
    } = await supabase.auth.getSession()

    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session?.access_token}`,
    }
  }, [])

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const headers = await getAuthHeaders()
        const res = await fetch(`${API_URL}/api/v1/customers`, { headers })

        if (res.ok) {
          setCustomers(await res.json())
        }
      } catch {
        toast.error("Failed to load customers")
      }
    }

    fetchCustomers()
  }, [getAuthHeaders])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]

    if (!file) {
      return
    }

    if (!file.name.endsWith(".xlsx")) {
      toast.error("This file is not a valid Excel document. Only .xlsx is supported.")
      return
    }

    setLoading(true)

    const formData = new FormData()
    formData.append("file", file)

    try {
      const headers: Record<string, string> = await getAuthHeaders()
      delete headers["Content-Type"]

      const res = await fetch(`${API_URL}/api/v1/invoices/parse-excel`, {
        method: "POST",
        headers,
        body: formData,
      })

      const data = await res.json()

      if (res.ok) {
        toast.success("Excel data extracted. Please review the populated form.")
        const row = data.data

        setFoundFields(data.found_fields || [])
        setMissingFields(data.missing_fields || [])

        if (row["Invoice Number"]) {
          setInvoiceNumber(String(row["Invoice Number"]))
        }

        if (row["Invoice Date"]) {
          try {
            setInvoiceDate(new Date(row["Invoice Date"]).toISOString().split("T")[0])
          } catch {}
        }

        if (row["Customer Name"]) {
          const match = customers.find(
            (customer) =>
              customer.customer_name.toLowerCase() ===
              String(row["Customer Name"]).toLowerCase()
          )

          if (match) {
            setCustomerId(match.id)
          } else {
            toast.error(`Customer '${row["Customer Name"]}' not found in database. Please select manually.`)
          }
        }

        if (row["Quantity Units"] != null) {
          setUnits(String(row["Quantity Units"]))
        }
        if (row["Per Unit Rate"] != null) {
          setRate(String(row["Per Unit Rate"]))
        }
        if (row["Open Access Charges"] != null) {
          setOpenAccessCharges(String(row["Open Access Charges"]))
        }
        if (row["Round Off"] != null) {
          setRoundOff(String(row["Round Off"]))
        }
        if (row["Description"]) {
          setDescription(String(row["Description"]))
        }

        setImportMode("manual")
      } else {
        toast.error(data.detail || "Failed to parse Excel file")
      }
    } catch {
      toast.error("Network error while uploading file")
    } finally {
      setLoading(false)

      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!invoiceNumber || !customerId || !invoiceDate) {
      toast.error("Please fill in all required fields")
      return
    }

    const formattedMonthOfSupply = normalizeMonthOfSupply(monthOfSupply, invoiceDate)

    if (monthOfSupply && !formattedMonthOfSupply) {
      toast.error("Month of Supply must be a valid month, like 2026-06 or June 2026")
      return
    }

    setLoading(true)

    try {
      const headers = await getAuthHeaders()
      const body = {
        invoice_number: invoiceNumber,
        customer_id: customerId,
        invoice_date: invoiceDate,
        month_of_supply: formattedMonthOfSupply,
        payment_mode: paymentMode || null,
        description: description || null,
        units: units ? parseFloat(units) : null,
        rate: rate ? parseFloat(rate) : null,
        gross_amount: amount || null,
        round_off: roundOffVal,
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
        let errorMessage = "Failed to create invoice. Please check the inputs."

        if (err.detail) {
          if (Array.isArray(err.detail)) {
            errorMessage = err.detail
              .map(
                (detail: { loc?: string[]; msg?: string }) =>
                  `${detail.loc?.join(".")} - ${detail.msg}`
              )
              .join(", ")
          } else if (typeof err.detail === "string") {
            errorMessage = err.detail
          }
        }

        toast.error(errorMessage)
      }
    } catch {
      toast.error("Network error")
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (n: number) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(n)

  return (
    <RoleGuard allowedRoles={["admin", "accountant", "employee"]}>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild>
              <Link href="/invoices/register"><ArrowLeft className="h-4 w-4" /></Link>
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
                Invoice Generator
              </h1>
              <p className="text-muted-foreground mt-1">
                Create a new invoice manually or import from Excel.
              </p>
            </div>
          </div>
          <div className="flex bg-muted p-1 rounded-lg">
            <Button 
              variant={importMode === "manual" ? "secondary" : "ghost"} 
              className="rounded-md"
              onClick={() => setImportMode("manual")}
            >
              Create Manually
            </Button>
            <Button 
              variant={importMode === "excel" ? "secondary" : "ghost"} 
              className="rounded-md"
              onClick={() => setImportMode("excel")}
            >
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              Import From Excel
            </Button>
          </div>
        </div>

        {importMode === "excel" && (
          <Card className="border-dashed border-2 bg-muted/20">
            <CardContent className="flex flex-col items-center justify-center p-12 text-center space-y-4">
              <div className="p-4 bg-primary/10 rounded-full text-primary">
                <UploadCloud className="w-8 h-8" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">Upload Excel Spreadsheet</h3>
                <p className="text-muted-foreground max-w-sm mt-1">
                  Upload a .xlsx file containing columns: Customer Name, Quantity Units, Per Unit Rate, Description, Round Off, Open Access Charges.
                </p>
              </div>
              <div className="pt-4">
                <input 
                  type="file" 
                  id="excel-upload" 
                  className="hidden" 
                  accept=".xlsx" 
                  ref={fileInputRef}
                  onChange={handleFileUpload} 
                />
                <Button onClick={() => fileInputRef.current?.click()} disabled={loading}>
                  {loading ? "Parsing..." : "Select .xlsx File"}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {foundFields.length > 0 && importMode === "manual" && (
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="border-emerald-200 bg-emerald-50/50 dark:bg-emerald-950/20 dark:border-emerald-900">
              <CardHeader className="py-3">
                <CardTitle className="text-sm text-emerald-800 dark:text-emerald-300">Successfully Detected</CardTitle>
              </CardHeader>
              <CardContent className="py-2 pt-0 text-sm text-emerald-700 dark:text-emerald-400">
                <ul className="list-disc pl-4 space-y-1">
                  {foundFields.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
            {missingFields.length > 0 && (
              <Card className="border-amber-200 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-900">
                <CardHeader className="py-3">
                  <CardTitle className="text-sm text-amber-800 dark:text-amber-300">Missing Fields (Fill Manually)</CardTitle>
                </CardHeader>
                <CardContent className="py-2 pt-0 text-sm text-amber-700 dark:text-amber-400">
                  <ul className="list-disc pl-4 space-y-1">
                    {missingFields.map((f) => (
                      <li key={f}>{f}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        <div className={importMode === "excel" ? "opacity-50 pointer-events-none" : ""}>
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
                        <Input
                          id="month_of_supply"
                          type="text"
                          value={monthOfSupply}
                          onChange={(e) => setMonthOfSupply(e.target.value)}
                          placeholder="June 2026 or 2026-06"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="payment_mode">Payment Mode</Label>
                        <Select value={paymentMode} onValueChange={setPaymentMode}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select mode" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="cheque">CHEQUE/RTGS</SelectItem>
                            <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
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
                    <CardTitle>Line Items & Billing</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="description">Item Description</Label>
                      <Input id="description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Solar Power Allotted 01.05.2026 to 31.05.2026" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="units">Quantity (Units)</Label>
                        <Input id="units" type="number" step="0.001" min="0" value={units} onChange={(e) => setUnits(e.target.value)} placeholder="0.000" />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="rate">Per Unit Rate (₹)</Label>
                        <Input id="rate" type="number" step="0.0001" min="0" value={rate} onChange={(e) => setRate(e.target.value)} placeholder="0.0000" />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="round_off">Round Off / On (₹)</Label>
                        <Input id="round_off" type="number" step="0.01" value={roundOff} onChange={(e) => setRoundOff(e.target.value)} placeholder="0.00" />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="open_access">Open Access Charges (₹)</Label>
                        <Input id="open_access" type="number" step="0.01" min="0" value={openAccessCharges} onChange={(e) => setOpenAccessCharges(e.target.value)} placeholder="0.00" />
                      </div>
                    </div>
                    <div className="space-y-2 pt-2">
                      <Label htmlFor="notes">Internal Notes</Label>
                      <Textarea id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional notes... (Not printed on PDF)" rows={2} />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Right: Live Preview */}
              <div className="space-y-6">
                <Card className="sticky top-20 bg-muted/20">
                  <CardHeader>
                    <CardTitle>Amount Preview</CardTitle>
                    <CardDescription>Live calculation</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Amount (Units × Rate)</span>
                      <span className="font-medium text-emerald-600">{formatCurrency(amount)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Round / Off</span>
                      <span className="font-medium">{(roundOffVal > 0 ? "+" : "") + formatCurrency(roundOffVal)}</span>
                    </div>
                    <div className="flex justify-between text-sm pt-2 border-t">
                      <span className="font-medium">Total</span>
                      <span className="font-bold">{formatCurrency(total)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Open Access Charges</span>
                      <span className="text-destructive font-medium">- {formatCurrency(oac)}</span>
                    </div>
                    <Separator className="my-2" />
                    <div className="flex justify-between text-lg font-bold items-center text-primary">
                      <span>Net Amount</span>
                      <span>{formatCurrency(netAmount)}</span>
                    </div>
                  </CardContent>
                </Card>

                <div className="flex flex-col gap-3">
                  <Button type="submit" className="w-full" disabled={loading}>
                    <Save className="h-4 w-4 mr-2" />
                    {loading ? "Saving & Generating PDF..." : "Save Invoice"}
                  </Button>
                </div>
              </div>
            </div>
          </form>
        </div>
      </div>
    </RoleGuard>
  )
}
