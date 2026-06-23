"use client"

import {
  LayoutDashboard,
  FileText,
  FilePlus,
  ClipboardList,
  BarChart3,
  Calculator,
  Bot,
  Activity,
  Users,
  Settings,
  LogOut,
  Zap,
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
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { signout } from "@/app/actions/auth"

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
    ],
  },
  {
    label: "Finance",
    items: [
      { title: "Invoice Generator", url: "/invoices/generator", icon: FilePlus },
      { title: "Invoice Register", url: "/invoices/register", icon: ClipboardList },
      { title: "Revenue Dashboard", url: "/revenue", icon: BarChart3 },
      { title: "Monthly Calculator", url: "/calculator", icon: Calculator },
    ],
  },
  {
    label: "Manage",
    items: [
      { title: "Customers", url: "/customers", icon: Users },
      { title: "Activity Logs", url: "/activity", icon: Activity },
      { title: "Settings", url: "/settings", icon: Settings },
    ],
  },
]

export function AppSidebar() {
  const pathname = usePathname()

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
        {navMain.map((group) => (
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
