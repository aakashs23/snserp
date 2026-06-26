"use client"

import { useState, useEffect } from "react"
import { Calculator as CalculatorIcon, ArrowRight, Loader2, CheckCircle2 } from "lucide-react"
import { createClient } from "@/utils/supabase/client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"

interface CalculatorResponse {
  withdrawal_loss_units: number
  injection_loss_units: number
  total_line_loss_units: number
  sellable_units: number
  gross_revenue: number
  generation_tax: number
  agent_commission: number
  applied_round_off: number
  final_net_income: number
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
import { RoleGuard } from "@/components/role-guard"

export default function CalculatorPage() {
// ...
  return (
    <RoleGuard allowedRoles={["admin", "accountant"]}>
      <div className="space-y-6 max-w-6xl mx-auto">
        <div>
          <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
            Financial Worksheet Calculator
          </h1>
          <p className="text-muted-foreground mt-1">
            Standard operational workflow calculator for Sri Naga Sai Energy.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-12">
          {/* Left Column: Inputs */}
          <Card className="lg:col-span-5 flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CalculatorIcon className="size-5 text-primary" />
                Worksheet Parameters
              </CardTitle>
              <CardDescription>Enter values to instantly see calculations.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 flex-1">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="month">Month</Label>
                  <Input 
                    id="month" 
                    placeholder="e.g. June 2026" 
                    value={month} 
                    onChange={(e) => setMonth(e.target.value)} 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="customer">Customer</Label>
                  <Input 
                    id="customer" 
                    placeholder="e.g. Alpha Industries" 
                    value={customer} 
                    onChange={(e) => setCustomer(e.target.value)} 
                  />
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="units">Number of Units Generated</Label>
                  <Input 
                    id="units" 
                    type="number" 
                    step="0.01" 
                    min="0"
                    value={unitsGenerated} 
                    onChange={(e) => setUnitsGenerated(e.target.value)} 
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="wLoss">Withdrawal Loss (%)</Label>
                    <Input 
                      id="wLoss" 
                      type="number" 
                      step="0.01" 
                      min="0" max="100"
                      value={withdrawalLossPct} 
                      onChange={(e) => setWithdrawalLossPct(e.target.value)} 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="iLoss">Injection Loss (%)</Label>
                    <Input 
                      id="iLoss" 
                      type="number" 
                      step="0.01" 
                      min="0" max="100"
                      value={injectionLossPct} 
                      onChange={(e) => setInjectionLossPct(e.target.value)} 
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="rate">Per Unit Rate (₹)</Label>
                    <Input 
                      id="rate" 
                      type="number" 
                      step="0.01" 
                      min="0"
                      value={perUnitRate} 
                      onChange={(e) => setPerUnitRate(e.target.value)} 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="oac">Open Access Charges</Label>
                    <Input 
                      id="oac" 
                      type="number" 
                      step="0.01" 
                      min="0"
                      value={openAccessCharges} 
                      onChange={(e) => setOpenAccessCharges(e.target.value)} 
                    />
                  </div>
                </div>

                <div className="space-y-2 pt-2">
                  <Label htmlFor="roundOff" className="text-muted-foreground flex items-center justify-between">
                    <span>Manual Round Off / On (Optional)</span>
                    <span className="text-xs font-normal">Overrides auto-rounding</span>
                  </Label>
                  <Input 
                    id="roundOff" 
                    type="number" 
                    step="0.01" 
                    placeholder="e.g. -0.47"
                    value={manualRoundOff} 
                    onChange={(e) => setManualRoundOff(e.target.value)} 
                  />
                </div>
              </div>
              
              {error && (
                <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md border border-destructive/20 mt-4">
                  {error}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Right Column: Calculations */}
          <Card className="lg:col-span-7 bg-muted/20 border-primary/10 shadow-inner flex flex-col relative overflow-hidden">
            {/* Subtle loading indicator at the top edge */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-muted overflow-hidden">
              {loading && <div className="h-full bg-primary animate-pulse w-full"></div>}
            </div>
            
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Calculation Output
                {loading && <Loader2 className="size-4 animate-spin text-muted-foreground" />}
                {!loading && result && !error && <CheckCircle2 className="size-4 text-emerald-500" />}
              </CardTitle>
              <CardDescription>Live breakdown of the billing amounts.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 flex-1">
              {!result ? (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground opacity-50 space-y-4">
                  <ArrowRight className="size-10" />
                  <p>Fill out the parameters to see results</p>
                </div>
              ) : (
                <div className="space-y-8 animate-in fade-in duration-300">
                  {/* Unit Calculations */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Units Breakdown</h4>
                    
                    <div className="grid grid-cols-[1fr_auto] gap-2 text-sm items-center">
                      <span className="text-muted-foreground">Total Units Generated</span>
                      <span className="font-medium">{formatUnits(parseFloat(unitsGenerated) || 0)}</span>
                      
                      <span className="text-muted-foreground pl-4 border-l-2 border-border/50">− Withdrawal Loss Units</span>
                      <span className="text-destructive font-medium">{formatUnits(result.withdrawal_loss_units)}</span>
                      
                      <span className="text-muted-foreground pl-4 border-l-2 border-border/50">− Injection Loss Units</span>
                      <span className="text-destructive font-medium">{formatUnits(result.injection_loss_units)}</span>
                      
                      <span className="text-muted-foreground pl-4 border-l-2 border-border/50">= Total Line Loss Units</span>
                      <span className="text-destructive font-medium">{formatUnits(result.total_line_loss_units)}</span>
                    </div>

                    <div className="flex justify-between items-center py-2 px-3 bg-secondary/50 rounded-md mt-2">
                      <span className="font-medium">Sellable Units</span>
                      <span className="font-bold text-lg">{formatUnits(result.sellable_units)}</span>
                    </div>
                  </div>

                  <Separator />

                  {/* Financial Calculations */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Financial Breakdown</h4>
                    
                    <div className="grid grid-cols-[1fr_auto] gap-2 text-sm items-center">
                      <span className="text-muted-foreground font-medium">Gross Revenue (Sellable × Rate)</span>
                      <span className="font-medium text-emerald-600">{formatCurrency(result.gross_revenue)}</span>
                      
                      <span className="text-muted-foreground">− Open Access Charges</span>
                      <span className="text-destructive font-medium">{formatCurrency(parseFloat(openAccessCharges) || 0)}</span>
                      
                      <span className="text-muted-foreground">− Generation Tax (₹0.63/Unit)</span>
                      <span className="text-destructive font-medium">{formatCurrency(result.generation_tax)}</span>
                      
                      <span className="text-muted-foreground">− Agent Commission (₹0.10/Unit)</span>
                      <span className="text-amber-600 font-medium">{formatCurrency(result.agent_commission)}</span>
                      
                      <span className="text-muted-foreground">Round Off Applied</span>
                      <span className="font-medium">{formatCurrency(result.applied_round_off)}</span>
                    </div>
                  </div>

                  {/* Final Result */}
                  <div className="mt-8 pt-6 border-t border-primary/20">
                    <div className="bg-primary/5 border border-primary/10 p-5 rounded-xl flex justify-between items-center shadow-sm">
                      <div className="space-y-1">
                        <span className="font-semibold text-lg">Net Income</span>
                        <p className="text-xs text-muted-foreground">Final payable amount rounded to nearest integer</p>
                      </div>
                      <span className="text-3xl font-bold text-primary tracking-tight">
                        {formatCurrency(result.final_net_income)}
                      </span>
                    </div>
                  </div>

                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </RoleGuard>
  )
}
