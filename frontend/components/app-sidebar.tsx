"use client"

import {
  LayoutDashboard,
  FileText,
  FilePlus,
  ClipboardList,
  BarChart3,
  Calculator,
  
  Activity,
  Users,
  Settings,
  LogOut,
  Zap,
  Trash2,
} from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"
import { signout } from "@/app/actions/auth"

import { useAuth } from "@/components/providers/auth-provider"

const navMain = [
  {
    label: "Overview",
    items: [
      { title: "Dashboard", url: "/", icon: LayoutDashboard },
    ],
  },
  {
    label: "Documents",
    items: [
      { title: "All Documents", url: "/documents", icon: FileText },
      { title: "Trash Bin", url: "/trash", icon: Trash2 },
    ],
  },
  {
    label: "Finance",
    items: [
      { title: "Invoice Generator", url: "/invoices/generator", icon: FilePlus },
      { title: "Invoice Register", url: "/invoices/register", icon: ClipboardList },
      { title: "Revenue Dashboard", url: "/revenue", icon: BarChart3 },
      { title: "Monthly Calculator", url: "/calculator", icon: Calculator },
      { title: "Loans", url: "/loans", icon: ClipboardList },
    ],
  },
  {
    label: "Manage",
    items: [
      { title: "Customers", url: "/customers", icon: Users },
      { title: "Users", url: "/users", icon: Users },
      { title: "Activity Logs", url: "/activity", icon: Activity },
      { title: "Settings", url: "/settings", icon: Settings },
    ],
  },
]

export function AppSidebar() {
  const pathname = usePathname()
  const { roleName, isLoading } = useAuth()

  if (isLoading) return null

  const filteredNavMain = navMain.map(group => {
    return {
      ...group,
      items: group.items.filter(item => {
        // Admin only
        if (item.title === "Users" || item.title === "Activity Logs" || item.title === "Customers") {
          return roleName === "admin"
        }
        // Admin, Employee
        if (item.title === "Invoice Generator" || item.title === "Loans" || item.title === "Monthly Calculator" || item.title === "Trash Bin") {
            return roleName === "admin" || roleName === "employee"
        }
        // Admin, Employee (Legacy group if needed)
        if (item.title === "Revenue Dashboard") {
          return roleName === "admin" || roleName === "employee"
        }
        // Dashboard, Documents, Invoice Register, Settings visible to all
        return true
      })
    }
  }).filter(group => group.items.length > 0)

  return (
    <Sidebar collapsible="icon" className="border-r-0">
      <SidebarHeader className="border-b border-sidebar-border">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link href="/">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <Zap className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold font-[family-name:var(--font-heading)]">SNS ERP</span>
                  <span className="text-xs text-muted-foreground">Sri Naga Sai Energy</span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        {filteredNavMain.map((group) => (
          <SidebarGroup key={group.label}>
            <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={pathname === item.url}
                      tooltip={item.title}
                    >
                      <Link href={item.url}>
                        <item.icon className="size-4" />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarFooter className="border-t border-sidebar-border">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              tooltip="Sign Out"
              onClick={() => signout()}
              className="text-muted-foreground hover:text-destructive"
            >
              <LogOut className="size-4" />
              <span>Sign Out</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
