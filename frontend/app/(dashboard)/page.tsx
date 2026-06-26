"use client"

import {
  BarChart3,
  FileText,
  IndianRupee,
  TrendingUp,
  FilePlus,
  Upload,
  Bot,
  Users,
} from "lucide-react"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/components/providers/auth-provider"

const stats = [
  {
    title: "Monthly Revenue",
    value: "₹0",
    description: "Current month",
    icon: IndianRupee,
    trend: null,
  },
  {
    title: "Total Invoices",
    value: "0",
    description: "All time",
    icon: FileText,
    trend: null,
  },
  {
    title: "Documents",
    value: "0",
    description: "Uploaded files",
    icon: Upload,
    trend: null,
  },
  {
    title: "Customers",
    value: "0",
    description: "Active customers",
    icon: Users,
    trend: null,
  },
]

const quickActions = [
  { title: "Upload Document", icon: Upload, href: "/documents", color: "bg-accent" },
  { title: "Create Invoice", icon: FilePlus, href: "/invoices/generator", color: "bg-primary" },
  { title: "AI Assistant", icon: Bot, href: "/ai", color: "bg-chart-4" },
  { title: "Revenue Dashboard", icon: BarChart3, href: "/revenue", color: "bg-chart-1" },
]

export default function DashboardPage() {
  const { roleName } = useAuth()

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
          Dashboard
        </h1>
        <p className="text-muted-foreground mt-1">
          Welcome to Sri Naga Sai ERP. Here&apos;s an overview of your business.
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title} className="relative overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions - Hidden for viewers */}
      {roleName !== "viewer" && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {quickActions.map((action) => (
              <Button
                key={action.title}
                variant="outline"
                className="h-auto flex-col gap-3 p-6 hover:shadow-md transition-all duration-200"
                asChild
              >
                <Link href={action.href}>
                  <div className={`rounded-lg p-2.5 ${action.color} text-white`}>
                    <action.icon className="h-5 w-5" />
                  </div>
                  <span className="font-semibold">{action.title}</span>
                </Link>
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Your latest actions and system events.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <TrendingUp className="h-12 w-12 mb-4 opacity-30" />
            <p className="text-sm">No recent activity yet.</p>
            <p className="text-xs mt-1">Actions will appear here as you use the system.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
