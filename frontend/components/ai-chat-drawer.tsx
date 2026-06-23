"use client"

import { useEffect, useRef } from "react"
import { X, Send, Bot, User as UserIcon, FileText, Loader2, Sparkles } from "lucide-react"
import { useChat } from "@/components/providers/chat-provider"
import { createClient } from "@/utils/supabase/client"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function AIChatDrawer() {
  const { isOpen, closeChat, messages, isLoading, sendMessage } = useChat()
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll logic similar to ChatGPT
  useEffect(() => {
    if (scrollRef.current && isOpen) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages, isOpen, isLoading])

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen])

  const handlePreview = async (document_id: string) => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      
      const res = await fetch(`${API_URL}/api/v1/documents/${document_id}/preview`, {
        headers: { "Authorization": `Bearer ${session?.access_token}` }
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      const value = e.currentTarget.value
      if (value.trim() && !isLoading) {
        sendMessage(value)
        e.currentTarget.value = ""
      }
    }
  }

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-background/20 backdrop-blur-sm transition-all duration-300"
          onClick={closeChat}
        />
      )}

      {/* Drawer */}
      <div 
        className={`fixed top-0 right-0 z-50 h-screen w-full max-w-md bg-background border-l shadow-2xl flex flex-col transform transition-transform duration-300 ease-in-out ${isOpen ? "translate-x-0" : "translate-x-full"}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2 text-primary">
            <Sparkles className="size-5" />
            <h2 className="font-semibold text-lg tracking-tight font-[family-name:var(--font-heading)]">AI Assistant</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={closeChat}>
            <X className="size-5" />
          </Button>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 bg-muted/20 min-h-0">
          <div className="space-y-6 pb-4">
            {messages.length === 0 && (
              <div className="text-center py-10 flex flex-col items-center justify-center opacity-50">
                <Bot className="size-12 mb-4" />
                <p className="text-sm font-medium">Hello! How can I help you today?</p>
                <p className="text-xs mt-2 max-w-[250px]">Ask me questions about your uploaded documents, invoices, or business analytics.</p>
              </div>
            )}
            
            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'ai' && (
                  <div className="flex-shrink-0 size-8 rounded-full bg-chart-4 flex items-center justify-center text-white mt-1">
                    <Bot className="size-4.5" />
                  </div>
                )}
                
                <div className={`flex flex-col gap-1.5 max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`p-3.5 rounded-2xl ${msg.role === 'user' ? 'bg-primary text-primary-foreground rounded-tr-sm' : 'bg-card border shadow-sm rounded-tl-sm'}`}>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                  </div>
                  
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="flex flex-col gap-1.5 mt-1 w-full">
                      <div className="flex flex-wrap gap-1.5">
                        {msg.citations.map((cite, i) => (
                          <button
                            key={i}
                            onClick={() => handlePreview(cite.document_id)}
                            className="flex items-center gap-1 text-[11px] font-medium bg-muted border rounded-md px-2 py-1 hover:bg-accent hover:text-white transition-colors"
                            title={cite.snippet}
                          >
                            <FileText className="size-3" />
                            <span className="truncate max-w-[120px]">{cite.file_name}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="flex-shrink-0 size-8 rounded-full bg-accent flex items-center justify-center text-white mt-1">
                    <UserIcon className="size-4.5" />
                  </div>
                )}
              </div>
            ))}
            
            {/* Thinking State */}
            {isLoading && (
              <div className="flex gap-3 justify-start">
                <div className="flex-shrink-0 size-8 rounded-full bg-chart-4 flex items-center justify-center text-white mt-1">
                  <Bot className="size-4.5" />
                </div>
                <div className="p-3.5 rounded-2xl bg-card border shadow-sm rounded-tl-sm flex items-center gap-2">
                  <Loader2 className="size-4 animate-spin text-muted-foreground" />
                  <span className="text-sm text-muted-foreground font-medium">Thinking...</span>
                </div>
              </div>
            )}
            <div ref={scrollRef} className="h-1" />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-4 border-t bg-background">
          <div className="relative flex items-center">
            <Input
              ref={inputRef}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything..."
              className="pr-12 py-6 rounded-full bg-muted/50 focus-visible:ring-1 focus-visible:ring-offset-0 border-muted"
              disabled={isLoading}
            />
            <Button 
              size="icon" 
              className="absolute right-1.5 h-9 w-9 rounded-full transition-transform active:scale-95" 
              onClick={() => {
                const val = inputRef.current?.value
                if (val && val.trim() && !isLoading) {
                  sendMessage(val)
                  if (inputRef.current) inputRef.current.value = ""
                }
              }}
              disabled={isLoading}
            >
              <Send className="size-4 ml-0.5" />
            </Button>
          </div>
          <p className="text-[10px] text-center text-muted-foreground mt-2">
            AI can make mistakes. Check important info.
          </p>
        </div>
      </div>
    </>
  )
}
